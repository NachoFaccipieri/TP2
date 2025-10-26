from flask import Flask
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# MQTT settings
MQTT_BROKER = "localhost"  # IP de la raspberry
MQTT_PORT = 1883
MQTT_TOPIC = "cerradura/persona"

# Cliente para publicar datos
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Conección a MQTT establecida")
    persona= "Mati"  #aca se tendria que ir actualizando el embedding desde la base de datos
    client.publish(topic, str(persona))


# Parte del suscriptor
def on_message(client, userdata, message):
    print("Mensaje recibido: " + message.payload.decode())

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def publish_message(data):
    mqtt_client.publish(MQTT_TOPIC, json.dumps(data))

if __name__ == '__main__':
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    app.run(host='0.0.0.0', port=5001)  # Run Flask app on a different port
    mqtt_client.loop_stop()