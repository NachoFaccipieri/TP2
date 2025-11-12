# Pruebas locales y configuración rápida como Access Point

Este documento explica cómo probar el proyecto sin hardware extra y cómo configurar la Raspberry Pi como Access Point (AP) para acceder a la web desde un móvil.

## 1) Pruebas locales (sin pulsador físico)

Requisitos:
- Broker MQTT (Mosquitto) accesible desde la Raspberry (o local).
- Página web (`index.html` + `script.js`) que usa mqtt.js para comunicarse.
- `comprobarRostro.py` en la Raspberry (o PC de pruebas).

Pasos básicos:
1. Arranca el broker MQTT. En la Raspberry puedes usar `mosquitto` o el contenedor que prefieras.
2. Ejecuta el script de reconocimiento:

```powershell
python .\comprobarRostro.py
```

3. En la Raspberry (si no tienes el pulsador conectado) puedes simular el timbre desde la terminal donde corre el script: presiona `t` y luego Enter. El script publicará en `cerradura/timbre` y ejecutará la captura.

4. Alternativa: desde otra máquina o desde la web (si ya está conectada al broker), publica manualmente en el topic para forzar la captura:

```powershell
# usando mosquitto_pub
mosquitto_pub -h <BROKER> -t cerradura/timbre -m "ping"
```

5. La web mostrará la persona detectada en `cerradura/persona`. Usa los botones "Permitir"/"Denegar" para publicar la confirmación en `cerradura/confirmacion`.

Formato recomendado para confirmación (web -> Pi):

```json
{ "permitir": true }
```

o

```json
{ "permitir": false }
```

El script `comprobarRostro.py` espera hasta 15 segundos por la confirmación.

## 2) Probar sin modelos (modo desarrollo)

Si no quieres cargar MTCNN/FaceNet (por memoria o instalación), puedes comentar temporalmente la carga de modelos al inicio de `comprobarRostro.py` y simular `cerradura/persona` desde la web o con `mosquitto_pub`.

## 3) Configurar Raspberry Pi como Access Point (resumen rápido)

Advertencia: estos pasos cambian la configuración de red. Hazlos con acceso físico a la Pi o asegúrate de saber cómo revertir los cambios.

1. Instala paquetes necesarios:

```bash
sudo apt update
sudo apt install hostapd dnsmasq
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

2. Configura una IP estática para la interfaz WLAN (ejemplo `/etc/dhcpcd.conf`):

Añade al final:

```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

3. Configura `dnsmasq` (respalda el original primero):

```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

Y pega:

```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

4. Crea `/etc/hostapd/hostapd.conf` con algo así:

```
interface=wlan0
driver=nl80211
ssid=MiCerraduraAP
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=UnaClaveSegura
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

5. Apunta `DAEMON_CONF` en `/etc/default/hostapd` al archivo creado:

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

6. Habilita y arranca servicios:

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

7. Prueba conectar con tu móvil a la red WiFi `MiCerraduraAP` usando la contraseña indicada. Abre el navegador y visita `http://192.168.4.1` (si sirves la web desde la Pi). Ajusta el broker MQTT en la web si el broker está en la Pi (usando proxy o WebSockets).

## 4) Notas y recomendaciones
- Si usas Mosquitto con WebSockets necesitas configurar `listener 9001` y `protocol websockets` o usar Nginx como proxy hacia `/mqtt` (hay ejemplos en `docs/` del repo).
- Para producción considera seguridad: contraseña del AP, autenticación en Mosquitto y TLS si expones servicios.
- Ajusta los pines GPIO en variables de entorno `LED_R_PIN`, `LED_G_PIN`, `LED_B_PIN`, `BUTTON_PIN` si tu cableado es distinto.

---
Si quieres, actualizo también la sección README local con un resumen rápido y/o genero un script para crear la AP automáticamente (con rollback). ¿Qué prefieres ahora?