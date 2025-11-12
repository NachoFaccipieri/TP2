# Proyecto Cerradura - Reconocimiento Facial (FaceID)

Pequeña guía rápida para arrancar y probar el proyecto en una Raspberry Pi o en modo desarrollo.

## Resumen
Este repositorio contiene:
- `comprobarRostro.py`: servicio en Python que captura desde cámara, genera embeddings, y se comunica vía MQTT.
- `index.html`, `script.js`, `style.css`: interfaz web que se comunica con el broker MQTT por WebSockets.
- `docs/`: documentación con pasos más detallados.

## Pruebas rápidas (comandos copy-paste)
Estos pasos sirven para probar el flujo completo sin demasiada configuración.

1) Arrancar un broker MQTT (Mosquitto) localmente (si no tienes uno):

```powershell
# usando Docker (desde la carpeta del proyecto)
docker compose -f docs/docker-compose-mosquitto.yml up -d
```

Si prefieres usar el mosquitto del sistema:

```powershell
sudo apt update
sudo apt install mosquitto
sudo systemctl start mosquitto
```

2) Ejecutar el servicio de reconocimiento en la Raspberry (o PC de pruebas):

```powershell
python .\comprobarRostro.py
```

- El servicio intentará cargar MTCNN/FaceNet. Si la Pi tiene poca RAM se usan variables de entorno para reducir hilos: `RPI_LOW_RAM=1` por defecto.
- Si no tienes el pulsador físico, en la terminal donde corre `comprobarRostro.py` puedes presionar `t` + Enter para simular el timbre.

3) Abrir la interfaz web
- Sirve la carpeta con un servidor simple si abres localmente:

```powershell
python -m http.server 8000
# luego abre http://localhost:8000/index.html
```

- Conecta la web al broker (si el broker está en la Pi y la web en la Pi, usa `ws://localhost:9001` o el proxy `/mqtt` si usas nginx).

4) Flujo de prueba
- En la web: presiona "Tocar timbre" para pedir captura (o presiona `t` en la terminal de la Pi para simular si no hay pulsador).
- Cuando la Pi publique en `cerradura/persona`, la web mostrará la información.
- Usa los botones "Permitir" / "Denegar" en la web: publican en `cerradura/confirmacion` con JSON `{"permitir": true}` o `{"permitir": false}`.

5) Comandos útiles para publicar manualmente (desde otra máquina):

```powershell
# Simular timbre
mosquitto_pub -h <BROKER> -t cerradura/timbre -m "ping"
# Simular confirmación
mosquitto_pub -h <BROKER> -t cerradura/confirmacion -m '{"permitir":true}'
```

## Documentación detallada
Consulta `docs/TESTING_AND_AP.md` para instrucciones extendidas, y `docs/README_local_test.md` para pruebas locales con mocks.

---
Si quieres, puedo también:
- Añadir la sección en otro formato (más breve o más técnico).
- Incluir ejemplos de `mosquitto.conf` para habilitar WebSockets.
- Crear un script para configurar la Pi como Access Point con rollback automático.

Dime cómo prefieres que lo ajuste y lo hago.