# 📡 EXPLICACIÓN: Variables de Topics vs Strings

## ❓ Tu Pregunta Principal

**Pregunta 1:** En FaceID.py se publica con `TOPIC_RESPUESTA`, pero en script.js se pregunta por `'cerradura/persona'`. ¿Por qué se llaman diferente?

**Pregunta 2:** En FaceID.py se pregunta por `TOPIC_TIMBRE` pero en on_message se compara con `msg.topic`. ¿Cuál es la diferencia?

---

## 🎯 Respuesta Corta

**`TOPIC_RESPUESTA` y `'cerradura/persona'` son EXACTAMENTE LO MISMO.**

Solo que uno está guardado en una **variable** (en Python) y el otro es un **string literal** (en JavaScript).

---

## 📝 Desglose Detallado

### En FaceID.py (Servidor - Python)

```python
# LÍNEA 95: Definición de variables al inicio del archivo
TOPIC_REGISTRO = os.environ.get('TOPIC_REGISTRO', 'cerradura/registro')
TOPIC_TIMBRE = os.environ.get('TOPIC_TIMBRE', 'cerradura/timbre')
TOPIC_RESPUESTA = os.environ.get('TOPIC_RESPUESTA', 'cerradura/persona')
TOPIC_STATUS = os.environ.get('TOPIC_STATUS', 'cerradura/status')
TOPIC_CONFIRMACION = os.environ.get('TOPIC_CONFIRMACION', 'cerradura/confirmacion')

# ¿Qué significa?
# - Si existe una variable de entorno llamada 'TOPIC_RESPUESTA', úsala
# - Si NO existe, usa el valor por defecto: 'cerradura/persona'
```

**Entonces:**
```
TOPIC_RESPUESTA = 'cerradura/persona'
```

### Cuando publicas (FaceID.py línea 556)

```python
if min_dist < umbral:
    nombre = names[idx]
    porcentaje = int((1 - min_dist / umbral) * 100)
    print(f'[TIMBRE] Coincidencia: {nombre} ({porcentaje}% de coincidencia)')
    
    # Aquí se publica
    client.publish(TOPIC_RESPUESTA, json.dumps({
        'ok': True,
        'mensaje': 'Coincidencia encontrada',
        'coincidencia': True,
        'nombre': nombre,
        'distancia': min_dist,
        'porcentaje': porcentaje
    }))
```

**Lo que en realidad hace es:**
```python
# Sustituye TOPIC_RESPUESTA por su valor
client.publish('cerradura/persona', json.dumps({...}))
```

### En script.js (Cliente - JavaScript)

```javascript
// Línea 35: Se suscribe al topic
client.on('message', (topic, message) => {
    onMessage(topic, message);
});

function onMessage(topic, payload) {
    let msg = JSON.parse(payload.toString());
    
    // Línea 45: Se pregunta por el topic
    if (topic === 'cerradura/persona') {
        // Procesa si es 'cerradura/persona'
        if (msg.coincidencia) {
            setStatus(`✅ Coincidencia con ${msg.nombre}: ${msg.porcentaje}%`);
        }
    }
}
```

---

## 🔄 Diagrama Completo del Flujo

```
┌─────────────────────────────────────────────────────────────┐
│                    FaceID.py (Servidor)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  TOPIC_RESPUESTA = 'cerradura/persona'  ← Variable con valor│
│                                                               │
│  handle_timbre() detecta coincidencia                        │
│  ↓                                                            │
│  client.publish(TOPIC_RESPUESTA, json.dumps({...}))        │
│  ↓                                                            │
│  Sustituye variable:                                         │
│  client.publish('cerradura/persona', {...})                │
│  ↓                                                            │
│  Envía por MQTT al Broker                                   │
│                                                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ MQTT Broker
                         │ (Mosquitto)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    script.js (Cliente)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  client.subscribe('cerradura/persona')  ← Se suscribe      │
│  ↓                                                            │
│  Broker envía mensaje a script.js (porque está suscrito)    │
│  ↓                                                            │
│  onMessage(topic='cerradura/persona', message={...})        │
│  ↓                                                            │
│  if (topic === 'cerradura/persona') {  ← Verifica topic    │
│      Procesa el mensaje...                                  │
│  }                                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ❓ AHORA: ¿Por qué en un lado se usa variable y en otro string?

### Opción 1: Usar variables en AMBOS lados (Recomendado)

**FaceID.py** (ya lo hace así):
```python
TOPIC_RESPUESTA = 'cerradura/persona'
client.publish(TOPIC_RESPUESTA, json.dumps({...}))
```

**script.js** (PODRÍA hacerlo así):
```javascript
const TOPIC_RESPUESTA = 'cerradura/persona';

