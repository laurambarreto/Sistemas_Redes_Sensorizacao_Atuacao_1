# Projeto IoT: Sistema de Monitorização e Alarme via MQTT

Este projeto consiste num sistema distribuído de Internet of Things (IoT) para monitorização em tempo real de uma máquina industrial. O sistema utiliza o protocolo **MQTT** (arquitetura *Publish/Subscribe*) para comunicar dados de telemetria entre sensores, um controlador remoto e uma consola de alarmes física baseada num **Raspberry Pi**.

---

## Arquitetura e Componentes do Sistema

O projeto está dividido em três componentes principais, separando a lógica de simulação, controlo e atuação física:

### 1. Sensores (Publisher) - `Pub_sensors.py`
Simula o funcionamento de sensores industriais (Edge Computing). 
* Gera dados de telemetria em tempo real: **Temperatura do Líquido de Arrefecimento (ºC)**, **Pressão (bar)** e **Rotações por Minuto (RPM)**.
* Publica continuamente estes valores no *broker* MQTT (ex: tópico `machine_30/coolant`).

### 2. Controlador Remoto (Publisher) - `Pub_controller.py`
Interface de controlo remoto para o operador da máquina.
* Permite enviar comandos (`ON` / `OFF`) para ligar ou desligar a consola de alarmes remotamente através do tópico `machine_30/controller`.

### 3. Consola de Alarmes (Subscriber & Hardware) - `Sub_alarm_console.py`
O núcleo do sistema de alerta. Corre num **Raspberry Pi** e reage aos dados recebidos.
* **Integração de Hardware:** Controla LEDs (Verde, Amarelo, Vermelho) e um Buzzer através dos pinos GPIO.
* **Lógica de Estado (Business Logic):**
  * 🟢 **LED Verde:** Pressão (1 a 5 bar) e Temperatura (90 a 105 ºC) nos valores ideais.
  * 🟡 **LED Amarelo (Warning):** Um dos parâmetros (Pressão ou Temperatura) está fora dos limites normais.
  * 🔴 **LED Vermelho (Danger):** Ambos os parâmetros estão em valores críticos.
  * 🔊 **Buzzer:** Acionado imediatamente se as RPMs ultrapassarem o limite seguro (2500 RPM).
* **Tolerância a Falhas (Watchdog/Timeout):** Utiliza *Multi-threading* para monitorizar a "saúde" da ligação. Se os sensores deixarem de enviar dados por mais de 3 segundos (ex: falha de rede ou sensor danificado), o sistema entra em modo de emergência (LED vermelho a piscar + Buzzer contínuo).

---

## Tecnologias e Conceitos Aplicados

* **Linguagem:** Python
* **Protocolo IoT:** MQTT (`paho-mqtt` library)
* **Hardware:** Raspberry Pi, Pinos GPIO, LEDs, Buzzer Ativo
* **Integração de Hardware:** `RPi.GPIO`
* **Conceitos de Engenharia de Software:**
  * **Concorrência:** Uso da biblioteca `threading` para monitorização paralela do *timeout* sem bloquear a receção de mensagens MQTT.
  * **Segurança:** Autenticação no broker MQTT com credenciais configuradas.
  * **Event-Driven Architecture:** Reação assíncrona baseada em eventos (callbacks MQTT).

---

## Como Executar

1. É necessário um Broker MQTT a correr (ex: *Mosquitto*) no IP configurado (`10.6.1.71` ou outro correspondente).
2. No Raspberry Pi, executa o subscritor:
   ```bash
   python Sub_alarm_console.py
