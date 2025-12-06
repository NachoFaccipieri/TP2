# Máquina de Estados - Sistema FaceID

## Estados Principales (AppState)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA FACEID DOOR                          │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  INICIALIZANDO   │ ← Estado inicial al arrancar
    │   (LED Amarillo  │
    │    titilante)    │
    └────────┬─────────┘
             │ MQTT conecta
             ↓
    ┌──────────────────┐
    │   ESPERANDO      │ ← Estado de reposo
    │ (LED Azul solido)│
    └────┬─────────────┘
         │
         ├─ Presionar botón físico → PROCESANDO_RECONOCIMIENTO
         │
         └─ Web solicita registro → ESPERANDO_REGISTRO


    ┌──────────────────────────────┐
    │ PROCESANDO_RECONOCIMIENTO    │ ← Capturando y analizando
    │  (LED Amarillo solido)       │
    └────────┬─────────────────────┘
             │ Análisis completado
             ↓
    ┌──────────────────────────────┐
    │  ESPERANDO_CONFIRMACION      │ ← Esperando decisión
    │  (LED Amarillo o Azul según  │
    │   coincidencia)              │
    └────┬────────────────────┬────┘
         │                    │
    Permitir ✅          Denegar ❌
         │                    │
         ↓                    ↓
    ┌─────────────┐    ┌─────────────┐
    │ VERDE 10S   │    │  ROJO 10S   │
    │ (servo abre)│    │ (puerta no  │
    │             │    │  abre)      │
    └────┬────────┘    └────┬────────┘
         │ 10 segundos      │ 10 segundos
         └─────┬────────────┘
               ↓
         ┌──────────────┐
         │  ESPERANDO   │
         └──────────────┘


    ┌──────────────────────────────┐
    │   ESPERANDO_REGISTRO         │ ← Web solicita registro
    │    (LED Azul titilante)      │
    └────────┬─────────────────────┘
             │ Presionar botón físico
             ↓
    ┌──────────────────────────────┐
    │     REGISTRANDO              │ ← Capturando rostro
    │    (LED Azul titilante)      │
    └────────┬─────────────────────┘
             │ Rostro capturado y guardado
             ↓
         ┌──────────────┐
         │  ESPERANDO   │
         └──────────────┘
```

---

## Estados de LED (LEDState)

| Estado | Color | Significado | Duración |
|--------|-------|-------------|----------|
| `AZUL_SOLIDO` | 🔵 Azul fijo | Sistema listo, esperando | Indefinido |
| `AMARILLO_TITILANTE` | 🟡 Amarillo parpadeante | Inicializando o registrando | Mientras dure la acción |
| `AMARILLO_SOLIDO` | 🟡 Amarillo fijo | Reconocimiento coincidió, esperando confirmación | Hasta confirmación |
| `AZUL_TITILANTE` | 🔵 Azul parpadeante | Reconocimiento NO coincidió, esperando decisión manual | Hasta decisión |
| `VERDE_10S` | 🟢 Verde fijo | Acceso PERMITIDO, puerta abierta | 10 segundos |
| `ROJO_10S` | 🔴 Rojo fijo | Acceso DENEGADO | 10 segundos |

---

## Estados del Servo (ServoState)

| Estado | Ángulo | Significado |
|--------|--------|-------------|
| `CERRADO` | 0° | Puerta cerrada (posición inicial) |
| `ABIERTO` | 180° | Puerta abierta (acceso permitido) |

---

## Flujos de Transición Detallados

### 🎯 Flujo 1: Reconocimiento con Coincidencia

```
ESPERANDO
    ↓ [Presionar botón físico]
PROCESANDO_RECONOCIMIENTO (captura imagen)
    ↓ [Imagen procesada, facial reconocido]
ESPERANDO_CONFIRMACION
    ├─ LED: AMARILLO_SOLIDO (coincidencia encontrada)
    ├─ Web muestra: "✅ Coincidencia: Juan (distancia 0.45)"
    │
    ├─ Usuario: Presiona "✅ Permitir" en web
    │   ↓
    │   ESPERANDO ← [LED: VERDE_10S, servo abre 10s]
    │
    └─ Usuario: Presiona "❌ Denegar" en web
        ↓
        ESPERANDO ← [LED: ROJO_10S, servo no abre]
```

---

### 🎯 Flujo 2: Reconocimiento sin Coincidencia

```
ESPERANDO
    ↓ [Presionar botón físico]
PROCESANDO_RECONOCIMIENTO (captura imagen)
    ↓ [Imagen procesada, NO hay coincidencia]
ESPERANDO_CONFIRMACION
    ├─ LED: AZUL_TITILANTE (sin coincidencia, espera decisión)
    ├─ Web muestra: "❌ No se encontró coincidencia (distancia 1.2)"
    │
    ├─ Usuario: Presiona "✅ Permitir" de todas formas
    │   ↓
    │   ESPERANDO ← [LED: VERDE_10S, servo abre 10s]
    │
    └─ Usuario: Presiona "❌ Denegar"
        ↓
        ESPERANDO ← [LED: ROJO_10S, servo no abre]
```

---

### 🎯 Flujo 3: Registro de Nuevo Rostro

```
ESPERANDO
    ↓ [Usuario presiona "Registrar" en web, ingresa nombre]
