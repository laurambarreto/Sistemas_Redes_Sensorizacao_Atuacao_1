import paho.mqtt.client as mqtt
import time
import json
import socket

GroupID = "30"  
machine_id = "M1"
ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host, port = "127.0.0.1", 5002 

alarme_por_parametro = {
    "rpm": 0,
    "coolant_temperature": 0,
    "oil_pressure": 0,
    "battery_potential": 0,
    "consumption": 0
}

start_time = time.time()
tempo_limite = 5 * 60  # 5 minutos em segundos

def enviar_alerta_nivel(nivel):
    mensagem = {
        "type": "alert",
        "level": nivel,
        "reason": f"Máquina em estado {nivel} - múltiplos sensores fora dos limites"
    }
    ClientSocket.sendto(json.dumps(mensagem).encode(), (host, port))
    print(f"[ALERTA] Enviado ALERTA {nivel} para {host}:{port}")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

    # From Machine_Data_Manager
    client.subscribe(f"{GroupID}/{machine_id}/Machine_Data_Manager")

# Callback ao receber mensagem MQTT
def on_message(client, userdata, msg):
    global active, last_message_time, alarme_por_parametro
    try:
        mensagem = json.loads(msg.payload.decode())
        parametro = mensagem.get("parameter")

        if parametro in alarme_por_parametro:
            alarme_por_parametro[parametro] += 1
        
        # Verifica o tempo e condição crítica
        tempo_passado = time.time() - start_time
        parametros_ativos = [p for p, v in alarme_por_parametro.items() if v > 0]

        if tempo_passado <= tempo_limite:
            if len(parametros_ativos) >= 5:
                enviar_alerta_nivel("CRITICAL")

            elif len(parametros_ativos) >= 3:
                enviar_alerta_nivel("DANGER")

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