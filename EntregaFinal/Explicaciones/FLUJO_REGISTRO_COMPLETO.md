# 📝 FLUJO COMPLETO DE REGISTRO - Continuación

## Recapitulación (Lo que ya explicaste)

```
1️⃣  Usuario presiona "Registrar nuevo rostro" en web
    ↓
2️⃣  registrarNuevoRostro() (JavaScript)
    ├─ Pide nombre: "Nacho"
    ├─ Publica en 'cerradura/registro': { nombre: "Nacho" }
    ↓
3️⃣  MQTT Broker recibe en 'cerradura/registro'
    ↓
4️⃣  on_message() (Python) se ejecuta
    ├─ Verifica topic == TOPIC_REGISTRO
    ├─ Crea hilo
    ├─ Ejecuta handle_registro(client, payload)
    ↓
5️⃣  handle_registro() (Python)
    ├─ Extrae nombre: "Nacho"
    ├─ Establece nombre_registro_pendiente = "Nacho"
    ├─ Establece registro_solicitado_flag = True
    ├─ Cambia estado a ESPERANDO_REGISTRO
    ├─ LED cambia a AZUL_TITILANTE (parpadeando)
    ├─ Publica en 'cerradura/status': "Presiona botón para registrar Nacho"
    └─ TERMINA (pero cambió estados y flags)
```

---

## ✅ Continuación: ¿Qué pasa después?

### PASO 6️⃣ : El Sistema Espera (en Paralelo)

```
ESTADO DEL SISTEMA DESPUÉS DE handle_registro():

┌─────────────────────────────────────────────────────────┐
│  Variables Globales (FaceID.py)                         │
├─────────────────────────────────────────────────────────┤
│  nombre_registro_pendiente = "Nacho"                    │
│  registro_solicitado_flag = True                        │
│  current_app_state = AppState.ESPERANDO_REGISTRO        │
│  current_led_state = LEDState.AZUL_TITILANTE            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Hardware (Raspberry Pi)                                │
├─────────────────────────────────────────────────────────┤
│  LED RGB: AZUL parpadeando (indica "espera")            │
│  Botón: gpiozero monitoreando continuamente             │
│  Cámara: Lista para capturar                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Web (script.js)                                        │
├─────────────────────────────────────────────────────────┤
│  Recibe en 'cerradura/status':                          │
│  "Presiona el botón para registrar Nacho"               │
│  Muestra en la pantalla esta información                │
└─────────────────────────────────────────────────────────┘
```

### PASO 7️⃣ : Usuario Presiona Botón Físico

```
👆 USUARIO PRESIONA EL BOTÓN FÍSICO (GPIO 16)
    ↓
gpiozero detecta la presión
    ↓
    ¿Cómo? gpiozero corre internamente un thread que
    monitorea el GPIO 16 continuamente:
    
    while True:
        if GPIO_16_is_LOW():  # Botón presionado
            on_boton_presionado()  # Llama callback
        time.sleep(0.01)
    ↓
on_boton_presionado() se ejecuta automáticamente
    ├─ print("[BOTON] ✅ Botón presionado")
    ├─ Lee el estado actual: current_app_state
    │  → Es AppState.ESPERANDO_REGISTRO ✓
    ├─ Como el estado es ESPERANDO_REGISTRO:
    │  └─ Llama iniciar_registro()
    └─ Fin
```

---

## 🎯 PASO 8️⃣ : iniciar_registro() se Ejecuta

```python
def iniciar_registro():
    """Inicia el proceso de registro desde el botón físico"""
    global mqtt_client, registro_solicitado_flag, nombre_registro_pendiente
    
    # Verificación de seguridad
    if not registro_solicitado_flag:
        print("[APP] No hay registro solicitado, ignorando presión de botón")
        return
    # → En nuestro caso: registro_solicitado_flag == True, así que continúa
    
    print(f"[REGISTRO] Capturando rostro para: {nombre_registro_pendiente}")
    # → Imprime: "[REGISTRO] Capturando rostro para: Nacho"
    
    cambiar_estado_app(AppState.REGISTRANDO)
    # → Cambia estado a REGISTRANDO
    
    cambiar_estado_led(LEDState.AZUL_TITILANTE)
    # → LED sigue en AZUL_TITILANTE (igual que antes)
    
    # CAPTURA DE IMAGEN
    img, err = capture_frame()
    if err:
        print(f"[REGISTRO] Error de captura: {err}")
        mqtt_client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': err}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        registro_solicitado_flag = False
        nombre_registro_pendiente = None
        return
    # → Si captura bien: img = PIL.Image, err = None
    
    # GENERAR EMBEDDING
    embedding = generarEmbedding(img)
    if embedding is None:
        print("[REGISTRO] No se detectó rostro")
        mqtt_client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': 'No se detectó rostro'}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        registro_solicitado_flag = False
        nombre_registro_pendiente = None
        return
    # → Si detecta rostro: embedding = array de 128 números
    
    # GUARDAR EMBEDDING
    try:
        save_embedding(embedding, nombre_registro_pendiente)
        # → Guarda en:
        #    ├─ embeddings.txt (vector de números)
        #    └─ names.txt (nombre: "Nacho")
        
        print(f'[REGISTRO] Rostro {nombre_registro_pendiente} registrado exitosamente')
        # → Imprime: "[REGISTRO] Rostro Nacho registrado exitosamente"
        
        mqtt_client.publish(TOPIC_RESPUESTA, json.dumps({
            'ok': True,
            'mensaje': f'Rostro {nombre_registro_pendiente} registrado'
        }))
        # → Publica en 'cerradura/persona':
        #    { ok: true, mensaje: "Rostro Nacho registrado" }
        
        cambiar_estado_app(AppState.ESPERANDO)
        # → Cambia estado a ESPERANDO (listo para nuevo evento)
        
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        # → LED cambia a AZUL sólido (indica "listo")
        
    except Exception as e:
        print(f"[REGISTRO] Error al guardar: {e}")
        mqtt_client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': f'Error al guardar: {e}'}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
    
    # LIMPIAR FLAGS
    registro_solicitado_flag = False
    # → Ya no espera más registros
    
    nombre_registro_pendiente = None
    # → Borra el nombre guardado
```

