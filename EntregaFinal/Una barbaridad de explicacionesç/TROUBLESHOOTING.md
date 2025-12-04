# TROUBLESHOOTING - Problemas y Soluciones

## 🔴 LED Siempre Rojo

**Causa:** No ejecutas con `sudo`

**Solución:**
```bash
sudo python3 FaceID.py
```

---

## 🔴 Botón No Funciona

**Error:** `RuntimeError: Failed to add edge detection`

**Causa:** Falta de permisos o GPIO en uso

**Soluciones (Prueba en orden):**

```bash
# 1. Ejecutar con sudo
sudo python3 FaceID.py

# 2. Si sigue sin funcionar, limpiar GPIO
sudo pkill -f python3
sleep 1
sudo python3 FaceID.py

# 3. Si aún no anda, agregar usuario al grupo GPIO
sudo usermod -a -G gpio $USER
# Luego reinicia la sesión o usa sudo

# 4. Última opción: Reiniciar Pi
sudo reboot
```

---

## 🔴 MQTT No Conecta

**Síntoma:** Dice "Conectando..." pero no conecta

**Soluciones:**

```bash
# 1. Verificar Mosquitto está corriendo
sudo systemctl status mosquitto

# 2. Si no está, iniciar
sudo systemctl start mosquitto

# 3. Ver si escucha
mosquitto_pub -h localhost -t test -m "test"
mosquitto_sub -h localhost -t test

# 4. Ver logs de Mosquitto
sudo tail -f /var/log/mosquitto/mosquitto.log
```

---

## 🔴 "Permiso Denegado" en GPIO

**Síntoma:** `Permission denied` o similar

**Solución:**
```bash
# Ejecutar con sudo
sudo python3 FaceID.py

# O agregar usuario a grupo GPIO
sudo usermod -a -G gpio $USER
```

---

## 🔴 Cámara No Funciona

**Síntoma:** Error al capturar imagen

```bash
# Verificar cámara está habilitada
raspi-config  # Interfacing → Camera → Yes

# Probar cámara
raspistill -o test.jpg
```

---

## 🔴 Puerto 5000 en Uso

**Síntoma:** "Address already in use"

```bash
# Cambiar puerto
export FLASK_PORT=8080
sudo python3 FaceID.py

# O matar lo que usa el puerto
sudo lsof -i :5000
sudo kill -9 <PID>
```

---

## 🔴 LED No Enciende de Ningún Color

**Posibles causas:**

1. **Desconexión física**
   - Verificar cables
   - GND debe estar en pin LARGO

2. **Polaridad invertida**
   - Pin largo = GND (cátodo)
   - Patas cortas = GPIO (ánodos)

3. **Test manual**
   ```bash
   sudo python3 test_led.py
   ```

---

## 🔴 Botón No Responde (Test OK)

**Si `test_boton.py` funciona pero el sistema no:**

1. Estado de app está bloqueado
2. Probar presionando en diferentes momentos
3. Ver logs:
   ```bash
   sudo python3 FaceID.py 2>&1 | grep BOTON
   ```

---

## 🔴 Servo No Se Mueve

**Posibles causas:**

1. **Sin alimentación 5V externa**
   - El servo NECESITA 5V aparte (no de la Pi)

2. **Desconexión física**
   - Signal en GPIO 14
   - 5V del servo en fuente externa
   - GND en común

3. **Test manual**
   ```bash
   sudo python3 test_servo.py
   ```

---

## 🔴 Memoria Insuficiente

**Síntoma:** TensorFlow no carga

```bash
# Ver memoria
free -h

# Aumentar swap
sudo nano /etc/dphys-swapfile
# Cambiar: CONF_SWAPSIZE=2048
sudo systemctl restart dphys-swapfile

# Esperar a que termine
sleep 10

# Probar nuevamente
sudo python3 FaceID.py
```

---

## 🔴 Reconocimiento No Funciona

**Si captura pero no reconoce:**

1. Registrar nuevo rostro primero
2. Verificar embeddings.txt no está vacío
3. Probar con más iluminación
4. Cambiar umbral en FaceID.py línea ~550:
   ```python
   umbral = 0.8  # Menor = más estricto
   ```

---

## 🔴 Web Accesible Pero Nada Funciona

**Síntoma:** Página carga pero no hay respuesta

1. Verificar Flask está corriendo
   ```bash
   ps aux | grep FaceID
   ```

2. Ver logs
   ```bash
   sudo python3 FaceID.py 2>&1 | tail -20
   ```

3. Probar API
   ```bash
   curl http://localhost:5000/api/status
   ```

---

## 🔴 "ImportError" - Librerías Faltantes

**Solución:**
```bash
pip install opencv-python
pip install numpy
pip install pillow
pip install paho-mqtt
pip install flask
pip install flask-cors
pip install tensorflow
pip install keras
pip install keras-facenet
```

---

## 🆘 SI NADA FUNCIONA

**Hacer esto en orden:**

```bash
# 1. Limpiar todo
sudo pkill -f python3
sudo pkill -f mosquitto
sleep 2

# 2. Reiniciar servicios
sudo systemctl start mosquitto
sleep 2

# 3. Limpiar GPIO
python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()" 2>/dev/null

# 4. Ejecutar con sudo
sudo python3 FaceID.py
```

Si sigue sin funcionar:

```bash
# Reiniciar la Pi
sudo reboot
```

---

## 📝 VERIFICACIONES ANTES DE REPORTE

Antes de reportar un problema, verifica:

```bash
# 1. ¿Ejecutas con sudo?
# 2. ¿GPIO readall muestra los pines?
gpio readall

# 3. ¿test_*.py funcionan?
sudo python3 test_led.py
sudo python3 test_boton.py

# 4. ¿MQTT conecta?
mosquitto_pub -h localhost -t test -m "test"

# 5. ¿Mosquitto escucha en 9001?
netstat -an | grep 9001
```

---

**Última actualización: Diciembre 2025**
