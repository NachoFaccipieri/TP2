# Funciones Importadas de PAHO MQTT

## Resumen Rápido

| Función Importada | Línea Import | Línea Uso | Propósito |
|-------------------|--------------|-----------|-----------|
| `mqtt.Client()` | 19 | 619, 636 | Crear cliente MQTT |
| `client.on_connect` | 19 | 620, 638 | Asignar callback de conexión |
| `client.on_message` | 19 | 621, 639 | Asignar callback de mensaje |
| `client.connect()` | 19 | 626, 641 | Conectar a broker MQTT |
| `client.subscribe()` | 19 | 577-579 | Suscribirse a topic |
| `client.publish()` | 19 | 412, 427, 428, 517, 521, 529, 533, 540, 547, 552, 558, 563, 569, 580 | Publicar mensaje en topic |
| `client.loop_forever()` | 19 | 631, 651 | Loop infinito procesando MQTT |

---

## Import Statement

### Línea 19: PAHO MQTT Import

```python
import paho.mqtt.client as mqtt
```

**¿Qué proporciona?**
- `mqtt.Client()` - Crear cliente MQTT
- `client.on_connect` - Propiedad para callback de conexión
- `client.on_message` - Propiedad para callback de mensaje
- `client.connect()` - Conectar a broker
- `client.subscribe()` - Suscribirse a topics
- `client.publish()` - Publicar mensajes
- `client.loop_forever()` - Loop principal MQTT

---

## Función: mqtt.Client()

### Creación del Cliente (Línea 619)

```python
def main():
    client = mqtt.Client()  # Línea 619
    client.on_connect = on_connect
    client.on_message = on_message
```

**De dónde viene:**
- `mqtt.Client()` ← de `import paho.mqtt.client as mqtt` (línea 19)

**Qué hace:**
- Crea un objeto cliente MQTT
- Retorna una instancia que se puede usar para conectar/publicar/suscribirse

---

## Propiedad: client.on_connect

### Asignación de Callback (Línea 620)

```python
def main():
    client = mqtt.Client()
    client.on_connect = on_connect  # Línea 620
    client.on_message = on_message
```

**De dónde viene:**
- `client.on_connect` ← propiedad del objeto Client (de paho)

**Qué hace:**
- Asigna la función `on_connect()` como callback
- Se ejecuta automáticamente cuando MQTT se conecta

**Función de Callback (Línea 569-583):**

```python
def on_connect(client, userdata, flags, rc):
    """Callback ejecutado cuando MQTT conecta"""
    if rc == 0:  # Conexión exitosa
        print(f'[MQTT] Conectado al broker MQTT {BROKER}:{BROKER_PORT}')
        
        # Suscribirse a topics
        client.subscribe(TOPIC_REGISTRO)         # Línea 577
        client.subscribe(TOPIC_TIMBRE)           # Línea 578
        client.subscribe(TOPIC_CONFIRMACION)     # Línea 579
        
        # Cambiar estado del sistema
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        
        # Publicar que estamos listos
        client.publish(TOPIC_STATUS, 'servicio-listo')  # Línea 585
    else:
        print(f'[MQTT] Error al conectar al broker MQTT, rc={rc}')
```

---

## Propiedad: client.on_message

### Asignación de Callback (Línea 621)

```python
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message  # Línea 621
```

**De dónde viene:**
- `client.on_message` ← propiedad del objeto Client (de paho)

**Qué hace:**
- Asigna la función `on_message()` como callback
- Se ejecuta automáticamente cuando llega un mensaje MQTT

**Función de Callback (Línea 608-621):**

```python
def on_message(client, userdata, msg):
    """Callback ejecutado cuando llega un mensaje MQTT"""
    print(f'[MQTT] Mensaje en topic {msg.topic}: {msg.payload}')
    try:
        if msg.topic == TOPIC_REGISTRO:
            # Manejar registro en hilo separado
            threading.Thread(target=handle_registro, args=(client, msg.payload)).start()
            
        elif msg.topic == TOPIC_TIMBRE:
            # Manejar timbre en hilo separado
            threading.Thread(target=handle_timbre, args=(client,)).start()
            
        elif msg.topic == TOPIC_CONFIRMACION:
            # Manejar confirmación en hilo separado
            threading.Thread(target=handle_confirmacion, args=(client, msg.payload)).start()
        else:
            print(f'[MQTT] Topic no manejado: {msg.topic}')
    except Exception as e:
        print(f'[MQTT] Error al procesar mensaje: {e}')
```

