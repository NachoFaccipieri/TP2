# SETUP - Instalación y Configuración

## ⚡ INSTALACIÓN RÁPIDA (Copiar y Pegar)

### 1️⃣ Actualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 2️⃣ Instalar Librerías Base

```bash
sudo apt install -y git python3-pip python3-dev libatlas-base-dev libjasper-dev libharfbuzz0b libwebp6 libtiff5 libjasper1 libopenjp2-7
sudo apt install -y libopenblas-dev liblapack-dev libblas-dev
sudo apt install -y mosquitto mosquitto-clients
```

### 3️⃣ Instalar Python Packages

```bash
pip install --upgrade pip setuptools
pip install opencv-python
pip install numpy
pip install pillow
pip install paho-mqtt
pip install flask flask-cors
pip install tensorflow
pip install keras
```

### 4️⃣ Habilitar Cámara (Si Usa Pi Camera)

```bash
sudo raspi-config
# Interfacing → Camera → Yes → OK
# Finish
sudo reboot
```

### 5️⃣ Verificar Cámara

```bash
raspistill -o test.jpg
# Presiona Enter, debería crear test.jpg
ls -la test.jpg
```

### 6️⃣ Configurar Mosquitto para WebSockets

```bash
# Crear archivo de configuración
sudo nano /etc/mosquitto/conf.d/websocket.conf
```

Copiar esto en el editor:
```
listener 1883
protocol mqtt

listener 9001
protocol websockets
```

Guardar: `Ctrl+X` → `Y` → `Enter`

Reiniciar Mosquitto:
```bash
sudo systemctl restart mosquitto
```

Verificar que escucha:
```bash
netstat -an | grep 9001
```

### 7️⃣ Verificar MQTT

```bash
# Terminal 1
mosquitto_sub -h localhost -t test

# Terminal 2 (otra ventana/SSH)
mosquitto_pub -h localhost -t test -m "hola"

# Terminal 1 debe mostrar: hola
```

### 8️⃣ Clonar/Descargar Proyecto

```bash
cd ~
# Si lo tienes en Git
git clone <tu-repo>
cd EntregaFinal
```

### 9️⃣ Ejecutar Sistema

```bash
# Primero registrar un rostro
sudo python3 FaceID.py

# En otro navegador ir a: http://localhost:5000
# Presiona botón "📸 Registrar Rostro"
# Luego presiona el botón físico en la puerta
# Captura el rostro
```

### 🔟 Acceder desde Otro Dispositivo

En otra computadora/teléfono:
```
http://<IP-RASPBERRY>:5000
```

Obtener IP:
```bash
hostname -I
```

---

## 🔧 CONFIGURACIÓN MANUAL (SI NECESITAS AJUSTAR)

### Variables de Configuración en FaceID.py

Línea ~30:
```python
MQTT_BROKER = "localhost"      # O tu IP de Mosquitto
MQTT_PORT = 1883
MQTT_WEBSOCKET_PORT = 9001
FLASK_PORT = 5000
```

### Pines GPIO

Línea ~20:
```python
PIN_LED_ROJO = 17
PIN_LED_VERDE = 27
PIN_LED_AZUL = 22
PIN_SERVO = 14
PIN_BOTON = 21
```

### Umbral de Reconocimiento Facial

Línea ~550 (busca `umbral`):
```python
umbral = 0.8  # 0.6-0.9 (menor = más estricto)
```

---

## ✅ VERIFICACIÓN POST-INSTALACIÓN

```bash
# 1. GPIO OK?
gpio readall

# 2. MQTT OK?
mosquitto_pub -h localhost -t test -m "ok"

# 3. Cámara OK?
raspistill -o test.jpg

# 4. Test LED
sudo python3 test_led.py

# 5. Test Botón
sudo python3 test_boton.py

# 6. Test Servo
sudo python3 test_servo.py
```

Si todos pasan ✅, ejecutar:
```bash
sudo python3 FaceID.py
```

---

## 🔄 AUTOSTART (Opcional - Ejecutar al Reiniciar)

### Crear Script

```bash
sudo nano /etc/systemd/system/faceid.service
```

Copiar:
```
[Unit]
Description=FaceID Door System
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/EntregaFinal
ExecStart=/usr/bin/python3 /home/pi/EntregaFinal/FaceID.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Guardar: `Ctrl+X` → `Y` → `Enter`

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable faceid
sudo systemctl start faceid
```

Ver estado:
```bash
sudo systemctl status faceid
```

---

## 🗑️ DESINSTALACIÓN

```bash
# Detener servicio
sudo systemctl stop faceid
sudo systemctl disable faceid

# Eliminar
sudo rm /etc/systemd/system/faceid.service

# Limpiar pip packages
pip uninstall -y opencv-python numpy pillow paho-mqtt flask tensorflow keras
```

---

## 📞 SOPORTE RÁPIDO

| Problema | Comando |
|----------|---------|
| ¿Funciona Mosquitto? | `mosquitto_pub -h localhost -t test -m "test"` |
| ¿Puedo acceder a web? | `curl http://localhost:5000/api/status` |
| ¿GPIO funciona? | `gpio readall` |
| ¿LED enciende? | `sudo python3 test_led.py` |
| ¿Botón responde? | `sudo python3 test_boton.py` |
| Ver logs FaceID | `sudo python3 FaceID.py 2>&1 \| tail -20` |
| Limpiar GPIO | `sudo python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()"` |

---

**Última actualización: Diciembre 2025**
