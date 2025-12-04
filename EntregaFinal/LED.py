import RPi.GPIO as GPIO
import time

# --- Configuración ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Definimos los pines
PIN_ROJO = 17
PIN_VERDE = 27
PIN_AZUL = 22

# Configuramos los pines como SALIDA y aseguramos que empiecen APAGADOS (LOW)
GPIO.setup(PIN_ROJO, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PIN_VERDE, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PIN_AZUL, GPIO.OUT, initial=GPIO.LOW)

# --- Funciones de Ayuda (Lógica Cátodo Común) ---
# HIGH (1) -> Envía 3.3V -> ENCIENDE
# LOW (0) -> Envía 0V -> APAGA

def apagar_todo():
    GPIO.output(PIN_ROJO, GPIO.LOW)
    GPIO.output(PIN_VERDE, GPIO.LOW)
    GPIO.output(PIN_AZUL, GPIO.LOW)

def encender_rojo():
    apagar_todo()
    GPIO.output(PIN_ROJO, GPIO.HIGH)

def encender_verde():
    apagar_todo()
    GPIO.output(PIN_VERDE, GPIO.HIGH)

def encender_azul():
    apagar_todo()
    GPIO.output(PIN_AZUL, GPIO.HIGH)