"""
Cliente mock para pruebas locales. No usa TensorFlow ni cámara.
Se conecta a un broker MQTT (por defecto test.mosquitto.org) y responde a:
- 'cerradura/registro' -> publica en 'cerradura/persona' confirmación
- 'cerradura/timbre'  -> publica en 'cerradura/persona' con resultado aleatorio

Uso:
  python local/mock_mqtt.py

Configurable via ENV:
  MQTT_BROKER (default test.mosquitto.org)
  MQTT_PORT (default 1883)

Nota: para la web necesitamos un broker con WebSockets; test.mosquitto.org provee ws://test.mosquitto.org:8080
Este script usa la conexión TCP estándar (1883) al broker público.
"""
import os
import json
import time
import random
import paho.mqtt.client as mqtt

BROKER = os.environ.get('MQTT_BROKER', '192.168.100.7')
PORT = int(os.environ.get('MQTT_PORT', '1883'))
TOPIC_REG = 'cerradura/registro'
TOPIC_TIM = 'cerradura/timbre'
TOPIC_RESP = 'cerradura/persona'
TOPIC_STATUS = 'cerradura/status'

def on_connect(client, userdata, flags, rc):
    print('Conectado al broker', BROKER, 'rc=', rc)
    client.subscribe(TOPIC_REG)
    client.subscribe(TOPIC_TIM)

def on_message(client, userdata, msg):
    print('Mensaje rec:', msg.topic, msg.payload)
    if msg.topic == TOPIC_REG:
        try:
            data = json.loads(msg.payload)
            nombre = data.get('nombre', 'SinNombre')
        except Exception:
            nombre = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)
        # Simular demora de captura y guardado
        client.publish(TOPIC_STATUS, f'Registrando {nombre}')
        time.sleep(1)
        client.publish(TOPIC_RESP, json.dumps({'ok': True, 'mensaje': f'Rostro {nombre} registrado'}))

    elif msg.topic == TOPIC_TIM:
        client.publish(TOPIC_STATUS, 'Timbre recibido - capturando')
        time.sleep(1)
        # Respuesta aleatoria para simular coincidencia
        if random.random() < 0.5:
            nombre = random.choice(['Mati','Ana','Jorge','Invitado'])
            dist = round(random.uniform(0.3, 0.9), 3)
            client.publish(TOPIC_RESP, json.dumps({'ok': True, 'coincidencia': True, 'nombre': nombre, 'distancia': dist, 'mensaje': 'Coincidencia encontrada'}))
        else:
            dist = round(random.uniform(1.1, 2.5), 3)
            client.publish(TOPIC_RESP, json.dumps({'ok': True, 'coincidencia': False, 'distancia': dist, 'mensaje': 'No coincide con la base'}))

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print('Interrumpido')

if __name__ == '__main__':
    print('Mock MQTT client - broker:', BROKER, 'port:', PORT)
    main()
