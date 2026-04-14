import paho.mqtt.client as mqtt
import time
import random
import sys
import json
from datetime import datetime

def conv_bar_psi (value):
    return value*14.5038

def conv_cent_F (value):
    return value*1.8 + 32

def conv_V_mV (value):
    return value*1000

def conv_gal_l (value):
    return value*0.264172

# Valores iniciais (dentro dos intervalos saudáveis)
sensor_data = {
    "rpm": 1100,                 # 800-3000 RPM
    "coolant_temperature": 90.0, # 70-130°C (ou °F para algumas máquinas)
    "oil_pressure": 3.0,         # 1.5-8.0 bar/psi
    "battery_potential": 12.6,   # 10-14V (ou mV para H65P)
    "consumption": 15.0,         # 1-50 l/h ou gal/h

    "rssi" : -90,                # -120 dBm to -50 dBm
    "snr" : -5,                  # -20 dB to 10 dB
    "chanel_rssi" : -90          # -120 dBm to -50 dBm
}

# Unidades por tipo de máquina (Tabela 1)
MACHINE_UNITS = {
    "A23X": {"pressure_unit": "psi", "temp_unit": "°C", "consumption_unit": "l/h"},
    "B47Y": {"pressure_unit": "bar", "temp_unit": "°C", "consumption_unit": "gal/h"},
    "C89Z": {"pressure_unit": "psi", "temp_unit": "°C", "consumption_unit": "gal/h"},
    "D56W": {"pressure_unit": "bar", "temp_unit": "°C", "consumption_unit": "l/h"},
    "E34V": {"pressure_unit": "psi", "temp_unit": "°F", "consumption_unit": "gal/h"},
    "F78T": {"pressure_unit": "bar", "temp_unit": "°F", "consumption_unit": "l/h"},
    "G92Q": {"pressure_unit": "psi", "temp_unit": "°F", "consumption_unit": "l/h"},
    "H65P": {"pressure_unit": "bar", "temp_unit": "°F", "consumption_unit": "gal/h", "battery_unit": "mV"}
}



try:
    # Atribui os argumentos a variáveis
    GROUP_ID = sys.argv[1]          # Primeiro argumento (GroupID)
    UPDATE_TIME = int(sys.argv[2])  # Segundo argumento (convertido para inteiro)
    MACHINE_CODE = sys.argv[3]      # Terceiro argumento (Código da máquina, ex: A23X)
except ValueError:
    print("Erro. Verifique os argumentos passados.")
    print("Uso: python3 machine.py <GroupID> <MACHINE_UPDATE_TIME> <Machine_Code>")
    sys.exit(1)

broker = "broker.hivemq.com" #para testes em casa, 10.6.1.9 na defesa
port = 1883

modo_normal = True
modo_controlo = False
modo_alerta = False


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

    #Daqui vêm mensagens para reduzir gradualmente RPM e valores fora dos limites
    client.subscribe(f"v3/{GROUP_ID}@ttn/devices/{MACHINE_CODE}/down/push_actuador")
    #Daqui vêm mensagens para parar a máquina porque já não está saudável
    client.subscribe(f"v3/{GROUP_ID}@ttn/devices/{MACHINE_CODE}/down/push_alert") 
    
def update_JSON_values():
    global sensor_data, received_at
    # Atualiza os valores do JSON com variações incrementais, respeitando os limites.
    
    # Na mesma unidade para todas as máquinas
    sensor_data["rpm"] += random.uniform(100, 200)
    sensor_data["rpm"] = max(800, min(3000, sensor_data["rpm"]))

    if MACHINE_CODE in ["B47Y", "D56W", "F78T", "H65P"]: # oil pressure (bar)
        sensor_data["oil_pressure"] += random.uniform(0, 0.5)
        sensor_data["oil_pressure"] = max(1.5, min(8.0, sensor_data["oil_pressure"]))
    else: # oil pressure (psi)
        sensor_data["oil_pressure"] += random.uniform(conv_bar_psi(0), + conv_bar_psi(0.5))
        sensor_data["oil_pressure"] = max(conv_bar_psi(1.5), min(conv_bar_psi(8.0), sensor_data["oil_pressure"]))

    if MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]: # coolant temperature (°C)
        sensor_data["coolant_temperature"] += random.uniform(0, 1)
        sensor_data["coolant_temperature"] = max(70.0, min(130.0, sensor_data["coolant_temperature"]))
    else: # coolant temperature (°F)
        sensor_data["coolant_temperature"] += random.uniform(conv_cent_F(0), conv_cent_F(1.0))
        sensor_data["coolant_temperature"] = max(conv_cent_F(70.0), min(conv_cent_F(130.0), sensor_data["coolant_temperature"]))
    
    if MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]: # battery potential (V)
        sensor_data["battery_potential"] += random.uniform(0, 0.2)
        sensor_data["battery_potential"] = max(10.0, min(14.0, sensor_data["battery_potential"]))
    elif MACHINE_CODE == "H65P": # battery potential (mV)
        sensor_data["battery_potential"] += random.uniform(0, conv_V_mV(0.2))
        sensor_data["battery_potential"] = max(10000, min(14000, sensor_data["battery_potential"]))
    
    if MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]: # consumption (l/h)
        sensor_data["consumption"] += random.uniform(0, 1.0)
        sensor_data["consumption"] = max(1.0, min(50.0, sensor_data["consumption"]))
    else: # consumption (gal/h)
        sensor_data["consumption"] += random.uniform(0, + conv_gal_l(1.0))
        sensor_data["consumption"] = max(conv_gal_l(1.0), min(conv_gal_l(50.0), sensor_data["consumption"]))


    # Variações aleatórias dos parâmetros da comunicação LoRaWAN
    sensor_data["rssi"] += random.randint(-3, 3)
    sensor_data["snr"] += random.uniform(-0.5, 0.5)
    sensor_data["chanel_rssi"] += random.randint(-3, 3)

    # Impedir que os valores saiam dos limites definidos
    sensor_data["rssi"] = max(-120, min(-50, sensor_data["rssi"]))
    sensor_data["snr"] = max(-20, min(10, sensor_data["snr"]))
    sensor_data["chanel_rssi"] = max(-120, min(-50, sensor_data["chanel_rssi"]))