client.on('message', (topic, message) => {
    if (topic === TOPIC_RESPUESTA) {  // ← Usando variable
        // Procesar
    }
});
```

**Ventaja:** Si cambias el nombre del topic, cambias en UN lugar y funciona en ambos lados.

### Opción 2: Usar strings en AMBOS lados (Lo actual)

**FaceID.py:**
```python
client.publish('cerradura/persona', json.dumps({...}))
```

**script.js:**
```javascript
if (topic === 'cerradura/persona') {
    // Procesar
}
```

**Ventaja:** Simple, directo, no hay variables.

---

## 🔀 Segunda Pregunta: TOPIC_TIMBRE vs msg.topic

### En on_message() de FaceID.py (línea 594-605)

```python
def on_message(client, userdata, msg):
    print(f'[MQTT] Mensaje en topic {msg.topic}: {msg.payload}')
    try:
        if msg.topic == TOPIC_REGISTRO:               # ← Variable
            threading.Thread(target=handle_registro, args=(client, msg.payload)).start()
        elif msg.topic == TOPIC_TIMBRE:              # ← Variable
            threading.Thread(target=handle_timbre, args=(client,)).start()
        elif msg.topic == TOPIC_CONFIRMACION:        # ← Variable
            threading.Thread(target=handle_confirmacion, args=(client, msg.payload)).start()
```

**¿Qué es qué?**

```
msg.topic
├─ 'msg' = objeto que vino del MQTT Broker
├─ '.topic' = propiedad del objeto que contiene el nombre del topic
└─ Ejemplo: msg.topic = 'cerradura/timbre'

TOPIC_TIMBRE
└─ Variable que contiene: 'cerradura/timbre'

Comparación:
msg.topic == TOPIC_TIMBRE
'cerradura/timbre' == 'cerradura/timbre'  ✓ TRUE
```

---

## 📊 Tabla Comparativa

| Elemento | Tipo | Valor | Dónde | Cuándo |
|----------|------|-------|-------|--------|
| `TOPIC_RESPUESTA` | Variable Python | `'cerradura/persona'` | FaceID.py línea 97 | Definida al inicio |
| `TOPIC_TIMBRE` | Variable Python | `'cerradura/timbre'` | FaceID.py línea 95 | Definida al inicio |
| `msg.topic` | Propiedad del objeto | Varía según mensaje | En on_message() | Cuando llega mensaje MQTT |
| `'cerradura/persona'` | String literal | `'cerradura/persona'` | script.js línea 45 | Hardcodeado en código |
| `topic` parámetro | Parámetro función | Varía según mensaje | onMessage(topic, msg) | Cuando llega mensaje MQTT |

---

## 🔗 Flujo Completo: ¿Quién recibe qué?

### Escenario: Se presiona el botón físico

```
1️⃣  Botón físico presionado (GPIO 16)
    ↓
2️⃣  on_boton_presionado() se ejecuta
    ↓
3️⃣  iniciar_reconocimiento() se llama
    ↓
4️⃣  client.publish(TOPIC_TIMBRE, 'ping')
    ↓ (TOPIC_TIMBRE = 'cerradura/timbre')
    ↓
5️⃣  client.publish('cerradura/timbre', 'ping')
    ↓
6️⃣  Mensaje enviado al Broker MQTT
    ↓
7️⃣  Broker ve que TÚ (FaceID.py) estás suscrito a 'cerradura/timbre'
    ↓
8️⃣  Broker devuelve el mensaje a FaceID.py
    ↓
9️⃣  on_message(client, userdata, msg) se ejecuta
    ├─ msg.topic = 'cerradura/timbre'
    ├─ msg.payload = 'ping'
    ↓
