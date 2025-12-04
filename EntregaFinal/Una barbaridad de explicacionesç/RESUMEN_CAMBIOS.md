# Resumen de Cambios Implementados

## 🎯 Objetivo
Integrar el botón físico, LED RGB y servomotor en el sistema FaceID, reemplazando la simulación anterior por control real de hardware con máquinas de estado para cada componente.

---

## ✅ Cambios Realizados

### 1. **FaceID.py** - Cambios Principales

#### Nuevas Importaciones
```python
import RPi.GPIO as GPIO
from enum import Enum
```

#### Nuevas Máquinas de Estado
```python
LEDState(Enum)           # Estados del LED
ServoState(Enum)         # Estados del servo
AppState(Enum)           # Estados de la aplicación
```

#### Nuevas Funciones Agregadas

| Función | Descripción |
|---------|-------------|
| `apagar_todos_leds()` | Apaga todos los LEDs |
| `set_led(rojo, verde, azul)` | Establece color específico |
| `cambiar_estado_led()` | Máquina de estados del LED |
| `_led_parpadeo()` | Thread para LED titilante |
| `set_servo_angle()` | Posiciona servo en ángulo |
| `abrir_puerta()` | Abre servo por 10 segundos |
| `cerrar_puerta()` | Cierra servo |
| `on_boton_presionado()` | Callback del botón |
| `setup_boton()` | Configura detección de botón |
| `cambiar_estado_app()` | Máquina de estados de app |
| `iniciar_reconocimiento()` | Inicia reconocimiento desde botón |
| `iniciar_registro()` | Inicia registro desde botón |
| `handle_confirmacion()` | Maneja respuesta web |
| `load_embeddings()` | Carga embeddings de BD |

#### Modificaciones a Funciones Existentes
- **`handle_registro()`**: Ahora espera presión de botón si no hay nombre
- **`handle_timbre()`**: Integrada máquina de estados
- **`on_connect()`**: Cambia a `ESPERANDO` y LED azul sólido
- **`on_message()`**: Agrega manejo de topic `cerradura/confirmacion`
- **`main_flask()`**: Inicializa GPIO, botón y servo al iniciar

#### Variables Globales Agregadas
```python
GPIO_INITIALIZED        # Flag de inicialización GPIO
current_app_state       # Estado actual de la app
current_led_state       # Estado actual del LED
current_servo_state     # Estado actual del servo
boton_presionado_flag   # Flag de presión de botón
registro_solicitado_flag# Flag de registro en espera
led_state_lock          # Lock para cambios de LED
app_state_lock          # Lock para cambios de app
last_recognized_person  # Almacena última persona reconocida
```

#### Nuevos Topics MQTT
```python
TOPIC_CONFIRMACION = 'cerradura/confirmacion'  # Confirmación de acceso
```

---

### 2. **script.js** - Cambios en Frontend

#### Cambios Principales
- **Removido**: Función `tocarTimbre()` - Ya no es necesaria
- **Removido**: Botón "Tocar timbre" del HTML
- **Agregado**: Flag `registroSolicitado` para track de registro
- **Mejorado**: Flujo de registro (espera botón físico)
- **Agregado**: Comentario informando que se usa botón físico

#### Nuevo Flujo de Registro
```javascript
// Antes: Click botón → Captura inmediata
// Ahora: Click botón → Marca flag → Espera botón físico → Captura
```

---

### 3. **index.html** - Cambios en Interfaz

#### HTML Modificado
- **Removido**: `<button id="ring-bell">` (ya no se necesita)
- **Agregado**: Bloque informativo azul con ℹ️
- **Texto mejorado**: "Presiona el botón físico en la puerta"
- **Emojis mejorados**: Botones ahora tienen emojis

#### Versión Script Actualizada
```html
<!-- Antes -->
<script src="script.js?v=4"></script>

<!-- Ahora -->
<script src="script.js?v=5"></script>
```

---

### 4. **style.css** - Sin cambios
- Se mantiene compatible con nuevas estructuras HTML

---

## 🔄 Flujos de Operación

