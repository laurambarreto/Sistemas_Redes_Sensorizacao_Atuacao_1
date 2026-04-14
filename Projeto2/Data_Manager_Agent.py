import paho.mqtt.client as mqtt
import time
import threading
import json
import socket
from datetime import datetime
from influxdb_client_3 import InfluxDBClient3, Point

GROUP_ID = "30"
MACHINE_ID = "A23X"
UDP_host, UDP_port = "127.0.0.1", 5002
ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#------------- Guardar no InfluxDB ------------------
token = "bSEhhbnFIZKDTfeSpV1mfdeeY7dtuy6NOG9aOwDVwDM_KTRRR89j4XDj7L4C4eYJVmJN00FWTjk2wbMGoFKytA==" 			# CHANGE TO YOUR INFLUXDB CLOUD TOKEN
org = "SRSA_PL"		# CHANGE TO YOUR INFLUXDB CLOUD ORGANIZATION
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
database = "SRSA"		# CHANGE TO YOUR INFLUXDB CLOUD BUCKET
write_client = InfluxDBClient3(host=host, token=token, database=database, org=org)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

    # From Machine
    client.subscribe(f"v3/{GROUP_ID}@ttn/devices/{MACHINE_ID}/up")
    # From Machine_Data_Manager
    client.subscribe(f"{GROUP_ID}/{MACHINE_ID}/Machine_Data_Manager")

def processar_unidades(sensor_data, MACHINE_ID):
    if (MACHINE_ID in ["A23X", "C89Z", "E34V", "G92Q"]):
        # Processar os dados para a unidade correta
        sensor_data["oil_pressure"] = sensor_data["oil_pressure"] //14.5038
    if (MACHINE_ID in ["E34V", "F78T", "G92Q", "H65P"]):
        sensor_data["coolant_temperature"] = (sensor_data["coolant_temperature"] - 32) * 5/9
    if (MACHINE_ID == "H65P"):
        sensor_data["battery_potencial"] = sensor_data["rpm"] // 1000
    if (MACHINE_ID in ["A23X", "D56W", "F78T", "G92Q"]):
        sensor_data["consumption"] = sensor_data["consumption"] * 0.264172

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    global active, last_message_time, sensor_data, sensor_timeout
    topic = msg.topic
    payload = msg.payload.decode()
    data = json.loads(payload)
    try:
        if "up" in topic:
            # Processamento dos dados dos sensores
            sensor_data["rpm"] = float(data["decoded_payload"]["rpm"])
            sensor_data["coolant_temp"] = float(data["decoded_payload"]["coolant_temperature"])
            sensor_data["oil_pressure"] = float(data["decoded_payload"]["oil_pressure"])
            sensor_data["battery_potential"] = float(data["decoded_payload"]["battery_potencial"])
            sensor_data["consumption"] = float(data["decoded_payload"]["consumption"])
            MACHINE_ID = data["decoded_payload"] ["machine_id"]

            # preprocessar as unidades da maquina (tudo para rpm, bar, ºC, V, L/h)
            processar_unidades(sensor_data, MACHINE_ID)
            
            sensors = {
                "GroupID": GROUP_ID,
                "machine_id": MACHINE_ID,
                "rpm": sensor_data["rpm"],
                "coolant_temperature": sensor_data["coolant_temp"],
                "oil_pressure": sensor_data["oil_pressure"],
                "battery_potential": sensor_data["battery_potential"],
                "consumption": sensor_data["consumption"]
            }
            
            client.publish(f"{GROUP_ID}/{MACHINE_ID}/Data_Manager_Agent", sensors)

            # Aqui escreve-se os dados recebidos no influxDB
            p = Point("Projeto") \
            .tag("machine_id", MACHINE_ID) \
            .field("rpm", sensor_data["rpm"]) \
            .field("coolant_temperature", sensor_data["coolant_temp"]) \
            .field("oil_pressure", sensor_data["oil_pressure"]) \
            .field("battery_potential", sensor_data["battery_potential"]) \
            .field("consumption", sensor_data["consumption"]) 
            
            write_client.write(p) #tem q ter sensores, controll messages, alert messages and signal information 

        elif "Machine_Data_Manager" in topic:
            # Aqui processa-se os dados recebidos do Machine_Data_Manager

            payload = {
                "downlinks":[
                {
                    "frm_payload": " 0x01 0x01 0x01 0xFA ",
                    "f_port": 1,
                    "priority": "NORMAL",
                }
                ]
            }
            payload = json.loads(payload)
            client.publish(f"v3/{GROUP_ID}@ttn/devices/{MACHINE_ID}/down/push_actuador", payload)

    except Exception as e:
        print(f"[ERRO] {e}")

def escutar_udp():
    print(f"[UDP] A escutar alertas em {host}:{port} ...")
    ServerSocket.bind((UDP_host, UDP_port))
    while True:
        try:
            data, addr = ServerSocket.recvfrom(1024)
            mensagem = json.loads(data.decode())
            print(f"[UDP] Alerta recebido de {addr}: {mensagem}")
            
            estado = mensagem["level"]

            if estado == "CRITICAL":
                payload = {
                    "downlinks":[
                    {
                        "frm_payload": " 0x02 0x01 0x01 ",
                        "f_port": 1,
                        "priority": "NORMAL",
                    }
                    ]
                }

            else :
                payload = {
                "downlinks":[
                {
                    "frm_payload": " 0x02 0x02 0x01 ",
                    "f_port": 1,
                    "priority": "NORMAL",
                }
                ]
            }
            payload = json.loads(payload)
            client.publish(f"v3/{GROUP_ID}@ttn/devices/{MACHINE_ID}/down/alert", payload)

        except Exception as e:
            print(f"[UDP ERRO] {e}")

broker = "broker.hivemq.com" #"test.mosquitto.org"
port = 1883
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
#client.username_pw_set("srsa_sub", "srsa_password")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)

# Iniciar thread da escuta UDP
udp_thread = threading.Thread(target=escutar_udp, daemon=True)
udp_thread.start()

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    print("\n[ALARME] Encerrado.")