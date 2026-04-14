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

    # From Machine to Data_Manager_Agent
    client.subscribe(f"v3/{GroupID}@ttn/devices/{machine_id}/up")

    # From Data_Manager_Agent to Machine
    client.subscribe(f"v3/{GroupID}@ttn/devices/{machine_id}/down/push_actuator")
    client.subscribe(f"v3/{GroupID}@ttn/devices/{machine_id}/down/push_alert")

    # From Machine_Data_Manager to Data_Manager_Agent
    client.subscribe(f"{GroupID}/{machine_id}/Machine_Data_Manager")

    # From Data_Manager_Agent to Machine_Data_Manager
    client.subscribe(f"{GroupID}/{machine_id}/Data_Manager_Agent")

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        data = json.loads(payload)
        message_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{message_time} : {topic} : {data}" + "/n")

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
    print("\n[Debugger] Encerrado.")
