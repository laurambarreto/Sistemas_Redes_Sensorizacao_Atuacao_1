import paho.mqtt.client as mqtt

broker = "10.6.1.71" # para testes em casa, 10.6.1.9 na defesa
port = 1883
group_id = "30"  
topic = f"machine_{group_id}/controller"

client = mqtt.Client()
client.connect(broker, port)

def send_command(command):
    client.publish(topic, command)
    print(f"\n[CONTROLLER] Enviado: {command}")

# Menu
while True:
    print("\n1 - Ligar consola remota")
    print("2 - Desligar consola remota")
    print("0 - Sair")
    opcao = input("Escolha: ")

    if opcao == "1":
        send_command("ON")
    elif opcao == "2":
        send_command("OFF")
    elif opcao == "0":
        print("A sair...")
        break
    else:
        print("Opção inválida.")
