import paho.mqtt.client as mqtt

#Defino los parametros de conexión
broker = "localhost"    #ip de raspberry en futuro.
port = 1883
topic = "cerradura/persona"

#Creo cliente MQTT para publicar los datos.
client= mqtt.Client()

#Definimos una funcion para cuando nos conectemos al broker.
def on_connect(client, userdata, flag, rc, properties=None):
    if rc == 0:
        print("Me conecte al broker MQTT Mosquitto!")
        client.subscribe(topic)
        print(f"Suscrito al topic: {topic}")
    else:
        print("Error al conectarse al broker MQTT Mosquitto.")

#Cuando llegue un nuevo mensaje al topic lo muestro.
def on_message(client, userdata, msg):
    print(f"Mensaje recibido en el topic {msg.topic}: {msg.payload.decode()}")
        
#Asignamos la funcion a usar cuando nos conectemos y nos conectamos. 
client.on_connect= on_connect
client.on_message= on_message
client.connect(broker, port, 60)

#Dejo conexion en loop
client.loop_forever()


        