def create_payload():
    # Cria o payload JSON com os dados atualizados
    payload = { 
    "end_device_ids": { 
        "machine_id": "my-device", 
        "application_id": "my-application", 
        "dev_eui": "70B3D57ED00347C5", 
        "join_eui": "0000000000000000", 
        "dev_addr": "260B1234" 
    }, 
    "received_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), 
    "uplink_message": { 
        "f_port": 1, 
        "f_cnt": 1234, 
        "frm_payload": "BASE64_ENCODED_PAYLOAD", 
        "decoded_payload": { 
            "rpm": sensor_data["rpm"], 
            "coolant_temperature": sensor_data["coolant_temperature"], 
            "oil_pressure": sensor_data["oil_pressure"], 
            "battery_potential": sensor_data["battery_potential"], 
            "consumption": sensor_data["consumption"], 
            "machine_type": MACHINE_CODE, 
        }, 
        "rx_metadata": [ 
        { 
            "gateway_id": "gateway-1", 
            "rssi": sensor_data["rssi"], 
            "snr": sensor_data["snr"], 
            "channel_rssi": sensor_data["chanel_rssi"],
            "uplink_token": "TOKEN_VALUE" 
        } 
        ], 
        "settings": { 
            "data_rate": { 
                "modulation": "LORA", 
                "bandwidth": 125000, 
                "spreading_factor": 7 
            }, 
            "frequency": "868300000", 
            "timestamp": 1234567890 
        }, 
        "consumed_airtime": "0.061696s" 
    } 
} 
    return payload

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    global sensor_data, stop
    topic = msg.topic
    command = json.loads(msg.payload)
    payload_hex = command["downlinks"][0]["frm_payload"]
    payload_bytes = bytes.fromhex(payload_hex)

    msg_type = payload_bytes[0]
    action_type = payload_bytes[1]

    try:
        # Mensagem JSON recebida do Data_Manager_Agent para reduzir algum parâmetro fora dos limites
        if "push_actuador" in topic:
            modo_normal = False
            modo_controlo = True
            modo_alerta = False
            reduzir_valores(command, payload_bytes, msg_type, action_type) 
            modo_normal = True
            modo_controlo = False
            modo_alerta = False


        # Mensagem JSON recebida do Data_Manager_Agent para parar a máquina
        elif "push_alert" in topic:
            if action_type == 0x01: # Critical/shutdown
                stop_machine()

            else: # Danger
                danger()

    except Exception as e:
        print(f"[ERRO] {e}")

def stop_machine():
    global sensor_data, stop
    if (MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]): # coolant temperature (°C)
        while(sensor_data["rpm"] != 0 and sensor_data["oil_pressure"] != 0 and sensor_data["consumption"] != 0 and sensor_data["coolant_temperature"] >= 20):
            # Reduz os valores para 0
            sensor_data["rpm"] = max(0, sensor_data["rpm"] - 50)
            sensor_data["oil_pressure"] = max(0, sensor_data["oil_pressure"] - 0.1)
            sensor_data["coolant_temperature"] = max(0, sensor_data["coolant_temperature"] - 1)
            sensor_data["battery_potential"] = max(0, sensor_data["battery_potential"] - 0.1)
            sensor_data["consumption"] = max(0, sensor_data["consumption"] - 1)

            client.publish(topic=f"v3/{GROUP_ID}@ttn/devices/{MACHINE_CODE}/up",payload=json.dumps(payload))
            time.sleep(UPDATE_TIME)

    else: # coolant temperature (°F)
        while(sensor_data["rpm"] != 0 and sensor_data["oil_pressure"] != 0 and sensor_data["consumption"] != 0 and sensor_data["coolant_temperature"] >= 68):       
            # Reduz os valores para 0
            sensor_data["rpm"] = max(0, sensor_data["rpm"] - 50)
            sensor_data["oil_pressure"] = max(0, sensor_data["oil_pressure"] - 0.1)
            sensor_data["coolant_temperature"] = max(0, sensor_data["coolant_temperature"] - 1)
            sensor_data["battery_potential"] = max(0, sensor_data["battery_potential"] - 0.1)
            sensor_data["consumption"] = max(0, sensor_data["consumption"] - 1)

            client.publish(topic=f"v3/{GROUP_ID}@ttn/devices/{MACHINE_CODE}/up",payload=json.dumps(payload))
            time.sleep(UPDATE_TIME)

    stop = False # continuar a emissão de valores aleatorios na linha 178
    print("Máquina parada.")

