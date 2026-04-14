import paho.mqtt.client as mqtt
import time
import threading

sensor_data = {"coolant": 100, "pressure": 3, "rpm": 2000}
active = False
group_id = "30"  

last_message_time = time.time()
sensor_timeout = 3

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

    client.subscribe(f"machine_{group_id}/#")

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    global active, last_message_time, sensor_data, sensor_timeout
    topic = msg.topic
    payload = msg.payload.decode()
    try:
        if "controller" in topic:
            active = payload == "ON"
            print(f"[CONTROLLER] Sistema {'Ativado' if active else 'Desativado'}")

        if active:
            if any(x in topic for x in ("coolant", "pressure", "rpm")):
                last_message_time = time.time()

                if "coolant" in topic:
                    sensor_data["coolant"] = float(payload)
                    print(f"[SENSORS] Temperatura: {sensor_data['coolant']} ºC")
                elif "pressure" in topic:
                    sensor_data["pressure"] = float(payload)
                    print(f"[SENSORS] Pressão: {sensor_data['pressure']} bar")  
                elif "rpm" in topic:
                    sensor_data["rpm"] = int(float(payload))
                    print(f"[SENSORS] RPM: {sensor_data['rpm']}")

    except Exception as e:
        print(f"[ERRO] {e}")

def monitor_timeout1():
    global active, last_message_time
    while True:
        if active:
            elapsed = time.time() - last_message_time
            if elapsed > sensor_timeout:
                print("[ALARME] timeout")
        time.sleep(1)

broker = "broker.hivemq.com" #"test.mosquitto.org"
port = 1883
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
#client.username_pw_set("srsa_sub", "srsa_password")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)

threading.Thread(target=monitor_timeout1, daemon=True).start()

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    print("\n[ALARME] Encerrado.")
