# 🌊 FLUJO MQTT COMPLETO - GUÍA DETALLADA

## 📋 Resumen Rápido

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO TOTAL DEL SISTEMA                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1️⃣  Botón Físico Presionado                                        │
│      ↓                                                               │
│  2️⃣  gpiozero.Button llama on_boton_presionado()                   │
│      ↓                                                               │
│  3️⃣  on_boton_presionado() → iniciar_reconocimiento()             │
│      ↓                                                               │
│  4️⃣  iniciar_reconocimiento() publica en TOPIC_TIMBRE             │
│      ↓                                                               │
│  5️⃣  MQTT Broker recibe el publish                                 │
│      ↓                                                               │
│  6️⃣  on_message() es LLAMADA AUTOMÁTICAMENTE por el broker       │
│      ↓                                                               │
│  7️⃣  on_message() ve que el topic es TOPIC_TIMBRE                │
│      ↓                                                               │
│  8️⃣  on_message() crea hilo y llama handle_timbre()              │
│      ↓                                                               │
│  9️⃣  handle_timbre() procesa reconocimiento facial                │
│      ↓                                                               │
│  🔟 handle_timbre() publica respuesta en TOPIC_RESPUESTA           │
│      ↓                                                               │
│  1️⃣1️⃣ script.js recibe la respuesta y actualiza la web            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FASE 1: Botón Presionado (Genera el evento)

```python
# gpiozero detecta presión automáticamente
Button(PIN_BOTON)  # Línea 16
boton_gpiozero.when_pressed = on_boton_presionado  # Callback automático
```

**¿Qué sucede?**
- El botón físico se presiona
- gpiozero detecta el evento (sin necesidad de polls)
- **Automáticamente** llama a `on_boton_presionado()`

```python
# FaceID.py línea 317-330
def on_boton_presionado():
    """Callback cuando se presiona el botón (gpiozero)"""
    print("[BOTON] ✅ Botón presionado")
    
    with app_state_lock:
        estado_actual = current_app_state
    
    # Lógica según el estado actual
    if estado_actual == AppState.ESPERANDO:
        # ⬇️ AQUÍ: Llama función de reconocimiento
        print("[BOTON] → Iniciando reconocimiento...")
        iniciar_reconocimiento()
    
    elif estado_actual == AppState.ESPERANDO_REGISTRO:
        # Inicia registro
        print("[BOTON] → Iniciando registro...")
        iniciar_registro()
```

---

## 🎯 FASE 2: iniciar_reconocimiento() (Inicia el flujo)

```python
# FaceID.py línea 428-436
def iniciar_reconocimiento():
    """Inicia el proceso de reconocimiento desde el botón físico"""
    global mqtt_client
    
    cambiar_estado_app(AppState.PROCESANDO_RECONOCIMIENTO)
    cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
    
    if mqtt_client:
        mqtt_client.publish(TOPIC_TIMBRE, 'ping')  # ⬅️ PUBLISH AQUI
```

**¿Qué pasa aquí?**

1. Actualiza estado: `AppState.PROCESANDO_RECONOCIMIENTO`
2. LED cambia a amarillo (indica "procesando")
3. **Publica mensaje en TOPIC_TIMBRE**

```
┌──────────────────┐
│   Tu Raspberry   │
│   ─────────────  │
│ mqtt_client.     │
│ publish(         │
│   'cerradura/    │
│   timbre',       │
│   'ping'         │
│ )                │
└────────┬─────────┘
         │
         │ 📡 Envía por red
         │
         ▼
    ┌─────────────────┐
    │ MQTT Broker     │
    │ (Mosquitto)     │
    │ Puerto 1883     │
    └─────────────────┘
```

**El publish hace DOS cosas:**

1. **Envía el mensaje al broker MQTT** (llega a otros clientes suscritos)
2. **Como TU MISMO cliente ESTÁ suscrito a TOPIC_TIMBRE**, el broker te devuelve el mensaje
3. **Automáticamente llama tu `on_message()`** con ese mensaje

---

## 🎧 FASE 3: on_message() (Recibe el evento)

```python
# FaceID.py línea 583-597
def on_message(client, userdata, msg):
    print(f'[MQTT] Mensaje en topic {msg.topic}: {msg.payload}')
    try:
        if msg.topic == TOPIC_REGISTRO:              # cerradura/registro
            threading.Thread(target=handle_registro, args=(client, msg.payload)).start()
        
        elif msg.topic == TOPIC_TIMBRE:              # cerradura/timbre ⬅️ AQUI
            threading.Thread(target=handle_timbre, args=(client,)).start()
        
        elif msg.topic == TOPIC_CONFIRMACION:        # cerradura/confirmacion
            threading.Thread(target=handle_confirmacion, args=(client, msg.payload)).start()
        else:
            print(f'[MQTT] Topic no manejado: {msg.topic}')
    except Exception as e:
        print(f'[MQTT] Error al procesar mensaje: {e}')
```

