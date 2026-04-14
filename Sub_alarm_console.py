import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
import threading

# Pinos GPIO
GREEN_LED = 17
YELLOW_LED = 27
RED_LED = 22
BUZZER = 23

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(YELLOW_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

# Estado do sistema
sensor_data = {"coolant": 100, "pressure": 3, "rpm": 2000}
active = False
group_id = "30"  

last_message_time = time.time()
sensor_timeout = 3  # 4 segundos sem mensagens (sensors disconnected) gera um alerta

# Reset LEDs
def reset_outputs():
    GPIO.output(GREEN_LED, False)
    GPIO.output(YELLOW_LED, False)
    GPIO.output(RED_LED, False)
    GPIO.output(BUZZER, False)

# Avaliar os dados e controlar LEDs/buzzer
def update_outputs():
    
    reset_outputs()
      
    # Verifica se os dados estão dentro dos limites 
    coolant_ok = 90 <= sensor_data["coolant"] <= 105
    pressure_ok = 1 <= sensor_data["pressure"] <= 5
    rpm_ok = sensor_data["rpm"] < 2500

    if not rpm_ok:
        GPIO.output(BUZZER, True)
    
    if coolant_ok and pressure_ok:
        GPIO.output(GREEN_LED, True)
    elif coolant_ok or pressure_ok:
        GPIO.output(YELLOW_LED, True)
    else:
        GPIO.output(RED_LED, True)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

    client.subscribe(f"machine_{group_id}/#")

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    global active, last_message_time, sensor_data
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
                update_outputs
    except Exception as e:
        print(f"[ERRO] {e}")

def monitor_timeout():
    global active, last_message_time, sensor_timeout
    while True:
        if active:
            elapsed = time.time() - last_message_time
            if elapsed > sensor_timeout:
                # piscar vermelho + buzzer
                while time.time() - last_message_time > sensor_timeout:
                    GPIO.output(BUZZER, True)
                    # LED vermelho a piscar
                    GPIO.output(RED_LED, True)
                    time.sleep(0.5)
                    GPIO.output(RED_LED, False)
                    time.sleep(0.5)
        time.sleep(1)

# MQTT Setup
broker = "10.6.1.71"
port = 1883
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("srsa_sub", "srsa_password")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)

# iniciar monitor de timeout em background
threading.Thread(target=monitor_timeout, daemon=True).start()

try:
    client.loop_forever()
except KeyboardInterrupt:
    GPIO.cleanup()
    client.disconnect()
    print("\n[ALARME] Encerrado.")