---

## Función: client.subscribe()

### Suscripción a Topics (Línea 577-579)

```python
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f'[MQTT] Conectado al broker MQTT {BROKER}:{BROKER_PORT}')
        
        client.subscribe(TOPIC_REGISTRO)         # Línea 577
        client.subscribe(TOPIC_TIMBRE)           # Línea 578
        client.subscribe(TOPIC_CONFIRMACION)     # Línea 579
```

**De dónde viene:**
- `client.subscribe(topic)` ← método del objeto Client (de paho)

**Qué hace:**
- Se suscribe a un topic MQTT
- Cuando llega un mensaje a ese topic, se ejecuta `on_message()`

**Topics Suscritos:**
- `TOPIC_REGISTRO = 'cerradura/registro'` - Nuevo registro
- `TOPIC_TIMBRE = 'cerradura/timbre'` - Botón timbre
- `TOPIC_CONFIRMACION = 'cerradura/confirmacion'` - Decisión de acceso

---

## Función: client.connect()

### Conexión al Broker (Línea 626)

```python
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, BROKER_PORT, 60)  # Línea 626
    except Exception as e:
        print('Error al conectar al broker MQTT:', e)
        sys.exit(1)
```

**De dónde viene:**
- `client.connect(host, port, keepalive)` ← método del objeto Client (de paho)

**Parámetros:**
- `BROKER` = 'localhost' (por defecto, del env)
- `BROKER_PORT` = 1883 (puerto MQTT estándar)
- `60` = keepalive en segundos

**Línea 641 (En start_mqtt()):**

```python
def start_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(BROKER, BROKER_PORT, 60)  # Línea 641
    except Exception as e:
        print(f'[MQTT] Error al conectar al broker MQTT: {e}')
        cambiar_estado_led(LEDState.AMARILLO_TITILANTE)
        return
```

---

## Función: client.publish()

### Publicar Mensajes (Línea 412, 427, 428, etc.)

**Parámetros generales:**
```python
client.publish(topic, payload)
# topic: string con nombre del topic
# payload: string con el mensaje
```

### Uso 1: En iniciar_reconocimiento() (Línea 412)

```python
def iniciar_reconocimiento():
    """Inicia el proceso de reconocimiento desde el botón físico"""
    global mqtt_client
    
    cambiar_estado_app(AppState.PROCESANDO_RECONOCIMIENTO)
    cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
    
    if mqtt_client:
        mqtt_client.publish(TOPIC_TIMBRE, 'ping')  # Línea 412
```

**¿Qué publica?**
- Topic: `TOPIC_TIMBRE = 'cerradura/timbre'`
- Mensaje: `'ping'`

---

### Uso 2: En handle_registro() (Línea 517)

```python
def handle_registro(client, payload):
    """Maneja el evento de registro de nuevo rostro"""
    global registro_solicitado_flag, nombre_registro_pendiente
    
    nombre = None
    try:
        data = json.loads(payload)
        nombre = data.get('nombre')
    except Exception:
        nombre = payload.decode() if isinstance(payload, bytes) else str(payload)

    print(f"[REGISTRO] Solicitando registro para: {nombre}")
    print("[REGISTRO] Esperando presión de botón físico para capturar...")
    
    nombre_registro_pendiente = nombre
    
    registro_solicitado_flag = True
    cambiar_estado_app(AppState.ESPERANDO_REGISTRO)
    cambiar_estado_led(LEDState.AZUL_TITILANTE)
    
    client.publish(TOPIC_STATUS, f'Presiona el botón físico para registrar rostro de "{nombre}"')  # Línea 517
```

**¿Qué publica?**
- Topic: `TOPIC_STATUS = 'cerradura/status'`
- Mensaje: String con instrucciones

---

### Uso 3: En handle_timbre() - Errores (Línea 527)