**¿Cómo se llama on_message()?**

```python
# FaceID.py línea 607-609
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message  # ⬅️ Registra el callback
```

**paho.mqtt.client automáticamente:**
- Monitorea el broker
- Cuando recibe un mensaje en un topic **suscrito**
- **Automáticamente llama** `on_message(client, userdata, msg)`

```
┌─────────────────────────────────────────────────────────────────┐
│  MQTT LIBRARY (paho.mqtt.client) - Loop Infinito                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  client.loop_forever()  # ⬅️ Línea 619                          │
│  {                                                               │
│    while True:                                                  │
│      mensajes = recibir_del_broker()                           │
│      for cada_mensaje in mensajes:                             │
│        on_message(client, userdata, cada_mensaje)  # AUTOMÁTICO│
│  }                                                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 FASE 4: handle_timbre() (Procesa el reconocimiento)

```python
# FaceID.py línea 459-546
def handle_timbre(client):
    """Maneja el evento del timbre (reconocimiento de rostro)"""
    global last_recognized_person
    
    print("[TIMBRE] Procesando reconocimiento...")
    cambiar_estado_app(AppState.PROCESANDO_RECONOCIMIENTO)
    cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
    
    client.publish(TOPIC_STATUS, 'Evento timbre recibido: capturando')
    
    # Captura imagen de la cámara
    img, err = capture_frame()
    if err:
        print(f"[TIMBRE] Error de captura: {err}")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, ...}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return

    # Genera embedding (fingerprint del rostro)
    embedding = get_embedding_from_pil(img)
    if embedding is None:
        print("[TIMBRE] No se detectó rostro")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'coincidencia': False}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return

    # Compara con rostros guardados
    stored_embeddings, names = load_embeddings()
    if not stored_embeddings:
        print("[TIMBRE] No hay rostros registrados")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'coincidencia': False}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return

    # Calcula distancias
    distancias = [float(np.linalg.norm(embedding - emb)) for emb in stored_embeddings]
    min_dist = min(distancias)
    idx = int(np.argmin(distancias))
    umbral = 0.8  # Umbral de distancia para coincidencia

    cambiar_estado_app(AppState.ESPERANDO_CONFIRMACION)

    # ⬇️ RESULTADO: Coincidencia o no
    if min_dist < umbral:
        nombre = names[idx] if idx < len(names) else f'Persona #{idx+1}'
        print(f'[TIMBRE] Coincidencia: {nombre} (distancia {min_dist:.4f})')
        last_recognized_person = {'nombre': nombre, 'distancia': min_dist}
        cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
        
        # ⬅️ PUBLICA RESPUESTA POSITIVA
        client.publish(TOPIC_RESPUESTA, json.dumps({
            'ok': True,
            'mensaje': 'Coincidencia encontrada',
            'coincidencia': True,
            'nombre': nombre,
            'distancia': min_dist
        }))
    else:
        print(f'[TIMBRE] No coincidencia (min dist {min_dist:.4f})')
        last_recognized_person = None
        cambiar_estado_led(LEDState.AZUL_TITILANTE)
        
        # ⬅️ PUBLICA RESPUESTA NEGATIVA
        client.publish(TOPIC_RESPUESTA, json.dumps({
            'ok': True,
            'mensaje': 'No coincide con la base',
            'coincidencia': False,
            'distancia': min_dist
        }))
```

**¿Qué sucede aquí?**

1. Captura frame de la cámara
2. Genera embedding (fingerprint facial)
3. Compara con embeddings guardados
4. **Publica resultado en `TOPIC_RESPUESTA`**

---

## 💻 FASE 5: script.js recibe la respuesta (Frontend)

```javascript
// script.js línea 1-100
const client = new Paho.MQTT.Client(location.hostname, 9001, "web_" + Math.random());

client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;

client.connect({ onSuccess: onConnect });

function onConnect() {
    console.log("✅ Conectado al broker MQTT");
    client.subscribe("cerradura/persona");      // ⬅️ SUSCRITO A RESPUESTA
    client.subscribe("cerradura/status");
}