---

## 📊 Tabla del Proceso Completo

| Paso | Evento | Función | Estado App | Estado LED | Variables Clave |
|------|--------|---------|------------|------------|-----------------|
| 1 | Usuario presiona "Registrar" web | registrarNuevoRostro() | ESPERANDO | AZUL_SOLIDO | - |
| 2 | Publica en 'cerradura/registro' | (MQTT) | ESPERANDO | AZUL_SOLIDO | - |
| 3 | on_message() recibe | on_message() | ESPERANDO | AZUL_SOLIDO | - |
| 4 | Crea hilo | handle_registro() | ESPERANDO | AZUL_SOLIDO | - |
| 5 | Cambia estados | handle_registro() | ESPERANDO_REGISTRO | AZUL_TITILANTE | nombre_registro_pendiente="Nacho", registro_solicitado_flag=True |
| 6 | Publica en 'cerradura/status' | handle_registro() | ESPERANDO_REGISTRO | AZUL_TITILANTE | (mismo) |
| 7 | Usuario presiona botón físico | (GPIO 16) | ESPERANDO_REGISTRO | AZUL_TITILANTE | (mismo) |
| 8 | gpiozero detecta presión | on_boton_presionado() | ESPERANDO_REGISTRO | AZUL_TITILANTE | (mismo) |
| 9 | Verifica estado y llama | iniciar_registro() | REGISTRANDO | AZUL_TITILANTE | (mismo) |
| 10 | Captura imagen | capture_frame() | REGISTRANDO | AZUL_TITILANTE | last_captured_image=frame |
| 11 | Genera embedding | generarEmbedding() | REGISTRANDO | AZUL_TITILANTE | embedding=array(128) |
| 12 | Guarda embedding | save_embedding() | REGISTRANDO | AZUL_TITILANTE | (archivos: embeddings.txt, names.txt) |
| 13 | Publica resultado | MQTT publish | ESPERANDO | AZUL_SOLIDO | registro_solicitado_flag=False |
| 14 | Web recibe en 'cerradura/persona' | onMessage() (JS) | ESPERANDO | AZUL_SOLIDO | - |
| 15 | Muestra éxito en pantalla | script.js | ESPERANDO | AZUL_SOLIDO | - |

---

## 🔄 Flujo Completo Visual

```
┌────────────────────────────────────────────────────────────────────┐
│ WEB (script.js)                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ 1️⃣ Usuario: [Registrar nuevo rostro]                             │
│    registrarNuevoRostro()                                          │
│    → prompt("Nombre?") → "Nacho"                                   │
│    → publish('cerradura/registro', { nombre: "Nacho" })           │
│                                                                    │
│    ⬇️  [Espera respuesta en 'cerradura/status']                  │
│    Recibe: "Presiona el botón para registrar Nacho"              │
│    Muestra en pantalla                                             │
│                                                                    │
│    ⬇️  [Espera respuesta en 'cerradura/persona']                 │
│    Recibe: { ok: true, mensaje: "Rostro Nacho registrado" }      │
│    Muestra: "✅ Rostro Nacho registrado"                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                          ⬇️ MQTT ⬆️
┌────────────────────────────────────────────────────────────────────┐
│ SERVIDOR (FaceID.py)                                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ 2️⃣ on_message() - Topic: 'cerradura/registro'                    │
│    → Crea hilo                                                     │
│    → handle_registro(client, payload)                              │
│       ├─ nombre_registro_pendiente = "Nacho"                       │
│       ├─ registro_solicitado_flag = True                           │
│       ├─ estado = ESPERANDO_REGISTRO                               │
│       ├─ LED = AZUL_TITILANTE (parpadeando)                       │
│       └─ publish('cerradura/status', "Presiona botón...")         │
│                                                                    │
│ 3️⃣ [Esperando presión de botón - gpiozero monitorea]            │
│    ⏳ Monitoreo continuo en paralelo                             │
│                                                                    │
│ 4️⃣ on_boton_presionado() - GPIO 16 presionado                   │
│    → Lee estado: current_app_state = ESPERANDO_REGISTRO ✓         │
│    → Llama iniciar_registro()                                      │
│       ├─ estado = REGISTRANDO                                      │
│       ├─ Captura imagen: cv2.VideoCapture()                       │
│       ├─ Genera embedding: FaceNet (128 números)                   │
│       ├─ Guarda: embeddings.txt + names.txt                       │
│       ├─ estado = ESPERANDO                                        │
│       ├─ LED = AZUL_SOLIDO (listo)                                │
│       └─ publish('cerradura/persona', { ok: true, ... })         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                          ⬇️ MQTT ⬆️
┌────────────────────────────────────────────────────────────────────┐
│ HARDWARE (Raspberry Pi)                                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ 🔴 LED RGB:                                                        │
│    - Inicial: AZUL_SOLIDO (estado normal)                         │
│    - Después de handle_registro: AZUL_TITILANTE (espera botón)   │
│    - Después de iniciar_registro: AZUL_SOLIDO (listo)            │
│                                                                    │
│ 🔘 Botón (GPIO 16):                                              │
│    - gpiozero monitorea continuamente                             │
│    - Cuando se presiona: on_boton_presionado()                   │
│                                                                    │
│ 📷 Cámara:                                                         │
│    - capture_frame() abre, captura y cierra                       │
│    - La imagen se guarda en last_captured_image                   │
│                                                                    │
│ 💾 Almacenamiento:                                                │
│    - embeddings.txt: Vectores faciales guardados                  │
│    - names.txt: Nombres asociados                                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Resumen por Secciones

### Sección 1: Solicitud (Web → Servidor)
```
registrarNuevoRostro()
  ↓
