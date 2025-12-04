# Diagramas de Máquinas de Estados

## 📊 Máquina de Estados de la Aplicación

```
                    ┌─────────────────────────────────────────┐
                    │      INICIALIZANDO                      │
                    │  (LED: AMARILLO TITILANTE)             │
                    │  Esperando conexión MQTT...            │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │      ESPERANDO                          │
                    │  (LED: AZUL SOLIDO)                    │
                    │  Sistema listo                         │
                    └────┬──────────────────────┬─────────────┘
                         │                      │
            ┌────────────▼────┐      ┌─────────▼──────────────┐
            │ BOTON PRESIONADO │      │ REGISTRO SOLICITADO  │
            │ desde WEB o      │      │ desde WEB            │
            │ FISICO           │      │                      │
            └────────────┬─────┘      └─────────┬────────────┘
                         │                      │
        ┌────────────────▼─────────┐  ┌─────────▼──────────────────┐
        │ PROCESANDO RECONOCIMIENTO │  │ ESPERANDO REGISTRO         │
        │ (LED: AMARILLO SOLIDO)   │  │ (LED: AZUL TITILANTE)     │
        │ • Captura foto           │  │ Esperando presión botón    │
        │ • Compara embeddings     │  │ físico                     │
        └────────────┬─────────────┘  └─────────┬──────────────────┘
                     │                          │
         ┌───────────▼────────────┐    ┌────────▼─────────────────┐
         │ ESPERANDO CONFIRMACION │    │ REGISTRANDO              │
         │ (LED: AMARILLO SOLIDO) │    │ (LED: AZUL TITILANTE)   │
         │ Enviado resultado web  │    │ • Captura foto           │
         │ • Si coincidencia      │    │ • Genera embedding       │
         │ • Si no coincidencia   │    │ • Guarda en BD           │
         └───┬──────────────┬─────┘    └────────┬──────────────────┘
             │              │                   │
    ┌────────▼──┐  ┌───────▼───┐    ┌──────────▼────────┐
    │PERMITIR   │  │ DENEGAR   │    │ Completado       │
    │LED:VERDE  │  │ LED:ROJO  │    │ LED:AZUL SOLIDO │
    │10 segundos│  │ 10 segs   │    └──────────┬────────┘
    │SERVO:ABRE │  │ SERVO:--- │              │
    └────┬──────┘  └───┬───────┘              │
         │             │                      │
         │         ┌───▼─────────────────────▼─┐
         │         │   ESPERANDO                │
         │         │   (LED: AZUL SOLIDO)      │
         └────────▶│   Sistema listo           │◀─────┘
                   └───────────────────────────┘
```

## 🔄 Máquina de Estados del LED

```
┌─────────────────────────────────────────────────────────────────┐
│                     LED RGB (Cátodo Común)                     │
└─────────────────────────────────────────────────────────────────┘

ESTADOS:

🟡 AMARILLO_TITILANTE (inicio)
   ├─ Frecuencia: 500ms ON / 500ms OFF
   ├─ Pines: ROJO + VERDE
   └─ Transición: → AZUL_SOLIDO (conexión MQTT OK)

🔵 AZUL_SOLIDO (listo)
   ├─ Constante encendido
   ├─ Pines: AZUL
   ├─ Transición 1: → AMARILLO_SOLIDO (procesando reconocimiento)
   ├─ Transición 2: → AZUL_TITILANTE (registro solicitado)
   ├─ Transición 3: → VERDE_10S (acceso permitido)
   └─ Transición 4: → ROJO_10S (acceso denegado)

🟡 AMARILLO_SOLIDO (procesando)
   ├─ Constante encendido
   ├─ Pines: ROJO + VERDE
   └─ Transición: → AZUL_SOLIDO (reconocimiento completo)

🟢 VERDE_10S (acceso permitido)
   ├─ Constante encendido 10 segundos
   ├─ Pines: VERDE
   ├─ Timer: 10 segundos
   └─ Transición: → AZUL_SOLIDO (timer expirado)

🔴 ROJO_10S (acceso denegado)
   ├─ Constante encendido 10 segundos
   ├─ Pines: ROJO
   ├─ Timer: 10 segundos
   └─ Transición: → AZUL_SOLIDO (timer expirado)

🔵 AZUL_TITILANTE (registrando)
   ├─ Frecuencia: 500ms ON / 500ms OFF
   ├─ Pines: AZUL
   └─ Transición: → AMARILLO_SOLIDO (botón presionado para capturar)
```

## 🎛️ Máquina de Estados del Servo

```
┌─────────────────────────────────────────────────────────────────┐
│                     SERVO (GPIO 14 - PWM)                      │
└─────────────────────────────────────────────────────────────────┘

ESTADOS:

🔒 CERRADO (0°)
   ├─ Duty Cycle: 5%
   ├─ Posición: Completamente cerrado
   ├─ Estado por defecto
   └─ Transición: → ABIERTO (acceso permitido desde web)

🔓 ABIERTO (90°)
   ├─ Duty Cycle: 7.5%
   ├─ Posición: Completamente abierto
   ├─ Duración: 10 segundos máximo
   ├─ Timer: 10 segundos
   └─ Transición: → CERRADO (timer expirado o comando manual)

COMPORTAMIENTO:
• Inicio del programa: Servo se coloca en CERRADO
• Tras recibir "permitir": Servo se coloca en ABIERTO
• Después de 10 segundos: Servo vuelve a CERRADO automáticamente
```