ESPERANDO_REGISTRO
    ├─ LED: AZUL_TITILANTE
    ├─ Web muestra: "Esperando... Presiona el botón físico para registrar a 'Juan'"
    │
    ├─ [Usuario presiona botón físico en puerta]
    │
    REGISTRANDO
    ├─ LED: AZUL_TITILANTE
    ├─ Captura imagen
    ├─ Detecta rostro
    ├─ Genera embedding
    ├─ Guarda en embeddings.txt
    │
    └─ ESPERANDO ← [LED: AZUL_SOLIDO, Web muestra confirmación]
```

---

## Código de Estados (Python Enum)

```python
class AppState(Enum):
    INICIALIZANDO = 0                    # Startup
    ESPERANDO = 1                        # Listo, esperando
    PROCESANDO_RECONOCIMIENTO = 2        # Capturando y analizando
    ESPERANDO_CONFIRMACION = 3           # Esperando decisión web
    ESPERANDO_REGISTRO = 4               # Esperando presión botón para registrar
    REGISTRANDO = 5                      # Capturando rostro para registro

class LEDState(Enum):
    AMARILLO_TITILANTE = 1               # Startup/registrando
    AZUL_SOLIDO = 2                      # Listo
    VERDE_10S = 3                        # Acceso permitido (10s)
    ROJO_10S = 4                         # Acceso denegado (10s)
    AMARILLO_SOLIDO = 5                  # Coincidencia, esperando confirmación
    AZUL_TITILANTE = 6                   # Sin coincidencia, esperando decisión

class ServoState(Enum):
    CERRADO = 0                          # 0 grados
    ABIERTO = 1                          # 180 grados
```

---

## Transiciones por Evento

### Eventos de Botón Físico

| Evento | Estado Actual | Acción | Nuevo Estado |
|--------|---------------|--------|--------------|
| Presionar | `ESPERANDO` | Iniciar reconocimiento | `PROCESANDO_RECONOCIMIENTO` |
| Presionar | `ESPERANDO_REGISTRO` | Capturar para registro | `REGISTRANDO` |
| Presionar | Otros | Ignorar | (sin cambio) |

### Eventos de MQTT (Web)

| Evento | Estado Actual | Acción | Nuevo Estado |
|--------|---------------|--------|--------------|
| Registrar solicitado | `ESPERANDO` | Esperar botón | `ESPERANDO_REGISTRO` |
| Permitir acceso | `ESPERANDO_CONFIRMACION` | Abrir puerta 10s | `ESPERANDO` |
| Denegar acceso | `ESPERANDO_CONFIRMACION` | Rechazar | `ESPERANDO` |

### Eventos de Timers (Automáticos)

| Evento | Estado Actual | Acción | Nuevo Estado |
|--------|---------------|--------|--------------|
| 10s transcurridos (VERDE) | Cualquiera | Cerrar puerta | `ESPERANDO` |
| 10s transcurridos (ROJO) | Cualquiera | Volver a reposo | `ESPERANDO` |

---

## Sincronización de Estados

```python
# Locks para evitar race conditions
led_state_lock = threading.Lock()          # Protege cambios de LED
app_state_lock = threading.Lock()          # Protege cambios de estado app

# Cambiar estado es thread-safe
def cambiar_estado_app(nuevo_estado):
    global current_app_state
    with app_state_lock:
        if current_app_state != nuevo_estado:
            print(f"[APP STATE] {current_app_state.name} -> {nuevo_estado.name}")
            current_app_state = nuevo_estado
```

---

## Secuencia Temporal Ejemplo: Usuario autorizado

```
Tiempo  Evento                    AppState                LEDState            Acción
────────────────────────────────────────────────────────────────────────────────────
T+0s    Presionar botón          ESPERANDO          →    AMARILLO_SOLIDO   
                                                    PROCESANDO_REC       
                                 
T+1s    Imagen capturada         PROCESANDO_REC     →    AMARILLO_SOLIDO   [capturando]
        Rostro detectado         
        Embedding generado       
        
T+2s    Coincidencia encontrada  ESPERANDO_CONF     →    AMARILLO_SOLIDO   [esperando web]
        (distancia 0.45 < 0.8)   
        
T+3s    Usuario web: Permitir    ESPERANDO_CONF     →    VERDE_10S         [servo abre]
        
T+4s    Puerta abierta           (durante VERDE)         VERDE_10S         [servo 180°]
        
T+13s   10 segundos transcurren  VERDE_10S          →    AZUL_SOLIDO       [cierra puerta]
                                 ESPERANDO                                  [servo 0°]
        
T+14s   Sistema listo            ESPERANDO               AZUL_SOLIDO       ✅
```

---

## Notas Importantes

1. **Thread-Safety**: Todos los cambios de estado están protegidos con locks
2. **Timers**: Los timers de 10 segundos se programan como `threading.Timer()`
3. **LEDs**: Se controlan automáticamente al cambiar `AppState`
4. **Botón**: Solo funciona en ciertos estados (ESPERANDO, ESPERANDO_REGISTRO)
5. **Servo**: Se abre automáticamente solo si acceso es PERMITIDO
6. **LED Amarillo vs Azul Titilante**: 
   - Amarillo = Coincidencia encontrada, esperando confirmación
   - Azul titilante = Sin coincidencia, usuario debe decidir manualmente