def danger ():
    global sensor_data
    for i in range (5):
        # Na mesma unidade para todas as máquinas
        sensor_data["rpm"] -= 50
        sensor_data["rpm"] = max(800, min(3000, sensor_data["rpm"]))

        if MACHINE_CODE in ["B47Y", "D56W", "F78T", "H65P"]: # oil pressure (bar)
            sensor_data["oil_pressure"] -= 0.3
            sensor_data["oil_pressure"] = max(1.5, min(8.0, sensor_data["oil_pressure"]))
        else: # oil pressure (psi)
            sensor_data["oil_pressure"] -= conv_bar_psi(0.3)
            sensor_data["oil_pressure"] = max(conv_bar_psi(1.5), min(conv_bar_psi(8.0), sensor_data["oil_pressure"]))

        if MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]: # coolant temperature (°C)
            sensor_data["coolant_temperature"] -= 1
            sensor_data["coolant_temperature"] = max(70.0, min(130.0, sensor_data["coolant_temperature"]))
        else: # coolant temperature (°F)
            sensor_data["coolant_temperature"] -= conv_cent_F(1)
            sensor_data["coolant_temperature"] = max(conv_cent_F(70.0), min(conv_cent_F(130.0), sensor_data["coolant_temperature"]))
        
        if MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]: # battery potential (V)
            sensor_data["battery_potential"] -= 0.2
            sensor_data["battery_potential"] = max(10.0, min(14.0, sensor_data["battery_potential"]))
        elif MACHINE_CODE == "H65P": # battery potential (mV)
            sensor_data["battery_potential"] -= conv_V_mV(0.2)
            sensor_data["battery_potential"] = max(10000, min(14000, sensor_data["battery_potential"]))
        
        if MACHINE_CODE in ["A23X", "B47Y", "C89Z", "D56W"]: # consumption (l/h)
            sensor_data["consumption"] -= 1
            sensor_data["consumption"] = max(1.0, min(50.0, sensor_data["consumption"]))
        else: # consumption (gal/h)
            sensor_data["consumption"] -= conv_gal_l(1.0)
            sensor_data["consumption"] = max(conv_gal_l(1.0), min(conv_gal_l(50.0), sensor_data["consumption"]))

        time.sleep (UPDATE_TIME)


def reduzir_valores(payload_bytes, msg_type, action_type):
    global sensor_data
    try:

        param_id = payload_bytes[2]
        adjustment = int.from_bytes(payload_bytes[3:4], byteorder='big', signed=True)
        if msg_type != 0x01 or action_type != 0x01:
            print("Mensagem não é de controlo para modificação. Ignorada.")
            return

        param_map = {
            0x01: "rpm",
            0x02: "consumption",
            0x03: "coolant_temperature",
            0x04: "oil_pressure",
            0x05: "battery_potential"
        }

        if param_id in param_map:
            param_name = param_map[param_id]
            print(f"[ATUADOR] Reduzindo {param_name} em {adjustment}")

            # Ajusta o valor do parâmetro, respeitando os limites mínimos (não negativos)
            sensor_data[param_name] = max(0, sensor_data[param_name] + adjustment)

        else:
            print(f"[ERRO] Parâmetro desconhecido com ID: {param_id}")

    except Exception as e:
        print(f"[ERRO] ao reduzir valores: {e}")


client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("srsa", "srsa_password") #define o utilizador e password para aceder ao broker
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)

client.loop_start()  

try:
    while True:
        # publica os dados aleatorios se nao for para parar a máquina ou reduzir valores fora dos limites
        if (modo_normal == True):
            update_JSON_values()  # Atualiza os valores do JSON com variações incrementais
            payload = create_payload()  # Cria o payload JSON com os dados atualizados
            client.publish(topic=f"v3/{GROUP_ID}@ttn/devices/{MACHINE_CODE}/up",payload=json.dumps(payload))
            print("enviou valores")
            time.sleep(UPDATE_TIME)

except KeyboardInterrupt:
    print("\nExiting publisher")
    client.disconnect()