## 🔘 Máquina de Estados del Botón

```
┌─────────────────────────────────────────────────────────────────┐
│                    BOTÓN (GPIO 21 - Pull-Up)                   │
└─────────────────────────────────────────────────────────────────┘

DETECCIÓN:
├─ Tipo: Edge detection (FALLING)
├─ Debounce: 200ms
├─ Pull-up interno: Activado

EVENTOS:

Cuando AppState = ESPERANDO
└─ Presión botón: Envía comando timbre
   ├─ Inicia reconocimiento
   ├─ Captura foto
   └─ Compara embeddings

Cuando AppState = ESPERANDO_REGISTRO
└─ Presión botón: Captura para registro
   ├─ Inicia captura de nuevo rostro
   ├─ Genera embedding
   └─ Guarda en base de datos

En otros estados:
└─ Presión botón: IGNORADA
   (seguridad: evita acciones no permitidas)
```

## 🔗 Interacciones MQTT

```
┌──────────────────────────────────────────────────────────────────┐
│                      FLUJO MQTT                                 │
└──────────────────────────────────────────────────────────────────┘

PUBLICACIÓN (Raspberry → Broker):
├─ TOPIC_STATUS ("cerradura/status")
│  └─ Mensajes: estado general del sistema
│
├─ TOPIC_RESPUESTA ("cerradura/persona")
│  └─ Payload: {
│      "ok": true/false,
│      "coincidencia": true/false,
│      "nombre": "...",
│      "distancia": 0.xxx,
│      "mensaje": "..."
│     }
│
└─ TOPIC_TIMBRE ("cerradura/timbre")
   └─ Usado solo cuando se inicia desde Raspberry


SUSCRIPCIÓN (Broker → Raspberry):
├─ TOPIC_REGISTRO ("cerradura/registro")
│  ├─ Payload: {"nombre": "Nacho"}
│  └─ Espera presión de botón físico para capturar
│
├─ TOPIC_TIMBRE ("cerradura/timbre")
│  ├─ Payload: "ping"
│  └─ Inicia reconocimiento
│
└─ TOPIC_CONFIRMACION ("cerradura/confirmacion")
   ├─ Payload: {"permitir": true/false}
   └─ Respuesta del usuario en web (aceptar/denegar)
```

## 🎯 Flujos de Caso de Uso

### Caso 1: Reconocimiento desde Botón Físico
```
Usuario presiona botón físico
        │
        ▼
[APP] ESPERANDO → PROCESANDO_RECONOCIMIENTO
[LED] AZUL_SOLIDO → AMARILLO_SOLIDO
        │
        ├─ Captura foto
        ├─ Compara con embeddings
        └─ Envía resultado a web
        │
        ▼
[APP] ESPERANDO_CONFIRMACION
[STATUS] "Esperando confirmación..."
        │
        ├─ Usuario presiona PERMITIR en web
        │  ├─ [LED] VERDE_10S
        │  ├─ [SERVO] ABIERTO por 10s
        │  └─ Después: [LED] AZUL_SOLIDO, [SERVO] CERRADO
        │
        └─ Usuario presiona DENEGAR en web
           ├─ [LED] ROJO_10S
           ├─ [SERVO] CERRADO
           └─ Después: [LED] AZUL_SOLIDO
        │
        ▼
[APP] ESPERANDO
```

### Caso 2: Registro de Nuevo Rostro
```
Usuario hace clic "Registrar nuevo rostro"
        │
        ▼
Ingresa nombre de persona
        │
        ▼
[APP] ESPERANDO_REGISTRO
[LED] AZUL_TITILANTE
[STATUS] "Presiona botón físico para registrar"
        │
        ├─ Usuario presiona botón físico
        │
        ▼
[APP] REGISTRANDO
[LED] AMARILLO_SOLIDO (durante captura)
        │
        ├─ Captura foto
        ├─ Genera embedding
        ├─ Guarda en embeddings.txt y names.txt
        │
        ▼
[APP] ESPERANDO
[LED] AZUL_SOLIDO
[STATUS] "Rostro registrado exitosamente"
```

### Caso 3: Sin Coincidencia
```
Usuario presiona botón físico
        │
        ▼
[APP] PROCESANDO_RECONOCIMIENTO
[LED] AMARILLO_SOLIDO
        │
        ├─ Captura foto
        ├─ Compara con embeddings
        ├─ Distancia NO es menor a 0.8
        │
        ▼
[APP] ESPERANDO_CONFIRMACION
[STATUS] "❌ No se encontró coincidencia"
        │
        ├─ Sistema espera 30s o usuario presiona botón nuevamente
        │
        ▼
[APP] ESPERANDO
[LED] AZUL_SOLIDO
```
