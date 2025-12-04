# FaceID - Guía Rápida

## ⚡ PARA QUE ANDE TODO AHORA

```bash
sudo python3 FaceID.py
```

Accede a: `http://<IP_RASPBERRY>:5000`

---

## 🔴 PROBLEMAS COMUNES (Solo Los Que Importan)

| Problema | Solución |
|----------|----------|
| **LED rojo siempre** | Ejecutar con `sudo` |
| **Botón no funciona** | Ejecutar con `sudo` |
| **"Failed to add edge detection"** | Ejecutar con `sudo` |
| **MQTT no conecta** | Ver TROUBLESHOOTING.md |
| **No veo la web** | `hostname -I` para obtener IP |

**El 99% de los problemas se resuelven con `sudo`**

---

## 🔧 HARDWARE

```
GPIO 17 → LED Rojo
GPIO 27 → LED Verde
GPIO 22 → LED Azul
GPIO 14 → Servo (PWM)
GPIO 21 → Botón

GND → LED (pin LARGO) + Botón
5V → Servo (alimentación EXTERNA)
```

---

## 🟡🔵🟢🔴 SIGNIFICADO COLORES LED

- 🟡 **Amarillo titilando** = Conectando
- 🔵 **Azul sólido** = Sistema listo
- 🟡 **Amarillo sólido** = Procesando rostro
- 🟢 **Verde 10s** = Acceso permitido
- 🔴 **Rojo 10s** = Acceso denegado
- 🔵 **Azul titilando** = Registrando

---

## 👤 CÓMO USAR

### Entrar (Ya registrado)
1. Presiona botón físico
2. Espera resultado en web
3. Presiona "Permitir" o "Denegar"
4. Puerta se abre 10 segundos si permitiste

### Registrar Nuevo Rostro
1. Web: "Registrar nuevo rostro" + nombre
2. Presiona botón físico cuando pida
3. Se guarda automáticamente

---

## 🧪 PRUEBAS RÁPIDAS

```bash
# Test LED
sudo python3 test_led.py

# Test Botón
sudo python3 test_boton.py

# Test Servo
sudo python3 test_servo.py
```

---

## 📋 INSTALACIÓN (Quick Version)

```bash
# Actualizar
sudo apt-get update && sudo apt-get upgrade -y

# Instalar dependencias
sudo apt-get install -y python3-pip mosquitto mosquitto-clients

# Instalar paquetes Python
pip install opencv-python numpy pillow paho-mqtt flask flask-cors tensorflow keras keras-facenet

# Habilitar cámara
sudo raspi-config  # Interfacing → Camera → Yes

# Habilitar WebSocket en Mosquitto
sudo nano /etc/mosquitto/mosquitto.conf
# Agregar al final:
# listener 9001
# protocol websockets

# Reiniciar Mosquitto
sudo systemctl restart mosquitto

# Ejecutar
cd ~/Faq/TP2/EntregaFinal
sudo python3 FaceID.py
```

---

## 🎯 LO QUE CAMBIÓ

- ✅ Botón físico (GPIO 21) funciona
- ✅ LED RGB (GPIO 17/27/22) con colores según estado
- ✅ Servo (GPIO 14) abre/cierra automáticamente
- ✅ Web actualizada (botón timbre removido)
- ✅ Máquinas de estado para todo

---

## 🆘 MÁS PROBLEMAS

→ Ver `TROUBLESHOOTING.md`

---

**Versión 1.0 | Diciembre 2025 | Estado: ✅ FUNCIONAL**