```python
def handle_timbre(client):
    """Maneja el evento del timbre (reconocimiento de rostro)"""
    global last_recognized_person
    
    print("[TIMBRE] Procesando reconocimiento...")
    cambiar_estado_app(AppState.PROCESANDO_RECONOCIMIENTO)
    cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
    
    client.publish(TOPIC_STATUS, 'Evento timbre recibido: capturando')
    img, err = capture_frame()
    
    # Si existe algún error al capturar
    if err:
        print(f"[TIMBRE] Error de captura: {err}")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': err, 'coincidencia': False}))  # Línea 527
```

**¿Qué publica?**
- Topic: `TOPIC_RESPUESTA = 'cerradura/persona'`
- Mensaje: JSON con `{'ok': False, 'mensaje': ..., 'coincidencia': False}`

---

### Uso 4: En handle_timbre() - Sin Rostro (Línea 533)

```python
    # Se genera el embedding
    embedding = generarEmbedding(img)

    # Si no se detecta rostro
    if embedding is None:
        print("[TIMBRE] No se detectó rostro")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No se detectó rostro', 'coincidencia': False}))  # Línea 533
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return
```

**¿Qué publica?**
- Topic: `TOPIC_RESPUESTA = 'cerradura/persona'`
- Mensaje: JSON con `{'ok': True, 'mensaje': 'No se detectó rostro', 'coincidencia': False}`

---

### Uso 5: En handle_timbre() - Sin BD (Línea 540)

```python
    # Se cargan los embeddings almacenados
    stored_embeddings, names = load_embeddings()
    # Si no hay embeddings almacenados
    if not stored_embeddings:
        print("[TIMBRE] No hay rostros registrados")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No hay rostros registrados', 'coincidencia': False}))  # Línea 540
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return
```

---

### Uso 6: En handle_timbre() - Coincidencia (Línea 558)

```python
    if min_dist < umbral:
        nombre = names[idx] if idx < len(names) else f'Persona #{idx+1}'
        porcentaje = int((1 - min_dist / umbral) * 100) if min_dist < umbral else 0
        print(f'[TIMBRE] Coincidencia: {nombre} ({porcentaje}% de coincidencia)')
        last_recognized_person = {'nombre': nombre, 'distancia': min_dist}
        cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
        client.publish(TOPIC_RESPUESTA, json.dumps({  # Línea 558-563
            'ok': True,
            'mensaje': 'Coincidencia encontrada',
            'coincidencia': True,
            'nombre': nombre,
            'distancia': min_dist,
            'porcentaje': porcentaje
        }))
```

**¿Qué publica?**
- Topic: `TOPIC_RESPUESTA = 'cerradura/persona'`
- Mensaje: JSON con datos de coincidencia

---

### Uso 7: En handle_timbre() - No Coincidencia (Línea 569)

```python
    else:
        print(f'[TIMBRE] No coincidencia (min dist {min_dist:.4f})')
        last_recognized_person = None
        cambiar_estado_led(LEDState.AZUL_TITILANTE)
        client.publish(TOPIC_RESPUESTA, json.dumps({  # Línea 569-573
            'ok': True,
            'mensaje': 'No coincide con la base',
            'coincidencia': False,
            'distancia': min_dist
        }))
```

---

### Uso 8: En handle_confirmacion() - Permitido (Línea 590)

```python
def handle_confirmacion(client, payload):
    """Maneja la confirmación de acceso desde la web"""
    try:
        data = json.loads(payload)
        permitir = data.get('permitir', False)
    except Exception:
        print("[CONFIRMACION] Error al parsear confirmación")
        return
    
    if permitir:
        print("[CONFIRMACION] Acceso PERMITIDO")
        cambiar_estado_led(LEDState.VERDE_10S)
        abrir_puerta()
        client.publish(TOPIC_STATUS, '✅ Acceso permitido - Puerta abierta 10 segundos')  # Línea 590
    else:
        print("[CONFIRMACION] Acceso DENEGADO")
        cambiar_estado_led(LEDState.ROJO_10S)
        client.publish(TOPIC_STATUS, '❌ Acceso denegado')  # Línea 594
```

