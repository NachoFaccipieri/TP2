# Guía de Instalación - Raspberry Pi 3

## 📋 Prerrequisitos

- Raspberry Pi 3 con Raspbian/Raspberry Pi OS
- Conexión a internet (para descargas iniciales)
- Cámara PiCamera configurada
- Broker MQTT (Mosquitto)
- Conexión GPIO disponible

## 🔧 Paso 1: Actualizar Sistema

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

## 📦 Paso 2: Instalar Dependencias del Sistema

```bash
# Dependencias de compilación y desarrollo
sudo apt-get install -y build-essential python3-dev python3-pip

# OpenCV (requiere varias librerías)
sudo apt-get install -y libjasper-dev libtiff5 libtiff5-dev libharfbuzz0b libwebp6

# TensorFlow y Keras (se instalan después con pip)
# También pueden requerir dependencias del sistema
sudo apt-get install -y libatlas-base-dev libjasper-dev liblapack-dev libharfbuzz0b libwebp6

# Para la cámara
sudo apt-get install -y python3-picamera

# Para GPIO
sudo apt-get install -y python3-gpiozero rpi.gpio
```

## 🐍 Paso 3: Crear Entorno Virtual (Recomendado)

```bash
cd ~/Faq/TP2/EntregaFinal

# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate
```

## 📚 Paso 4: Instalar Dependencias Python

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar paquetes principales
pip install opencv-python
pip install numpy
pip install pillow
pip install paho-mqtt
pip install flask
pip install flask-cors

# Instalar TensorFlow (puede tardar mucho)
# Para Raspberry Pi 3 es recomendable TensorFlow Lite o versiones compiladas para ARM
pip install tensorflow

# Instalar keras y facenet
pip install keras
pip install keras-facenet

# O alternativamente usar estas versiones optimizadas para Pi:
pip install tf-keras
```

## ⚙️ Paso 5: Configurar Mosquitto (MQTT Broker)

```bash
# Instalar Mosquitto
sudo apt-get install -y mosquitto mosquitto-clients

# Habilitar WebSockets en Mosquitto
sudo nano /etc/mosquitto/mosquitto.conf
```

**Agregar al final del archivo:**
```
# WebSocket listener
listener 9001
protocol websockets
```

**Guardar y reiniciar Mosquitto:**
```bash
sudo systemctl restart mosquitto
```

## 🎥 Paso 6: Habilitar Cámara PiCamera

```bash
# Abrir raspi-config
sudo raspi-config
```

- Ir a `Interfacing Options` → `Camera`
- Seleccionar `Yes` para habilitar
- Reiniciar

**Verificar cámara:**
```bash
# Tomar foto de prueba
raspistill -o test.jpg

# Ver en consola
file test.jpg
```

## 🔌 Paso 7: Verificar GPIO

```bash
# Probar lectura de GPIO
python3 << 'EOF'
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(f"GPIO 21 state: {GPIO.input(21)}")
GPIO.cleanup()
EOF
```

## 🚀 Paso 8: Ejecutar FaceID.py

**Dentro del directorio EntregaFinal:**

```bash
# Con entorno virtual
source venv/bin/activate
python3 FaceID.py

# O sin entorno virtual
python3 FaceID.py
```

**Salida esperada:**
```
Cargando MTCNN y FaceNet (TensorFlow)...
Modelos cargados.
[BOTON] Botón configurado en GPIO 21
[APP] Servicio de reconocimiento iniciando...
[SERVO] Cerrando puerta...
[LED] Estado: AZUL SOLIDO
[MQTT] Conectado al broker MQTT localhost:1883
[APP] Iniciando servidor Flask en http://0.0.0.0:5000
[APP] Sistema listo - esperando eventos...
```

## 🌐 Acceder a la Interfaz Web

Desde cualquier navegador en la misma red:

```
http://<IP_RASPBERRY_PI>:5000
```

**Para encontrar la IP:**
```bash
hostname -I
# Salida: 192.168.x.x
```

## ⚙️ Paso 9: Variables de Entorno (Opcional)

**Crear archivo `.env` en el directorio:**
```bash
# .env
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
```

**Ejecutar con variables:**
```bash
source .env
python3 FaceID.py
```

## 🛠️ Paso 10: Ejecutar como Servicio (Opcional)

**Crear archivo de servicio:**
```bash
sudo nano /etc/systemd/system/faceid.service
```

**Contenido:**
```ini
[Unit]
Description=FaceID Door Lock Service
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Faq/TP2/EntregaFinal
Environment="PATH=/home/pi/Faq/TP2/EntregaFinal/venv/bin"
ExecStart=/home/pi/Faq/TP2/EntregaFinal/venv/bin/python3 FaceID.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Habilitar servicio:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable faceid.service
sudo systemctl start faceid.service

# Verificar estado
sudo systemctl status faceid.service

