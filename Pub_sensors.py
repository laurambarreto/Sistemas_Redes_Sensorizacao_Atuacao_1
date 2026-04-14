# sensors.py
import paho.mqtt.client as mqtt
import time
import random

broker = "10.6.1.71" #para testes em casa, 10.6.1.9 na defesa, 
port = 1883
group_id = "30"  

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("srsa", "srsa_password") #define o utilizador e password para aceder ao broker
client.on_connect = on_connect
client.connect(broker, port)

client.loop_start()  

try:
    while True:
        coolant = round(random.uniform(10, 200), 2)    # Temperatura do liquido de arrefecimento(ºC)
        pressure = round(random.uniform(0, 8), 2)      # Pressão (bar)
        rpm = random.randint(0, 4000)                  # rotações por minuto (RPM)

        client.publish(f"machine_{group_id}/coolant", coolant)
        client.publish(f"machine_{group_id}/pressure", pressure)
        client.publish(f"machine_{group_id}/rpm", rpm)

        print(f"[SENSORS] Temperatura: {coolant} ºC | Pressão: {pressure} bar | RPM: {rpm}")
        time.sleep(2)

except KeyboardInterrupt:
    print("\nExiting publisher")
    client.disconnect()
