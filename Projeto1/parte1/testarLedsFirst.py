# alarm_console.py
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time

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

# Meter tudo apagado no inicio 
GPIO.output(GREEN_LED, False)
GPIO.output(YELLOW_LED, False)
GPIO.output(RED_LED, False)
GPIO.output(BUZZER, False)

# testar um led para ver se nao explode:
GPIO.output(GREEN_LED, True)
time.sleep(1)
GPIO.output(GREEN_LED, False)

# testar o som para ver se nao pega fogo:
GPIO.output(BUZZER, True)
time.sleep(1)
GPIO.output(BUZZER, False)