### Flujo 1: Reconocimiento desde Botón Físico
```
Usuario presiona botón
    ↓
on_boton_presionado() callback
    ↓
iniciar_reconocimiento()
    ↓
[Estado: PROCESANDO_RECONOCIMIENTO]
[LED: AMARILLO SOLIDO]
    ↓
Captura foto + Compara embeddings
    ↓
[Estado: ESPERANDO_CONFIRMACION]
Envía JSON con resultado a web
    ↓
Usuario elige en web (Permitir/Denegar)
    ↓
handle_confirmacion()
    ↓
[LED: VERDE 10s O ROJO 10s]
[Servo: ABIERTO si permitir]
    ↓
[Estado: ESPERANDO]
[LED: AZUL SOLIDO]
```

### Flujo 2: Registro de Nuevo Rostro
```
Usuario click "Registrar nuevo rostro" + ingresa nombre
    ↓
handle_registro() con nombre
    ↓
[Estado: ESPERANDO_REGISTRO]
[LED: AZUL TITILANTE]
Publica "Presiona botón físico para registrar"
    ↓
Usuario presiona botón físico
    ↓
on_boton_presionado() → iniciar_registro()
    ↓
[Estado: REGISTRANDO]
[LED: AMARILLO SOLIDO durante captura]
    ↓
Captura foto + Genera embedding
    ↓
Guarda en embeddings.txt y names.txt
    ↓
[Estado: ESPERANDO]
[LED: AZUL SOLIDO]
```

---

## 📊 Tabla de Estados del LED

| Estado | Color | Comportamiento | Duración | Transición |
|--------|-------|----------------|----------|-----------|
| AMARILLO_TITILANTE | Amarillo | Parpadea 500ms | Indefinido | → AZUL_SOLIDO |
| AZUL_SOLIDO | Azul | Constante | Indefinido | → AMARILLO/VERDE/ROJO |
| AMARILLO_SOLIDO | Amarillo | Constante | Procesamiento | → AZUL_SOLIDO |
| VERDE_10S | Verde | Constante | 10 segundos | → AZUL_SOLIDO |
| ROJO_10S | Rojo | Constante | 10 segundos | → AZUL_SOLIDO |
| AZUL_TITILANTE | Azul | Parpadea 500ms | Registro | → AMARILLO_SOLIDO |

---

## 🔌 Configuración de Hardware

### Pines GPIO Utilizados
```
GPIO 17 → LED Rojo
GPIO 27 → LED Verde
GPIO 22 → LED Azul
GPIO 14 → Servo (PWM 50 Hz)
GPIO 21 → Botón (Pull-up, FALLING edge)
```

### Características de Cada Componente

**LED RGB (Cátodo Común)**
- HIGH = Enciende, LOW = Apaga
- Duty cycle: N/A (digital)
- Combinaciones para colores

**Servo**
- PWM 50 Hz
- Duty 5% = 0° (cerrado)
- Duty 7.5% = 90° (abierto)
- Tiempo movimiento: 0.5s

**Botón**
- Pull-up interno
- Debounce: 200ms
- Edge detection: FALLING
- Estado normal: HIGH

---

## 🧵 Threading y Sincronización

### Threads Utilizados
1. **MQTT Thread**: Loop de MQTT en hilo separado
2. **LED Blink Thread**: Parpadeo en hilo separado
3. **Handle Registro Thread**: Captura en hilo separado
4. **Handle Timbre Thread**: Reconocimiento en hilo separado
5. **Handle Confirmación Thread**: Confirmación en hilo separado
6. **Servo Timer Threads**: Timers para cierre automático

### Locks Implementados
```python
led_state_lock       # Protege cambios de estado LED
app_state_lock       # Protege cambios de estado app
last_image_lock      # Protege acceso a última imagen (existente)
```

---

## 📡 Topics MQTT (Resumen)

### Subscribe (Recibe Raspberry Pi)
```
cerradura/registro       → {"nombre": "..."}
cerradura/timbre         → "ping"
cerradura/confirmacion   → {"permitir": true/false}
```

### Publish (Envía Raspberry Pi)
```
cerradura/status   → "Estado del sistema"
cerradura/persona  → {"coincidencia": true/false, "nombre": "...", "distancia": 0.xxx}
```

---

## 🎨 Máquina de Estados Visual

```
INICIALIZANDO
     │
     ├─[MQTT OK]─→ ESPERANDO ←──┐
     │                │           │
     │                ├─[Botón]──→ PROCESANDO_RECONOCIMIENTO
     │                │           │
     │                │           └─→ ESPERANDO_CONFIRMACION
     │                │                 ├─[Permitir]─→ SERVO:ABIERTO
     │                │                 └─[Denegar]─→ SERVO:CERRADO
     │                │                 │
     │                │                 └─→ ESPERANDO
     │                │
     │                └─[Registro+Botón]→ REGISTRANDO
     │                                     │
     │                                     └─→ ESPERANDO
     │
     └─[MQTT Falla]→ LED:AMARILLO_TITILANTE
```

