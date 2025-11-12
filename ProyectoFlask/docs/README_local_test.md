Pruebas locales (sin Raspberry)

Objetivo: probar la comunicación web <-> broker MQTT y flujo registro/timbre sin usar la Pi ni la cámara.

Opciones de prueba (elige una):

1) Test rápido usando broker público (recomendado para empezar)
 - Abre `local/index_local.html` en un navegador. Para evitar problemas de `file://` sirve la carpeta local con Python:

```powershell
# desde la carpeta del proyecto
python -m http.server 8000
# luego abre http://localhost:8000/local/index_local.html
```

 - El script local por defecto está configurado para usar el broker en tu PC: `ws://192.168.100.7:9001`.
	 Si preferís usar el broker público de pruebas, editá `local/script_local.js` y cambia `BROKER_WS` a `ws://test.mosquitto.org:8080`.
 - Ejecuta el mock que simula la Pi (opcional, aunque el broker público funciona solo como transporte):

```powershell
# en otra terminal (usa tu entorno python con paho-mqtt instalado)
python local/mock_mqtt.py
```

 - En la página: presioná "Registrar nuevo rostro" (envía `cerradura/registro`) o "Tocar timbre" (envía `cerradura/timbre`). El `mock_mqtt.py` responderá en `cerradura/persona` con datos simulados.

2) Levantar un broker Mosquitto local con WebSockets (recomiendo Docker)

 - Requiere Docker instalado. En la carpeta del proyecto hay `docs/docker-compose-mosquitto.yml` y `mosquitto/config/mosquitto.conf`.

```powershell
# desde la carpeta del proyecto
docker compose -f docs/docker-compose-mosquitto.yml up -d
```

 - Servirá 1883 y 9001 en localhost. Luego abrí `local/index_local.html` (o sirve con `python -m http.server`) y el script local lo podés editar para conectar a `ws://localhost:9001` o `ws://192.168.100.7:9001` según tu red.

3) Probar con tu propio Mosquitto en Windows

 - Si ya tenés mosquitto en Windows y tenés websockets habilitados, ajustá `local/script_local.js` para usar `ws://localhost:9001`.

Notas finales
 - El mock usa el broker TCP (1883). El front-end usa WebSockets (8080/9001). Ambos pueden comunicarse a través del mismo broker si este expone ambos protocolos.
 - No instales TensorFlow para estas pruebas. El mock no usa TF.