🔟  if msg.topic == TOPIC_TIMBRE:
    ├─ 'cerradura/timbre' == 'cerradura/timbre' ✓ TRUE
    ├─ Crea hilo
    ├─ Llama handle_timbre(client)
    ↓
1️⃣1️⃣  handle_timbre() procesa reconocimiento facial
    ↓
1️⃣2️⃣  client.publish(TOPIC_RESPUESTA, json.dumps({...}))
    ↓ (TOPIC_RESPUESTA = 'cerradura/persona')
    ↓
1️⃣3️⃣  client.publish('cerradura/persona', json.dumps({...}))
    ↓
1️⃣4️⃣  Mensaje enviado al Broker MQTT
    ↓
1️⃣5️⃣  script.js en el navegador está suscrito a 'cerradura/persona'
    ↓
1️⃣6️⃣  onMessage('cerradura/persona', message) se ejecuta
    ↓
1️⃣7️⃣  if (topic === 'cerradura/persona') {
    ├─ 'cerradura/persona' === 'cerradura/persona' ✓ TRUE
    ├─ Parsea JSON
    ├─ Muestra: "✅ Coincidencia con Nacho: 83%"
```

---

## 💡 Analógía: El Sistema Postal

```
TOPIC_RESPUESTA = 'cerradura/persona'
    ↓
Es como tener una DIRECCIÓN GUARDADA en una variable:
    
mi_direccion = 'Calle Principal 123'

Cuando quieres enviar una carta:
    
enviar_carta(mi_direccion, contenido)
    ↓ (sustituye la variable)
enviar_carta('Calle Principal 123', contenido)
```

---

## ✅ Respuesta Final a tus Preguntas

### Pregunta 1: "¿Cómo recibe JS el mensaje si se publica con `TOPIC_RESPUESTA`?"

**Respuesta:**
- `TOPIC_RESPUESTA` es solo una variable que contiene `'cerradura/persona'`
- Se publica en el topic **`'cerradura/persona'`** (el valor)
- script.js se suscribe a **`'cerradura/persona'`** (mismo topic)
- El Broker automáticamente entrega el mensaje
- No importa si lo llamas `TOPIC_RESPUESTA` o `'cerradura/persona'`, el topic es **el mismo**

### Pregunta 2: "¿Por qué en `on_message()` se pregunta por `msg.topic == TOPIC_TIMBRE`?"

**Respuesta:**
- `msg.topic` es **lo que llegó del broker** (ej: `'cerradura/timbre'`)
- `TOPIC_TIMBRE` es **la variable con el mismo valor** (ej: `'cerradura/timbre'`)
- Se comparan los dos para verificar que el mensaje es del topic que esperamos
- Es **exactamente lo mismo** que escribir `msg.topic == 'cerradura/timbre'`, pero usando una variable

**Analogía:**
```
if msg.topic == TOPIC_TIMBRE:
    
Es lo mismo que:
    
if 'cerradura/timbre' == 'cerradura/timbre':
```

---

## 🎓 Punto Clave: Por qué usar variables?

### Mal (Hardcodeado):
```python
client.subscribe('cerradura/timbre')
client.subscribe('cerradura/registro')
client.subscribe('cerradura/confirmacion')

def on_message(client, userdata, msg):
    if msg.topic == 'cerradura/registro':  # ← String repetido
        handle_registro(...)
    elif msg.topic == 'cerradura/timbre':  # ← String repetido
        handle_timbre(...)
```

**Problema:** Si cambias el nombre del topic, debes cambiar en VARIOS lugares. Fácil cometer errores.

### Bien (Con variables):
```python
TOPIC_REGISTRO = 'cerradura/registro'
TOPIC_TIMBRE = 'cerradura/timbre'

client.subscribe(TOPIC_REGISTRO)
client.subscribe(TOPIC_TIMBRE)

def on_message(client, userdata, msg):
    if msg.topic == TOPIC_REGISTRO:  # ← Usa variable
        handle_registro(...)
    elif msg.topic == TOPIC_TIMBRE:  # ← Usa variable
        handle_timbre(...)
```

**Ventaja:** Cambias el valor en UN solo lugar (línea 95) y funciona en todas partes.