# Ver logs
sudo journalctl -u faceid.service -f
```

## 🧪 Pruebas Iniciales

### Prueba 1: Conexión MQTT
```bash
# Terminal 1 - En la Raspberry
python3 FaceID.py

# Terminal 2 - En otra máquina
mosquitto_sub -h <IP_RASPBERRY> -t "cerradura/#"

# Terminal 3 - Enviar mensaje de prueba
mosquitto_pub -h <IP_RASPBERRY> -t "cerradura/status" -m "Prueba conexión"
```

### Prueba 2: Botón Físico
```bash
# Presionar botón físico y verificar que aparezca:
[BOTON] Botón presionado
[APP STATE] ESPERANDO -> PROCESANDO_RECONOCIMIENTO
```

### Prueba 3: LED
```bash
# En Python
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # Rojo
GPIO.setup(27, GPIO.OUT)  # Verde
GPIO.setup(22, GPIO.OUT)  # Azul

# Rojo
GPIO.output(17, GPIO.HIGH)
GPIO.output(27, GPIO.LOW)
GPIO.output(22, GPIO.LOW)

# Cambiar a Verde
GPIO.output(17, GPIO.LOW)
GPIO.output(27, GPIO.HIGH)
GPIO.output(22, GPIO.LOW)

# Cambiar a Azul
GPIO.output(17, GPIO.LOW)
GPIO.output(27, GPIO.LOW)
GPIO.output(22, GPIO.HIGH)

GPIO.cleanup()
```

### Prueba 4: Servo
```bash
# En Python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)
pwm = GPIO.PWM(14, 50)
pwm.start(0)

# Cerrado (0°)
pwm.ChangeDutyCycle(5)
time.sleep(1)

# Abierto (90°)
pwm.ChangeDutyCycle(7.5)
time.sleep(1)

# Cerrado nuevamente
pwm.ChangeDutyCycle(5)
time.sleep(1)

pwm.stop()
GPIO.cleanup()
```

## 📍 Solución de Problemas

### Problema: "No se puede abrir la cámara"
```bash
# Verificar que la cámara está habilitada
raspi-config

# Reiniciar
sudo reboot
```

### Problema: "ModuleNotFoundError: No module named 'RPi.GPIO'"
```bash
pip install RPi.GPIO
pip install gpiozero
```

### Problema: "Error de memoria (RAM insuficiente)"
Las librerías de TensorFlow son pesadas en Pi. Opciones:
1. Usar modelo más ligero (MobileNet)
2. Compilar TensorFlow para ARM desde fuente
3. Usar TensorFlow Lite
4. Aumentar memoria swap:

```bash
# Ver swap actual
free -h

# Aumentar swap
sudo nano /etc/dphys-swapfile
# Cambiar CONF_SWAPSIZE=100 a CONF_SWAPSIZE=2048
sudo systemctl restart dphys-swapfile
```

### Problema: "Puerto 5000 ya en uso"
```bash
# Cambiar puerto en variables de entorno
export FLASK_PORT=8080
python3 FaceID.py
```

### Problema: MQTT no se conecta
```bash
# Verificar que Mosquitto está corriendo
sudo systemctl status mosquitto

# Reiniciar Mosquitto
sudo systemctl restart mosquitto

# Ver logs
mosquitto_pub -h localhost -t "test" -m "test"
mosquitto_sub -h localhost -t "test"
```

### Problema: GPIO error "Permission denied"
```bash
# Agregar usuario pi al grupo gpio
sudo usermod -a -G gpio pi

# O ejecutar con sudo
sudo python3 FaceID.py
```

## 📊 Monitoreo

**Ver uso de memoria:**
```bash
free -h

# O con monitoreo continuo
watch -n 1 free -h
```

**Ver uso de CPU:**
```bash
top

# O solo Python
ps aux | grep python
```

**Ver temperatura:**
```bash
/opt/vc/bin/vcgencmd measure_temp
```

## 🔒 Consideraciones de Seguridad

1. **Cambiar contraseña MQTT** si se utiliza en producción
2. **Habilitar SSL/TLS** en Mosquitto
3. **Cambiar puertos por defecto** (1883, 5000, 9001)
4. **Firewall**: Solo permitir conexiones desde IP conocidas
5. **Contraseña SSH**: Cambiar contraseña por defecto de Pi
6. **Actualizar regularmente**: `sudo apt-get update && sudo apt-get upgrade`

## 📝 Logs y Debugging

**Activar más verbosidad:**
```bash
# En Python, agregar prints adicionales en FaceID.py
# O usar logging module
```

**Guardar logs en archivo:**
```bash
python3 FaceID.py > logs/$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

## 🎓 Recursos Útiles

- [Raspberry Pi GPIO Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [OpenCV on Raspberry Pi](https://docs.opencv.org/master/d7/d8b/tutorial_pi_setup.html)
- [TensorFlow on Raspberry Pi](https://www.tensorflow.org/lite/guide/python)
- [MQTT Mosquitto](https://mosquitto.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