// ⬇️ AUTOMÁTICO: Se llama cuando llega un mensaje en topic suscrito
function onMessageArrived(message) {
    const topic = message.destinationName;
    const msg = message.payloadString;
    
    console.log(`Mensaje en ${topic}: ${msg}`);
    
    if (topic === "cerradura/persona") {
        // ⬅️ AQUI: Llega la respuesta del reconocimiento
        const data = JSON.parse(msg);
        
        if (data.coincidencia) {
            setStatus(`✅ Coincidencia: ${data.nombre}`);
            PERSON_INFO.classList.remove('hidden');
        } else {
            setStatus(`❌ No se encontró coincidencia...`);
            PERSON_INFO.classList.add('hidden');
        }
    }
}
```

---

## 📡 DIAGRAMA COMPLETO DE TÓPICOS

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TÓPICOS MQTT UTILIZADOS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  cerradura/registro       ← Web/Admin publica nombre a registrar    │
│                           → FaceID.py se suscribe                   │
│                           → on_message() llama handle_registro()    │
│                                                                       │
│  cerradura/timbre         ← FaceID.py publica "ping"               │
│                           (cuando botón se presiona)               │
│                           → FaceID.py se suscribe (loopback)      │
│                           → on_message() llama handle_timbre()    │
│                                                                       │
│  cerradura/persona        ← FaceID.py publica resultado AQUI       │
│  (TOPIC_RESPUESTA)        → script.js (web) se suscribe           │
│                           → onMessageArrived() procesa respuesta  │
│                                                                       │
│  cerradura/confirmacion   ← Web publica decisión (permitir/negar)  │
│                           → FaceID.py se suscribe                  │
│                           → on_message() llama handle_confirmacion()
│                                                                       │
│  cerradura/status         ← FaceID.py publica estados/mensajes    │
│                           → Web se suscribe (solo info)            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUJO COMPLETO PASO A PASO

```
PASO 1: Presionas el botón físico
├─ GPIO 16 detecta LOW → HIGH transición
└─ gpiozero.Button automáticamente llama on_boton_presionado()

PASO 2: on_boton_presionado() evalúa estado
├─ Lee current_app_state (supongamos AppState.ESPERANDO)
└─ Llama iniciar_reconocimiento()

PASO 3: iniciar_reconocimiento() publica
├─ Cambia LED a AMARILLO (indica procesando)
├─ Publica "ping" en TOPIC_TIMBRE (cerradura/timbre)
└─ Envía mensaje al MQTT Broker

PASO 4: MQTT Broker recibe publish
├─ Broker almacena el mensaje en TOPIC_TIMBRE
└─ Como TÚ estás suscrito, broker te devuelve el mensaje

PASO 5: paho.mqtt.client.loop_forever() detecta el mensaje
├─ Revisa cola de mensajes recibidos
├─ Encuentra un mensaje en TOPIC_TIMBRE
└─ AUTOMÁTICAMENTE llama on_message(client, userdata, msg)

PASO 6: on_message() procesa
├─ Verifica msg.topic == TOPIC_TIMBRE ✓
├─ Crea NUEVO HILO (threading.Thread)
└─ Lanza handle_timbre(client) en ese hilo

PASO 7: handle_timbre() ejecuta EN PARALELO
├─ Captura imagen de cámara
├─ Genera embedding (facial fingerprint)
├─ Compara con base de datos
├─ Decide: ¿Coincidencia o no?
└─ Publica resultado en TOPIC_RESPUESTA (cerradura/persona)

PASO 8: MQTT Broker recibe respuesta
├─ script.js está suscrito a cerradura/persona
└─ Broker envía mensaje a script.js

PASO 9: script.js recibe respuesta (en navegador)
├─ onMessageArrived() se ejecuta automáticamente
├─ Parsea JSON con {coincidencia: true/false, nombre, ...}
├─ Actualiza UI con resultado
└─ Muestra botones de confirmación (SIEMPRE VISIBLES)