---

## Función: client.loop_forever()

### Loop Infinito MQTT (Línea 631)

```python
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, BROKER_PORT, 60)
    except Exception as e:
        print('Error al conectar al broker MQTT:', e)
        sys.exit(1)

    # loop_forever bloqueará el hilo principal
    try:
        client.loop_forever()  # Línea 631
    except KeyboardInterrupt:
        print('Interrumpido por teclado, saliendo...')
```

**De dónde viene:**
- `client.loop_forever()` ← método del objeto Client (de paho)

**Qué hace:**
- Inicia un loop infinito que procesa mensajes MQTT
- Bloquea el hilo (no retorna)
- Ejecuta callbacks `on_connect()` y `on_message()` cuando es necesario
- Solo termina con `Ctrl+C` (KeyboardInterrupt)

### Línea 651 (En start_mqtt())

```python
def start_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(BROKER, BROKER_PORT, 60)
    except Exception as e:
        print(f'[MQTT] Error al conectar al broker MQTT: {e}')
        cambiar_estado_led(LEDState.AMARILLO_TITILANTE)
        return

    # Loop MQTT en hilo separado
    mqtt_client.loop_forever()  # Línea 651
```

**Diferencia:**
- En `start_mqtt()` se ejecuta en un **hilo separado** (daemon)
- En `main()` se ejecuta en el **hilo principal**

---

## Resumen de Todas las Funciones PAHO

```python
# Línea 19
import paho.mqtt.client as mqtt

# Crear cliente
client = mqtt.Client()
# ↑ mqtt.Client() - Función

# Asignar callbacks
client.on_connect = callback_func
# ↑ client.on_connect - Propiedad

client.on_message = callback_func
# ↑ client.on_message - Propiedad

# Conectar
client.connect(broker, puerto, keepalive)
# ↑ client.connect() - Método

# Suscribirse
client.subscribe(topic)
# ↑ client.subscribe() - Método

# Publicar
client.publish(topic, mensaje)
# ↑ client.publish() - Método

# Loop infinito
client.loop_forever()
# ↑ client.loop_forever() - Método
```

---

## Tabla Completa - PAHO Funciones

| Función/Propiedad | Línea Import | Tipo | Dónde se Usa | Línea Uso | Propósito |
|-------------------|--------------|------|--------------|-----------|-----------|
| `mqtt.Client()` | 19 | Constructor | `main()` | 619 | Crear cliente MQTT |
| `mqtt.Client()` | 19 | Constructor | `start_mqtt()` | 636 | Crear cliente MQTT |
| `client.on_connect` | 19 | Propiedad | `main()` | 620 | Asignar callback de conexión |
| `client.on_connect` | 19 | Propiedad | `start_mqtt()` | 638 | Asignar callback de conexión |
| `client.on_message` | 19 | Propiedad | `main()` | 621 | Asignar callback de mensaje |
| `client.on_message` | 19 | Propiedad | `start_mqtt()` | 639 | Asignar callback de mensaje |
| `client.connect()` | 19 | Método | `main()` | 626 | Conectar a broker MQTT |
| `client.connect()` | 19 | Método | `start_mqtt()` | 641 | Conectar a broker MQTT |
| `client.subscribe()` | 19 | Método | `on_connect()` | 577 | Suscribirse a TOPIC_REGISTRO |
| `client.subscribe()` | 19 | Método | `on_connect()` | 578 | Suscribirse a TOPIC_TIMBRE |
| `client.subscribe()` | 19 | Método | `on_connect()` | 579 | Suscribirse a TOPIC_CONFIRMACION |
| `client.publish()` | 19 | Método | `on_connect()` | 585 | Publicar en TOPIC_STATUS |
| `client.publish()` | 19 | Método | `iniciar_reconocimiento()` | 412 | Publicar ping en TOPIC_TIMBRE |
| `client.publish()` | 19 | Método | `handle_registro()` | 517 | Publicar en TOPIC_STATUS |
| `client.publish()` | 19 | Método | `handle_timbre()` | 521 | Publicar en TOPIC_STATUS |
| `client.publish()` | 19 | Método | `handle_timbre()` | 527 | Publicar en TOPIC_RESPUESTA |
| `client.publish()` | 19 | Método | `handle_timbre()` | 533 | Publicar en TOPIC_RESPUESTA |
| `client.publish()` | 19 | Método | `handle_timbre()` | 540 | Publicar en TOPIC_RESPUESTA |
| `client.publish()` | 19 | Método | `handle_timbre()` | 558-563 | Publicar en TOPIC_RESPUESTA |
| `client.publish()` | 19 | Método | `handle_timbre()` | 569-573 | Publicar en TOPIC_RESPUESTA |
| `client.publish()` | 19 | Método | `handle_confirmacion()` | 590 | Publicar en TOPIC_STATUS |
| `client.publish()` | 19 | Método | `handle_confirmacion()` | 594 | Publicar en TOPIC_STATUS |
| `client.loop_forever()` | 19 | Método | `main()` | 631 | Loop infinito MQTT |
| `client.loop_forever()` | 19 | Método | `start_mqtt()` | 651 | Loop infinito MQTT |

