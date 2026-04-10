import paho.mqtt.client as mqtt
import time
import json

GroupID = "30"  
machine_id = "A23X"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

    # From Data_Manager_Agent 
    client.subscribe(f"{GroupID}/{machine_id}/Data_Manager_Agent")

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    global active, last_message_time, sensor_data, sensor_timeout
    topic = msg.topic
    payload = msg.payload.decode()
    data = payload.split(" ")
    try:
        if "Data_Manager_Agent" in topic:
            # Processamento dos dados recebidos do Data_Manager_Agent
            rpm = data[0]
            coolant_temp = data[1]
            oil_pressure = data[2]
            battery_potential = data[3]
            consumption = data[4]

            # verificar se estão dentro dos limites
            # se nao estiver, enviar mensagem de controlo para o topico {GroupID}/{machine_id}/Machine_Data_Manager
            with open('intervals.cfg', 'r') as ficheiro:
                # Ler todas as linhas
                rpm_interval = list(map(int, ficheiro.readline().split()))
                coolant_temp_interval = list(map(float, ficheiro.readline().split()))
                oil_pressure_interval = list(map(float, ficheiro.readline().split()))
                battery_potential_interval = list(map(float, ficheiro.readline().split()))
                consumption_interval = list(map(float, ficheiro.readline().split()))

                if rpm > rpm_interval[1]:
                    print(f"[ALARME] RPM fora do intervalo: {rpm}")
                    payload = {
                        "parameter": "rpm",
                        "adjustment": int(250) 
                    }
                    client.publish(f"{GroupID}/{machine_id}/Machine_Data_Manager", json.dumps(payload))

                if coolant_temp > coolant_temp_interval[1]:
                    print(f"[ALARME] Temperatura fora do intervalo: {coolant_temp}")
                    payload = {
                        "parameter": "coolant_temp",
                        "adjustment": int(2) 
                    }
                    client.publish(f"{GroupID}/{machine_id}/Machine_Data_Manager", json.dumps(payload))

                if oil_pressure > coolant_temp_interval[1]:
                    print(f"[ALARME] Pressão do óleo fora do intervalo: {oil_pressure}")
                    payload = {
                        "parameter": "oil_pressure",
                        "adjustment": int(1) 
                    }
                    client.publish(f"{GroupID}/{machine_id}/Machine_Data_Manager", json.dumps(payload))

                if battery_potential > battery_potential_interval[1]:
                    print(f"[ALARME] Potência da bateria fora do intervalo: {battery_potential}")
                    payload = {
                        "parameter": "battery_potential",
                        "adjustment": int(1) 
                    }
                    client.publish(f"{GroupID}/{machine_id}/Machine_Data_Manager", json.dumps(payload))

                if consumption > consumption_interval[1]:
                    print(f"[ALARME] Consumo fora do intervalo: {consumption}")
                    payload = {
                        "parameter": "consumption",
                        "adjustment": int(2) 
                    }
                    client.publish(f"{GroupID}/{machine_id}/Machine_Data_Manager", json.dumps(payload))
            
    except Exception as e:
        print(f"[ERRO] {e}")

broker = "broker.hivemq.com" #"test.mosquitto.org"
port = 1883
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
#client.username_pw_set("srsa_sub", "srsa_password")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)


try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    print("\n[ALARME] Encerrado.")