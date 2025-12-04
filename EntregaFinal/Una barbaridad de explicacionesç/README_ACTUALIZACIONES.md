# Actualización FaceID - Integración Botón, LED y Servo

## 📋 Cambios Implementados

### 1. **Integración del Botón Físico**
- Reemplaza la simulación anterior del botón
- El botón físico (GPIO 21) ahora controla directamente el reconocimiento
- Presión única: inicia reconocimiento (timbre)
- Con registro solicitado desde web: inicia captura para nuevo registro

### 2. **Control de LED RGB (Cátodo Común)**
Pins: Rojo (GPIO 17), Verde (GPIO 27), Azul (GPIO 22)

#### Estados del LED:
- **🟡 AMARILLO TITILANTE** (startup):
  - Al iniciar el programa hasta que se conecte con el broker MQTT
  
- **🔵 AZUL SOLIDO** (listo):
  - Sistema listo y esperando eventos
  
- **🟡 AMARILLO SOLIDO** (procesando):
  - Mientras se procesa el reconocimiento facial (después de presionar botón)
  
- **✅ VERDE 10 segundos** (acceso permitido):
  - Se abre la puerta por 10 segundos
  - Vuelve a azul después
  
- **❌ ROJO 10 segundos** (acceso denegado):
  - Se muestra rechazo de acceso
  - Vuelve a azul después
  
- **🔵 AZUL TITILANTE** (registrando):
  - Mientras se captura un nuevo rostro para registro

### 3. **Control de Servomotor**
Pin: GPIO 14 (PWM a 50 Hz)

#### Comportamiento:
- **Inicio**: Posición cerrada (0°)
- **Acceso permitido desde web**: Se abre (90°) por 10 segundos
- **Después de 10 segundos**: Se cierra automáticamente (0°)

### 4. **Máquina de Estados de la Aplicación**
```
INICIALIZANDO → ESPERANDO 
              ↓         ↓
       PROCESANDO   ESPERANDO
       RECONOCIMIENTO REGISTRO
              ↓         ↓
       ESPERANDO     REGISTRANDO
       CONFIRMACION       ↓
              ↓ (confirmación web)
       ESPERANDO
```

### 5. **Flujo de Operación**

#### 🔔 Timbre (Reconocimiento):
1. Usuario presiona botón físico
2. LED → 🟡 AMARILLO SOLIDO
3. Sistema captura foto y compara con embeddings
4. Envía resultado a web
5. Sistema espera confirmación web

#### ✅ Confirmación Permitir:
1. Usuario hace clic en web "Permitir acceso"
2. LED → 🟢 VERDE 10s
3. Servo abre puerta (90°)
4. Después de 10s: Servo cierra (0°), LED → 🔵 AZUL

#### ❌ Confirmación Denegar:
1. Usuario hace clic en web "Denegar acceso"
2. LED → 🔴 ROJO 10s
3. Servo permanece cerrado
4. Después de 10s: LED → 🔵 AZUL

#### 📸 Registro de Nuevo Rostro:
1. Usuario hace clic en web "Registrar nuevo rostro" + ingresa nombre
2. Sistema espera presión de botón físico
3. LED → 🔵 AZUL TITILANTE
4. Usuario presiona botón
5. Sistema captura foto e ingresa en base de datos
6. LED → 🔵 AZUL SOLIDO
7. Vuelve a estado ESPERANDO

### 6. **Nuevos Topics MQTT**
- `cerradura/confirmacion`: Recibe confirmación de acceso (`{permitir: true/false}`)

### 7. **Cambios en el Umbral**
- Se cambió el umbral de distancia a **0.8** (antes era 1.0)
- Esto significa que solo acepta coincidencias más cercanas

## 🔧 Requisitos de Hardware

```
Raspberry Pi 3
├── LED RGB (Cátodo Común)
│   ├── Rojo → GPIO 17
│   ├── Verde → GPIO 27
│   └── Azul → GPIO 22
│
├── Servomotor
│   ├── Señal → GPIO 14 (PWM)
│   ├── 5V → 5V Rpi
│   └── GND → GND
│
├── Botón
│   ├── GPIO 21
│   └── GND (otra pata)
│
└── Cámara (PiCamera)
```

## 📦 Instalación de Dependencias

```bash
pip install opencv-python
pip install mtcnn
pip install keras-facenet
pip install numpy
pip install pillow
pip install paho-mqtt
pip install flask
pip install flask-cors
pip install RPi.GPIO
pip install gpiozero
```

## 🚀 Ejecución

```bash
# En la Raspberry Pi
python3 FaceID.py
```

## 📝 Variables de Entorno Opcionales

```bash
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export TOPIC_REGISTRO=cerradura/registro
export TOPIC_TIMBRE=cerradura/timbre
export TOPIC_RESPUESTA=cerradura/persona
export TOPIC_STATUS=cerradura/status
export TOPIC_CONFIRMACION=cerradura/confirmacion
```

## 🐛 Notas Importantes

1. **GPIO Initialization**: El código verifica si la inicialización de GPIO fue exitosa. Si no, continúa sin control de hardware (útil para testing en PC).

2. **Thread Safety**: Se utilizan locks para evitar race conditions en:
   - Cambios de estado del LED
   - Cambios de estado de la aplicación
   - Acceso a la última imagen capturada

3. **Limpieza de GPIO**: Se realiza al presionar Ctrl+C o salir del programa.

4. **Debounce del botón**: Se configura con 200ms para evitar lecturas falsas.

5. **PWM del servo**: Se detiene después de cada movimiento para evitar vibraciones.

6. **Parpadeo del LED**: Se ejecuta en hilo separado y se detiene cuando cambia de estado.

## 🔄 Máquina de Estados del LED (Detallada)

### Transiciones Permitidas:
```
AMARILLO_TITILANTE → AZUL_SOLIDO (conexión MQTT)
AZUL_SOLIDO → AMARILLO_SOLIDO (botón presionado)
AMARILLO_SOLIDO → AZUL_SOLIDO (reconocimiento completado)
AZUL_SOLIDO → VERDE_10S (acceso permitido desde web)
VERDE_10S → AZUL_SOLIDO (después de 10 segundos)
AZUL_SOLIDO → ROJO_10S (acceso denegado desde web)
ROJO_10S → AZUL_SOLIDO (después de 10 segundos)
AZUL_SOLIDO → AZUL_TITILANTE (registro solicitado desde web)
AZUL_TITILANTE → AMARILLO_SOLIDO (botón presionado durante registro)
AMARILLO_SOLIDO → AZUL_SOLIDO (registro completado)
```

## 📊 Logs de Consola

El sistema imprime logs con prefijos para fácil identificación:
- `[LED]` - Cambios de estado del LED
- `[SERVO]` - Movimientos del servo
- `[BOTON]` - Eventos del botón
- `[APP STATE]` - Cambios de estado de la aplicación
- `[MQTT]` - Eventos de MQTT
- `[TIMBRE]` - Eventos de reconocimiento
- `[REGISTRO]` - Eventos de registro
- `[CONFIRMACION]` - Eventos de confirmación desde web
