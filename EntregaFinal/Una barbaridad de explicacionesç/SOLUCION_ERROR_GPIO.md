# 🐛 Solución: Error "Failed to add edge detection"

## ❌ Problema

```
RuntimeError: Failed to add edge detection
```

Este error ocurre cuando:
1. El script NO se ejecuta con permisos `sudo`
2. El GPIO ya está siendo utilizado por otro proceso
3. El PIN está configurado incorrectamente

---

## ✅ Soluciones

### Solución 1: Ejecutar con SUDO (Recomendado)

El acceso a GPIO requiere permisos de administrador:

```bash
sudo python3 FaceID.py
```

**O si tienes entorno virtual:**

```bash
sudo /home/pi/ruta/venv/bin/python3 FaceID.py
```

---

### Solución 2: Agregar usuario al grupo GPIO

Para no necesitar `sudo` cada vez:

```bash
# 1. Agregar usuario al grupo gpio
sudo usermod -a -G gpio $USER

# 2. Agregar reglas udev
sudo nano /etc/udev/rules.d/99-gpio.rules

# Agregar esta línea:
SUBSYSTEM=="gpio", KERNEL=="gpio*", ACTION=="add", MODE="0660", GROUP="gpio"

# 3. Reiniciar
sudo reboot
```

---

### Solución 3: Limpiar GPIO anterior

Si hay un proceso anterior usando GPIO:

```bash
# 1. Encontrar el proceso
ps aux | grep python

# 2. Matar el proceso (reemplaza PID)
kill -9 <PID>

# 3. Limpiar GPIO
python3 << 'EOF'
import RPi.GPIO as GPIO
GPIO.cleanup()
print("GPIO limpiado")
EOF

# 4. Intentar de nuevo
sudo python3 FaceID.py
```

---

### Solución 4: Usar gpiozero con permisos

Si prefieres usar `gpiozero`:

```bash
# Instalar gpiozero
pip install gpiozero

# Configurar permisos
sudo usermod -a -G gpio $USER
sudo usermod -a -G dialout $USER
```

---

## 🔍 Verificar Configuración

### Verificar que GPIO está disponible

```bash
# Ver estado de GPIO
gpioinfo

# Ver qué GPIOs están en uso
cat /proc/device-tree/gpio/
```

### Verificar permisos

```bash
# Ver si tienes permisos
ls -la /dev/gpiomem

# Debería mostrar algo como:
# crw-rw---- 1 root gpio 247, 0 Dec  4 10:00 /dev/gpiomem
```

### Test rápido

```bash
# Probar GPIO con sudo
sudo python3 << 'EOF'
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(f"GPIO 21 state: {GPIO.input(21)}")
GPIO.cleanup()
print("✅ GPIO funciona!")
EOF
```

---

## 📋 Checklist de Ejecución

- [ ] Ejecutar con `sudo python3 FaceID.py`
- [ ] Verificar que GPIO está disponible con `ls -la /dev/gpiomem`
- [ ] No hay otro proceso Python usando GPIO
- [ ] Raspberry Pi tiene permisos correctos
- [ ] El botón está conectado a GPIO 21
- [ ] GND está conectado a tierra

---

## 🚀 Comando Correcto

**Para Raspberry Pi OS:**

```bash
# Opción 1: Con sudo (siempre funciona)
cd /home/pi/EntregaFinal
sudo python3 FaceID.py

# Opción 2: Si configuraste permisos GPIO
cd /home/pi/EntregaFinal
python3 FaceID.py

# Opción 3: Desde entorno virtual con sudo
cd /home/pi/EntregaFinal
source venv/bin/activate
sudo $VIRTUAL_ENV/bin/python3 FaceID.py
```

---

## 📊 Mejoras Implementadas en FaceID.py

Se agregaron mejoras para mayor robustez:

1. **Limpieza de GPIO anterior**: `GPIO.cleanup()` antes de inicializar
2. **Mejor manejo de errores**: Try-catch más específico
3. **Remover eventos previos**: `GPIO.remove_event_detect()` antes de agregar
4. **Mensajes informativos**: Indicar si GPIO no funciona
5. **Sistema continúa**: Si GPIO falla, el sistema sigue funcionando (sin hardware)

---

## 🔧 Comando Definitivo para Raspberry Pi

```bash
# Cambiar a directorio del proyecto
cd ~/Faq/TP2/EntregaFinal

# Ejecutar con permisos sudo
sudo python3 FaceID.py
```

**Salida esperada:**

```
[GPIO] Inicialización exitosa
Cargando MTCNN y FaceNet (TensorFlow)...
Modelos cargados.
[BOTON] Botón configurado en GPIO 21
[APP] Servicio de reconocimiento iniciando...
[SERVO] Cerrando puerta...
[LED] Estado: AZUL SOLIDO
[MQTT] Conectado al broker MQTT localhost:1883
[APP] Iniciando servidor Flask en http://0.0.0.0:5000
[APP] Accede a la interfaz web desde: http://<IP_RASPBERRY>:5000
[APP] Sistema listo - esperando eventos...
```

---

## 📞 Si sigue sin funcionar

### Opción A: Usar polling del botón (Sin edge detection)

Si sigue fallando, puedes usar polling en lugar de edge detection:

```python
# Reemplazar setup_boton() con:
def setup_boton():
    """Configura polling del botón"""
    global boton_thread
    if GPIO_INITIALIZED:
        print("[BOTON] Usando polling en lugar de edge detection")
        boton_thread = threading.Thread(target=_button_polling_loop, daemon=True)
        boton_thread.start()

def _button_polling_loop():
    """Loop de polling del botón"""
    prev_state = GPIO.HIGH
    while True:
        try:
            current_state = GPIO.input(PIN_BOTON)
            if current_state == GPIO.LOW and prev_state == GPIO.HIGH:
                print("[BOTON] Botón presionado (polling)")
                on_boton_presionado(PIN_BOTON)
            prev_state = current_state
            time.sleep(0.1)
        except:
            time.sleep(0.5)
```

### Opción B: Desabilitar botón completamente

Si no necesitas el botón físico, comenta la línea en `main_flask()`:

```python
def main_flask():
    print('[APP] Servicio de reconocimiento iniciando...')
    
    # Inicializar barrera en posición cerrada
    if GPIO_INITIALIZED:
        cerrar_puerta()
    
    # COMENTAR ESTA LÍNEA SI EL BOTON NO FUNCIONA:
    # setup_boton()
    
    # Resto del código...
```

---

## ✨ Alternativa: Usar Solo Web (Sin Hardware)

Si no tienes permiso GPIO, puedes usar solo la interfaz web:

```bash
# Desabilitar GPIO
export GPIO_DISABLED=1

# O modificar FaceID.py:
GPIO_INITIALIZED = False  # Forzar a False

# Luego ejecutar sin sudo
python3 FaceID.py
```

El sistema funcionará con:
- ✅ Interfaz web
- ✅ MQTT
- ✅ Reconocimiento facial
- ❌ LED (no funciona)
- ❌ Servo (no funciona)
- ❌ Botón (no funciona)

---

## 🎯 Resumen

| Problema | Solución |
|----------|----------|
| "Failed to add edge detection" | Ejecutar con `sudo python3 FaceID.py` |
| "Permission denied" | Agregar usuario a grupo `gpio` |
| "GPIO already in use" | Matar proceso anterior: `killall python3` |
| "Pin already configured" | `GPIO.cleanup()` antes de inicializar |

---

**Versión**: 1.1  
**Actualización**: Se agregó mejor manejo de errores en FaceID.py  
**Recomendación**: Siempre usar `sudo` al ejecutar