PASO 10: Usuario presiona "Permitir" o "Denegar"
├─ script.js publica en cerradura/confirmacion
├─ on_message() (servidor) llama handle_confirmacion()
├─ Servo abre puerta o solo apaga LED
└─ Vuelve a estado AppState.ESPERANDO
```

---

## ⚙️ FUNCIONES CLAVE RESUMEN

| Función | Quién la llama | Qué hace |
|---------|----------------|----------|
| `on_boton_presionado()` | gpiozero (automático) | Inicia reconocimiento/registro |
| `iniciar_reconocimiento()` | on_boton_presionado() | Publica en TOPIC_TIMBRE |
| `on_message()` | paho.mqtt (automático) | Recibe mensajes, crea hilos |
| `handle_timbre()` | on_message() (en hilo) | Procesa reconocimiento facial |
| `onMessageArrived()` | Paho MQTT JS (automático) | Recibe en web, actualiza UI |

---

## 🎯 RESPUESTA A TU PREGUNTA

> Cuando se publica en TOPIC_TIMBRE, ¿quién lo recibe? ¿on_connect?

**NO, lo recibe `on_message()`:**

1. **`on_connect()`** se llama UNA SOLA VEZ cuando te conectas al broker
   - Solo para suscribirse a topics
   - No recibe mensajes

2. **`on_message()`** se llama CADA VEZ que llega un mensaje a un topic suscrito
   - Se ejecuta automáticamente en loop_forever()
   - Es donde se procesa cada mensaje

```python
# Registras el callback en setup
mqtt_client.on_message = on_message

# paho.mqtt internamente hace esto:
while client_connected:
    mensajes = recibir_del_broker()
    for msg in mensajes:
        on_message(client, userdata, msg)  # ⬅️ TU FUNCIÓN
```

---

## 📊 ARQUITECTURA COMPLETA

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARQUITECTURA MQTT                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Tu Raspberry Pi (FaceID.py)                                  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ mqtt_client = mqtt.Client()                                  │   │
│  │ mqtt_client.on_connect = on_connect                          │   │
│  │ mqtt_client.on_message = on_message  ⬅️ AQUI LLEGA TODO    │   │
│  │ mqtt_client.connect(BROKER, PORT)                           │   │
│  │ mqtt_client.loop_forever()  ⬅️ LOOP INFINITO              │   │
│  │ {                                                            │   │
│  │   mientras conectado:                                       │   │
│  │     on_message() se llama automáticamente                  │   │
│  │ }                                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↑                                           │
│                          │ MQTT                                      │
│                          │ (Red/TCP)                                 │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ MQTT Broker (Mosquitto)                                      │   │
│  │ Puerto 1883 / 9001                                           │   │
│  │                                                               │   │
│  │ Tópicos:                                                     │   │
│  │  - cerradura/registro                                        │   │
│  │  - cerradura/timbre                                          │   │
│  │  - cerradura/persona (RESPUESTAS)                            │   │
│  │  - cerradura/confirmacion                                    │   │
│  │  - cerradura/status                                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↑                                           │
│                          │ MQTT                                      │
│                          │ WebSocket                                 │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Navegador Web (script.js)                                    │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ client = new Paho.MQTT.Client()                             │   │
│  │ client.onMessageArrived = onMessageArrived  ⬅️ RESPUESTAS  │   │
│  │ client.connect()                                             │   │
│  │ {                                                            │   │
│  │   cuando llega mensaje:                                      │   │
│  │     onMessageArrived() se llama automáticamente             │   │
│  │ }                                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 💡 ANALOGÍA: Sistema de Timbre en Casa

```
SENSOR DE TIMBRE (gpiozero Button)
    ↓ Detecta presión
CAMPANILLA SUENA (on_boton_presionado)
    ↓ Se activa
TÚ ESCUCHAS (iniciar_reconocimiento)
    ↓ Oyes el timbre
TÚ GRITAS "¡Hay alguien!" (publica en TOPIC_TIMBRE)
    ↓ Comunicas
VECINO ESCUCHA (on_message - automático)
    ↓ Mediante MQTT Broker
VECINO VE QUIÉN ES (handle_timbre - procesa)
    ↓ Verifica si es conocido
VECINO TE GRITA "¡Es Mati!" o "¡No conozco!" (publica TOPIC_RESPUESTA)
    ↓ Comunica resultado
TÚ ESCUCHAS (onMessageArrived - web)
    ↓ Mediante MQTT Broker
TÚ DECIDES PERMITIR/DENEGAR (presionas botón web)
    ↓ Comunicas decisión
PUERTA SE ABRE O CIERRA (handle_confirmacion)
    ↓ Ejecuta acción
```

---

## 🎓 PUNTO CLAVE

**La clave es entender que MQTT Broker es como un correo postal:**

1. **Envías una carta** (publish) → llega al correo
2. **El correo la reparte** a todos los que se suscribieron a ese tópico
3. **Tú también recibes tu propia carta** (porque estás suscrito)
4. **Tu `on_message()` automáticamente procesa cada carta** que llega

No necesitas preguntar al correo "¿llegó mi carta?", el correo te avisa automáticamente mediante el callback `on_message`.