publish('cerradura/registro', { nombre })
  ↓
handle_registro()
```

### Sección 2: Espera (Servidor → Hardware)
```
handle_registro()
  ├─ Configura estados y flags
  ├─ Publica aviso
  └─ TERMINA
  
gpiozero (en paralelo)
  └─ Monitorea botón continuamente
```

### Sección 3: Captura (Hardware → Servidor)
```
Usuario presiona botón
  ↓
on_boton_presionado()
  ↓
iniciar_registro()
  ├─ Captura imagen
  ├─ Genera embedding
  └─ Guarda embedding
```

### Sección 4: Respuesta (Servidor → Web)
```
iniciar_registro()
  ↓
publish('cerradura/persona', { ok: true, ... })
  ↓
onMessage() (JavaScript)
  ↓
Muestra éxito en pantalla
```

---

## 📝 Detalle de Funciones Clave

### capture_frame()
```python
def capture_frame(camera_index=0, save_last=True):
    # Abre la cámara
    cap = cv2.VideoCapture(0)
    
    # Captura un frame
    ret, frame = cap.read()
    
    # Guarda copia globalmente
    last_captured_image = frame.copy()
    
    # Cierra la cámara
    cap.release()
    
    # Convierte BGR → RGB para procesamiento
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    
    return img, None  # Retorna imagen PIL
```

### generarEmbedding()
```python
def generarEmbedding(img):
    # Detecta rostro en la imagen
    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None  # No hay rostro
    
    # Extrae el rostro detectado
    x, y, w, h = detections[0]['box']
    face = img_array[y:y+h, x:x+w]
    
    # Normaliza a 160x160 (requerido por FaceNet)
    face = Image.fromarray(face).resize((160, 160))
    
    # Convierte a array para FaceNet
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)
    
    # Genera embedding de 128 números
    embedding = embedder.embeddings(face)[0]
    
    # Normaliza L2
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding  # Array de 128 números
```

### save_embedding()
```python
def save_embedding(embedding, nombre):
    # Guarda embedding (vector) en embeddings.txt
    with open('embeddings.txt', 'a') as f:
        f.write(json.dumps(embedding.tolist()) + '\n')
    # Ejemplo: [0.123, 0.456, ..., 0.789]
    
    # Guarda nombre en names.txt
    with open('names.txt', 'a') as f:
        f.write(nombre + '\n')
    # Ejemplo: Nacho
```

---

## ✅ Checklist: ¿Qué Pasó?

Al finalizar el registro:

- ✅ Imagen capturada
- ✅ Rostro detectado
- ✅ Embedding generado (128 números)
- ✅ Embedding guardado en `embeddings.txt`
- ✅ Nombre guardado en `names.txt`
- ✅ Estado cambiado a `ESPERANDO`
- ✅ LED azul sólido
- ✅ Mensaje publicado a la web
- ✅ Web muestra "Rostro registrado exitosamente"

---

## 🎓 Puntos Clave

1. **handle_registro() termina rápidamente**, solo configura estados y flags
2. **gpiozero monitorea en paralelo** usando threads internos
3. **on_boton_presionado() verifica el estado** antes de ejecutar
4. **iniciar_registro() hace el trabajo pesado**: captura, embedding, guardado
5. **save_embedding() crea dos archivos**: uno con vectores, otro con nombres
6. **La sincronización es crucial**: flags y locks evitan conflictos
7. **Todo es asincrónico**: web no bloquea esperando respuesta

