import paho.mqtt.client as mqtt

#Defino los parametros de conexión
broker = "localhost"    #ip de raspberry en futuro.
port = 1883
topic = "cerradura/persona"

#Creo cliente MQTT para publicar los datos.
client= mqtt.Client()

#Definimos una funcion para cuando nos conectemos al broker.
def on_connect(client, userdata, flag, rc):
    print("Me conecte al broker MQTT Mosquitto!")
    persona= "Mati"  #aca se tendria que ir actualizando el embedding desde la base de datos
    client.publish(topic, str(persona))


#Asignamos la funcion a usar cuando nos conectemos y nos conectamos. 
client.on_connect= on_connect
client.connect(broker, port, 60)

#Dejar el cliente en un loop infinito para que se mantenga conectado.
client.loop_forever()