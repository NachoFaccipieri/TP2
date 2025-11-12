# Guía rápida: Mosquitto (WebSockets) + nginx para Raspberry Pi

Esta guía explica cómo habilitar WebSockets en Mosquitto para que la página web
pueda usar MQTT desde el navegador (mqtt.js), y cómo servir los archivos estáticos
con nginx. Está pensada para una Raspberry Pi que ejecutará el reconocimiento
por camera y Mosquitto como broker.

Resumen de la arquitectura
- Mosquitto (broker MQTT) — corre en la Raspberry Pi. Escucha 1883 (MQTT) y 9001 (WebSockets).
- nginx — sirve la carpeta web (index.html, script.js). Opcionalmente proxy WSS a mosquitto para TLS.
- Servicio Python (`comprobarRostro.py`) — se conecta al broker MQTT y escucha topics `cerradura/registro` y `cerradura/timbre`.

1) Instalar Mosquitto y clientes

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
```

2) Habilitar WebSockets en Mosquitto

- Copiar el archivo de ejemplo `docs/mosquitto_ws.conf` a `/etc/mosquitto/conf.d/01-websockets.conf`:

```bash
sudo cp docs/mosquitto_ws.conf /etc/mosquitto/conf.d/01-websockets.conf
```

- (Opcional) deshabilitar allow_anonymous y crear usuarios:

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd tu_usuario
# Luego en el conf añadir:
# allow_anonymous false
# password_file /etc/mosquitto/passwd
```

- Reiniciar Mosquitto:

```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

3) (Opcional pero recomendado) Servir la web con nginx

- Instalar nginx:

```bash
sudo apt install nginx
```

- Crear la carpeta web y copiar los archivos del proyecto (`index.html`, `script.js`, `style.css`):

```bash
sudo mkdir -p /var/www/faceid
sudo cp -r * /var/www/faceid/   # o copiar los archivos relevantes
sudo chown -R www-data:www-data /var/www/faceid
```

- Copiar el archivo de configuración de ejemplo `docs/nginx_faceid.conf` a `/etc/nginx/sites-available/faceid` y habilitarlo:

```bash
sudo cp docs/nginx_faceid.conf /etc/nginx/sites-available/faceid
sudo ln -s /etc/nginx/sites-available/faceid /etc/nginx/sites-enabled/faceid
sudo nginx -t
sudo systemctl restart nginx
```

Si querés exponer todo por HTTPS (recomendado para producción), usar `certbot` para obtener certificados y ajustar el bloque `server` para `listen 443 ssl;`.

4) Notas sobre WebSockets y TLS

- Si abrís la web por http:// (sin TLS), el cliente mqtt.js puede conectar directamente a ws://<raspberry>:9001.
- Si abrís la web por https:// (TLS), el navegador exigirá WSS (wss://). Tenés dos opciones:
  - Configurar mosquitto con TLS directamente (más complejo). 
  - Preferible: usar nginx como terminador TLS y proxy inverso a mosquitto websocket. En `docs/nginx_faceid.conf` hay un bloque comentado que muestra cómo hacer `location /mqtt` y `proxy_pass http://localhost:9001;`.

5) Probar la conexión desde el navegador

- Abrí la web desde la Raspberry: http://raspberry.local/ (o su IP)
- La página intentará conectar vía ws://<host>:9001. Si usás nginx/HTTPS y proxy, ajusta `script.js` para apuntar a `/mqtt` en lugar de `ws://host:9001`.

6) Probar Mosquitto con clientes desde la Raspberry

```bash
# Suscribirse en modo websocket:
mosquitto_sub -h localhost -t 'cerradura/persona' -p 9001 -V mqttv311

# Publicar (ejemplo desde la Raspberry, usando TCP 1883):
mosquitto_pub -h localhost -t 'cerradura/registro' -m '{"nombre":"Mati"}'
```

7) Seguridad y producción

- Habilitar autenticación (password_file) y ACLs.
- Limitar acceso de red al broker (firewall) si corresponde.
- Hacer backups regulares de `embeddings.txt` y `names.txt`.

8) Siguientes pasos (cuando tengas la Raspberry y cámara)

- (C) Probar todo en local: instalar dependencias de Python y ejecutar `comprobarRostro.py`.
- Ajustar el umbral de distancia y probar con varias imágenes.
- Si querés, te ayudo a automatizar el arranque del servicio con `systemd`.

---
Si querés, ahora creo el `systemd` unit file para `comprobarRostro.py` y/o una versión del `script.js` que use `/mqtt` como endpoint (para cuando uses nginx proxy con TLS). ¿Qué preferís ahora: el unit file o ajustar `script.js` para proxy? 
