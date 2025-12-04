# Referencia Rápida de Pines y Configuración

## 🔌 Asignación de Pines GPIO

| Componente | Pin GPIO | Tipo | Estado Inicial | Notas |
|-----------|----------|------|----------------|-------|
| LED Rojo | 17 | OUTPUT | LOW | Cátodo Común (HIGH = Enciende) |
| LED Verde | 27 | OUTPUT | LOW | Cátodo Común (HIGH = Enciende) |
| LED Azul | 22 | OUTPUT | LOW | Cátodo Común (HIGH = Enciende) |
| Servo | 14 | PWM (50 Hz) | 0° | Duty: 5% = 0°, 7.5% = 90° |
| Botón | 21 | INPUT | PULL-UP | Edge Detection (FALLING) |

## 🎨 Combinaciones de LED RGB

```
Rojo (R) | Verde (G) | Azul (B) | Color
---------|----------|----------|----------
  H      |    L     |    L     | ROJO
  L      |    H     |    L     | VERDE
  L      |    L     |    H     | AZUL
  H      |    H     |    L     | AMARILLO (Rojo + Verde)
  H      |    L     |    H     | MAGENTA (Rojo + Azul)
  L      |    H     |    H     | CIÁN (Verde + Azul)
  H      |    H     |    H     | BLANCO
  L      |    L     |    L     | APAGADO

H = HIGH (encendido)
L = LOW (apagado)
```

## 📡 Especificaciones del Servo

| Parámetro | Valor |
|-----------|-------|
| Frecuencia PWM | 50 Hz |
| Período | 20 ms |
| Duty Cycle mínimo | 5% (1 ms) |
| Duty Cycle máximo | 10% (2 ms) |
| Rango de movimiento | 0° a 180° |
| Tiempo de movimiento | ~0.5 segundos |

### Cálculo de Duty Cycle para Ángulo
```
duty = 5 + (angle / 180) * 5

Ejemplos:
- 0°   → duty = 5%
- 45°  → duty = 6.25%
- 90°  → duty = 7.5%
- 135° → duty = 8.75%
- 180° → duty = 10%
```

## 🔘 Especificaciones del Botón

| Parámetro | Valor |
|-----------|-------|
| Pin GPIO | 21 |
| Pull-up | Interno |
| Debounce | 200 ms |
| Edge Detection | FALLING (presión = 0) |
| Normal State | HIGH (sin presionar) |

## 📲 Topics MQTT

| Topic | Dirección | Payload | Descripción |
|-------|-----------|---------|-------------|
| cerradura/status | Publish | String | Estado general del sistema |
| cerradura/persona | Publish | JSON | Resultado de reconocimiento |
| cerradura/registro | Subscribe | JSON | Solicitud de registro {nombre: "..."} |
| cerradura/timbre | Subscribe | String | Comando para iniciar reconocimiento |
| cerradura/confirmacion | Subscribe | JSON | Confirmación de acceso {permitir: true/false} |

### Payload JSON Esperado

**cerradura/persona (Publish):**
```json
{
  "ok": true,
  "coincidencia": true,
  "nombre": "Nacho",
  "distancia": 0.456,
  "mensaje": "Coincidencia encontrada"
}
```

**cerradura/confirmacion (Subscribe):**
```json
{
  "permitir": true
}
// o
{
  "permitir": false
}
```

## 🔌 Conexiones de Hardware

### LED RGB (Cátodo Común)
```
   ┌─────────────────────┐
   │   LED RGB Cátodo    │
   │     Común           │
   └──┬────┬────┬────┬───┘
      │    │    │    │
      │    │    │    └─────► GND (Pin 6 o 9 de Rpi)
      │    │    └──────────► GPIO 22 (Azul)
      │    └───────────────► GPIO 27 (Verde)
      └────────────────────► GPIO 17 (Rojo)

Nota: Cátodo Común = pin largo a GND, patas cortas a GPIO
```

### Servo Motor
```
   ┌──────────────┐
   │   SERVO      │
   └──┬──┬───┬────┘
      │  │   │
      │  │   └────► GPIO 14 (PWM - Señal)
      │  └────────► +5V (Alimentación)
      └──────────► GND (Tierra)

Nota: El servo requiere 5V desde fuente externa en Pi
```

### Botón
```
   ┌──────────────┐
   │   BOTÓN      │
   └──┬───────┬───┘
      │       │
      │       └────► GPIO 21
      └────────────► GND (Pin 6 o 9)

Nota: Con pull-up interno, presión = LOW
```

## 📊 Estados de la Aplicación

```python
class AppState(Enum):
    INICIALIZANDO = 0
    ESPERANDO = 1
    PROCESANDO_RECONOCIMIENTO = 2
    ESPERANDO_CONFIRMACION = 3
    ESPERANDO_REGISTRO = 4
    REGISTRANDO = 5
```