---

## 🔐 Seguridad Agregada

1. **Máquinas de estado**: Previene acciones no permitidas
2. **Locks**: Evita race conditions
3. **Validación de payload MQTT**: Verifica JSON
4. **Edge detection con debounce**: Evita rebotes del botón
5. **Timeouts en operaciones críticas**: Auto-cierre de puerta

---

## 📊 Diagrama de Componentes

```
┌─────────────────────────────────────────────┐
│         Raspberry Pi 3                      │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │        FaceID.py                     │  │
│  │  ┌──────────────────────────────┐   │  │
│  │  │ Máquina de Estados (App)     │   │  │
│  │  │ Máquina de Estados (LED)     │   │  │
│  │  │ Máquina de Estados (Servo)   │   │  │
│  │  └──────────────────────────────┘   │  │
│  │              │                        │  │
│  │     ┌────────┼────────┐              │  │
│  │     ▼        ▼        ▼              │  │
│  │   GPIO   MQTT    Flask              │  │
│  └─────┬────┬─────┬──────────────────┘  │
│        │    │     │                     │
└────────┼────┼─────┼──────────────────────┘
         │    │     │
    ┌────▼─┐ │     ▼
    │ GPIO │ │   :5000
    └────┬─┘ │
    ┌────▼───┼───────────┐
    │        ▼           │
   LED   SERVO  BOTON   CAM
   RGB             R.PI
    ↓       ↓      ↓
  RGB LED  Puerta  Button  Camera
```

---

## ✨ Mejoras Implementadas

### Funcionalidad
- ✅ Botón físico reemplaza simulación
- ✅ LED RGB con máquina de estados completa
- ✅ Servo con apertura/cierre automático
- ✅ Sistema de confirmación de acceso desde web
- ✅ Registro de rostros desde botón físico

### Robustez
- ✅ Thread-safety con locks
- ✅ Máquinas de estado evitan inconsistencias
- ✅ Debounce en botón (200ms)
- ✅ PWM detenido después de movimientos servo
- ✅ Manejo de excepciones en inicialización GPIO

### Usabilidad
- ✅ Logs claros con prefijos [LED], [SERVO], [BOTON], etc.
- ✅ Interfaz web simplificada
- ✅ Documentación completa en 4 archivos
- ✅ Guía de instalación paso a paso

### Rendimiento
- ✅ LED parpadeo en thread separado
- ✅ MQTT en thread separado
- ✅ Timers para operaciones no bloqueantes
- ✅ Procesamiento de imágenes en threads

---

## 📚 Documentación Generada

| Archivo | Contenido |
|---------|----------|
| `README_ACTUALIZACIONES.md` | Resumen cambios y flujos |
| `DIAGRAMAS_ESTADOS.md` | Diagramas ASCII de máquinas de estado |
| `GUIA_INSTALACION_RPI.md` | Pasos completos instalación |
| `REFERENCIA_RAPIDA.md` | Referencia técnica y pines |

---

## 🚀 Próximas Mejoras Sugeridas

1. **Timeout de inactividad**: Volver a ESPERANDO si no hay confirmación en 30s
2. **Registro de eventos**: Base de datos con intentos/accesos
3. **Notificaciones**: Email/SMS en acceso permitido/denegado
4. **Multi-usuario**: Verificación dual (biométrica + PIN)
5. **Histórico**: Panel admin para ver intentos fallidos
6. **Calibración LED**: Ajustar brillo según luz ambiente
7. **Actualizaciones OTA**: Actualizar código remotamente
8. **Modo de prueba**: Desabilitar servo para testing

---

## 📞 Soporte Técnico

Para problemas específicos, ver:
- **Instalación**: `GUIA_INSTALACION_RPI.md`
- **Configuración**: `REFERENCIA_RAPIDA.md`
- **Diseño**: `DIAGRAMAS_ESTADOS.md`
- **Uso**: `README_ACTUALIZACIONES.md`

---

**Versión**: 1.0  
**Fecha**: Diciembre 2025  
**Autor**: Actualización Integración Hardware  
**Estado**: ✅ Implementado y documentado