---

## Ejemplo Completo: Flujo MQTT

```
PASO 1: Crear cliente
  ├─ client = mqtt.Client()  ◄── mqtt.Client()
  ├─ client.on_connect = on_connect  ◄── client.on_connect
  └─ client.on_message = on_message  ◄── client.on_message

PASO 2: Conectar a broker
  └─ client.connect(BROKER, BROKER_PORT, 60)  ◄── client.connect()
  
PASO 3: Suscribirse a topics
  ├─ client.subscribe('cerradura/registro')  ◄── client.subscribe()
  ├─ client.subscribe('cerradura/timbre')  ◄── client.subscribe()
  └─ client.subscribe('cerradura/confirmacion')  ◄── client.subscribe()

PASO 4: Iniciar loop
  └─ client.loop_forever()  ◄── client.loop_forever()
     │
     ├─ Espera mensajes en topics suscritos
     │
     └─ Cuando llega mensaje:
        └─ on_message(client, userdata, msg) se ejecuta
           ├─ Revisa msg.topic
           ├─ Si es 'cerradura/registro':
           │  └─ Publica en TOPIC_STATUS
           │     └─ client.publish(TOPIC_STATUS, mensaje)  ◄── client.publish()
           │
           ├─ Si es 'cerradura/timbre':
           │  └─ Publica en TOPIC_RESPUESTA después de procesar
           │     └─ client.publish(TOPIC_RESPUESTA, json)  ◄── client.publish()
           │
           └─ Si es 'cerradura/confirmacion':
              └─ Abre puerta y publica en TOPIC_STATUS
                 └─ client.publish(TOPIC_STATUS, mensaje)  ◄── client.publish()
```

---

## Variables de Configuración PAHO

```python
# Línea 102
BROKER = os.environ.get('MQTT_BROKER', 'localhost')
# Host del broker MQTT

# Línea 103
BROKER_PORT = int(os.environ.get('MQTT_PORT', '1883'))
# Puerto del broker MQTT (1883 es estándar)

# Línea 104-108: Topics suscritos
TOPIC_REGISTRO = os.environ.get('TOPIC_REGISTRO', 'cerradura/registro')
TOPIC_TIMBRE = os.environ.get('TOPIC_TIMBRE', 'cerradura/timbre')
TOPIC_RESPUESTA = os.environ.get('TOPIC_RESPUESTA', 'cerradura/persona')
TOPIC_STATUS = os.environ.get('TOPIC_STATUS', 'cerradura/status')
TOPIC_CONFIRMACION = os.environ.get('TOPIC_CONFIRMACION', 'cerradura/confirmacion')
```

**Uso en client.subscribe() y client.publish():**
```python
client.subscribe(TOPIC_REGISTRO)  # 'cerradura/registro'
client.subscribe(TOPIC_TIMBRE)    # 'cerradura/timbre'
client.subscribe(TOPIC_CONFIRMACION)  # 'cerradura/confirmacion'

client.publish(TOPIC_STATUS, mensaje)  # 'cerradura/status'
client.publish(TOPIC_RESPUESTA, json)  # 'cerradura/persona'
```