## 💡 Estados del LED

```python
class LEDState(Enum):
    AMARILLO_TITILANTE = 1  # Startup
    AZUL_SOLIDO = 2         # Listo
    VERDE_10S = 3           # Acceso permitido
    ROJO_10S = 4            # Acceso denegado
    AMARILLO_SOLIDO = 5     # Procesando
    AZUL_TITILANTE = 6      # Registrando
```

## 🚪 Estados del Servo

```python
class ServoState(Enum):
    CERRADO = 0  # 0°
    ABIERTO = 1  # 90°
```

## 🌐 URLs y Puertos

| Servicio | Puerto | URL | Notas |
|----------|--------|-----|-------|
| Flask Web | 5000 | http://localhost:5000 | Interfaz web |
| MQTT | 1883 | mqtt://localhost:1883 | Protocolo MQTT |
| MQTT WebSocket | 9001 | ws://localhost:9001 | Para navegadores |

## 📁 Archivos de Base de Datos

| Archivo | Ubicación | Contenido | Formato |
|---------|-----------|-----------|---------|
| embeddings.txt | APP_ROOT | Vectores de embeddings | JSON (1 por línea) |
| names.txt | APP_ROOT | Nombres de personas | Texto (1 por línea) |

### Ejemplo embeddings.txt
```json
[-0.123, 0.456, -0.789, ..., 0.234]
[-0.234, 0.567, -0.890, ..., 0.345]
```

### Ejemplo names.txt
```
Nacho
Mati
```

## ⚙️ Parámetros Configurables

| Parámetro | Valor Por Defecto | Ubicación | Notas |
|-----------|-------------------|-----------|-------|
| MQTT_BROKER | localhost | FaceID.py | IP o hostname del broker |
| MQTT_PORT | 1883 | FaceID.py | Puerto MQTT |
| FLASK_HOST | 0.0.0.0 | FaceID.py | Interfaz de escucha |
| FLASK_PORT | 5000 | FaceID.py | Puerto del servidor web |
| Umbral distancia | 0.8 | handle_timbre() | Menor = más estricto |
| Botón debounce | 200 ms | setup_boton() | Tiempo para descartar rebotes |
| LED parpadeo | 500 ms | _led_parpadeo() | Intervalo de parpadeo |
| Servo tiempo | 10 s | abrir_puerta() | Tiempo de apertura |
| Timeout timbre | 30 s | Impl. futura | Tiempo espera confirmación |

## 🔐 Configuración de Seguridad

**Credenciales MQTT (index.html):**
```javascript
window.MQTT_CONFIG = {
  username: 'mi_usuario',
  password: 'mi_contraseña'
};
```

**Variables de entorno (.bashrc o .env):**
```bash
export MQTT_BROKER=192.168.1.100
export MQTT_PORT=1883
export FLASK_PORT=5000
```

## 📝 Umbral de Reconocimiento

| Umbral | Distancia | Reconocimiento | Uso |
|--------|-----------|----------------|-----|
| < 0.6 | Muy cerrada | Muy restrictivo | Seguridad máxima |
| 0.7 | Cerrada | Restrictivo | Recomendado |
| 0.8 | **Actual** | Moderado | Equilibrio |
| 0.9 | Abierta | Permisivo | Poco restrictivo |
| 1.0 | Muy abierta | Muy permisivo | No recomendado |

## 🎯 Checklist de Configuración

- [ ] GPIO configurados correctamente
- [ ] LED RGB conectado y testeado
- [ ] Servo conectado a alimentación 5V externa
- [ ] Botón conectado con pull-up
- [ ] Cámara PiCamera habilitada
- [ ] Mosquitto instalado y corriendo
- [ ] MQTT WebSocket habilitado (puerto 9001)
- [ ] Python 3.7+ instalado
- [ ] Dependencias instaladas (pip)
- [ ] Base de datos inicializada (embeddings.txt vacío ok)
- [ ] FaceID.py modificado con configuración local
- [ ] Firewall permite puertos 5000, 1883, 9001
- [ ] Servicio systemd configurado (opcional)

## 🧪 Comandos de Prueba

```bash
# Test GPIO - LED Rojo
gpio -g mode 17 out && gpio -g write 17 1 && sleep 1 && gpio -g write 17 0

# Test MQTT conexión
mosquitto_pub -h localhost -t "test" -m "test"

# Test Flask
curl http://localhost:5000/

# Test Cámara
raspistill -o test.jpg -t 1000

# Ver estado de servicios
systemctl status mosquitto
sudo systemctl status faceid

# Ver logs en tiempo real
sudo journalctl -u faceid -f

# Test GPIO (Python)
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('GPIO OK')"
```

## 📞 Soporte

Para issues comunes, ver **GUIA_INSTALACION_RPI.md** sección "Solución de Problemas"
