# Sistema de Control de Acceso con Reconocimiento Facial

Sistema de cerradura inteligente con reconocimiento facial usando Raspberry Pi, MQTT y Flask.

## 🚀 Inicio Rápido (Desarrollo en PC)

### Requisitos
- Python 3.8+
- Docker Desktop (para el broker MQTT)
- Webcam USB

### Instalación

1. **Instalar dependencias de Python:**
```bash
pip install -r requeriments.txt
```

2. **Iniciar el sistema:**
```bash
start.bat
```

Esto iniciará:
- Broker MQTT Mosquitto (puertos 1883 y 9001)
- Servidor Flask (puerto 5000)

3. **Acceder a la interfaz web:**
```
http://localhost:5000
```

4. **Detener el sistema:**
```bash
stop.bat
```
O presiona `Ctrl+C` en la terminal de Flask y luego ejecuta `stop.bat`

---

## 📡 Arquitectura

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Navegador     │◄────────┤  Mosquitto MQTT  ├────────►│  comprobarRostro│
│   (Web UI)      │  WS:9001│   (Broker)       │ TCP:1883│   (Python)      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
         │                                                        │
         │                   ┌──────────────────┐                │
         └──────────────────►│   Flask Server   │◄───────────────┘
                   HTTP:5000 │  (Static Files)  │
                             └──────────────────┘
```

### Flujo de Comunicación

1. **Registro de rostro:**
   - Web → MQTT `cerradura/registro` → Python
   - Python captura foto, genera embedding, guarda
   - Python → MQTT `cerradura/persona` → Web (confirmación)

2. **Timbre (reconocimiento):**
   - Botón físico/Web → MQTT `cerradura/timbre` → Python
   - Python captura foto, compara con base de datos
   - Python → MQTT `cerradura/persona` → Web (muestra quién es)

3. **Confirmación de acceso:**
   - Web → MQTT `cerradura/confirmacion` → Python
   - Python enciende LED verde (permitir) o rojo (denegar)

---

## 🔧 Topics MQTT

| Topic | Dirección | Payload | Descripción |
|-------|-----------|---------|-------------|
| `cerradura/registro` | Web → Pi | `{"nombre": "Juan"}` | Registrar nuevo rostro |
| `cerradura/timbre` | Botón/Web → Pi | `"ping"` | Iniciar reconocimiento |
| `cerradura/persona` | Pi → Web | `{"coincidencia": true, "nombre": "Juan", "distancia": 0.5}` | Resultado del reconocimiento |
| `cerradura/confirmacion` | Web → Pi | `{"permitir": true/false}` | Permitir o denegar acceso |
| `cerradura/status` | Pi → Web | `"texto"` | Mensajes de estado |

---

## 🔌 Configuración GPIO (Raspberry Pi)

| Pin GPIO | Función | Descripción |
|----------|---------|-------------|
| GPIO 17 | LED Rojo | Acceso denegado |
| GPIO 27 | LED Verde | Acceso permitido |
| GPIO 22 | LED Azul | (Reservado) |
| GPIO 23 | Botón/Pulsador | Timbre físico |

**Nota:** En PC de desarrollo, el GPIO está mockeado y no hace nada.

---

## 🌐 Variables de Entorno

Puedes personalizar el comportamiento con variables de entorno:

```bash
# MQTT
MQTT_BROKER=localhost          # IP del broker MQTT
MQTT_PORT=1883                 # Puerto MQTT estándar
MQTT_USER=usuario              # Usuario MQTT (opcional)
MQTT_PASS=contraseña          # Contraseña MQTT (opcional)

# Flask
FLASK_HOST=0.0.0.0            # IP del servidor Flask
FLASK_PORT=5000               # Puerto del servidor Flask

# GPIO
LED_R_PIN=17                  # Pin LED rojo
LED_G_PIN=27                  # Pin LED verde
LED_B_PIN=22                  # Pin LED azul
BUTTON_PIN=23                 # Pin del botón

# Archivos
EMBED_FILE=./embeddings.txt   # Archivo de embeddings
NAMES_FILE=./names.txt        # Archivo de nombres
```

Ejemplo de uso:
```bash
set MQTT_BROKER=192.168.1.100
set FLASK_PORT=8080
python comprobarRostro.py
```

---

## 🥧 Despliegue en Raspberry Pi

Ver documentación detallada en:
- [`docs/README_MQTT_NGINX.md`](docs/README_MQTT_NGINX.md) - Configuración MQTT y Nginx
- [`docs/TESTING_AND_AP.md`](docs/TESTING_AND_AP.md) - Configurar Access Point
- [`docs/pi_optimizations.md`](docs/pi_optimizations.md) - Optimizaciones de memoria

### Resumen rápido:

1. **Instalar Mosquitto en la Pi:**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo cp mosquitto/config/mosquitto.conf /etc/mosquitto/conf.d/
sudo systemctl restart mosquitto
```

2. **Instalar dependencias Python:**
```bash
pip3 install -r requeriments.txt
```

3. **Crear servicio systemd:**
```bash
sudo cp docs/systemd_comprobarrostro.service /etc/systemd/system/cerradura.service
sudo systemctl enable cerradura
sudo systemctl start cerradura
```

4. **Acceder desde móvil:**
```
http://<IP_RASPBERRY>:5000
```

---

## 🧪 Pruebas Locales

### 1. Probar MQTT manualmente

Terminal 1 (suscriptor):
```bash
mosquitto_sub -h localhost -t "cerradura/#" -v
```

Terminal 2 (publicador):
```bash
mosquitto_pub -h localhost -t "cerradura/timbre" -m "test"
```

### 2. Simular timbre desde teclado

Cuando `comprobarRostro.py` está corriendo, presiona `t` + Enter en la terminal para simular el timbre.

### 3. Verificar Flask

```bash
curl http://localhost:5000/api/status
```

Debería devolver:
```json
{
  "status": "ok",
  "mqtt_broker": "localhost",
  "mqtt_port": 1883,
  "is_rpi": false
}
```

---

## 📝 Solución de Problemas

### Error: "No module named 'cv2'"
```bash
pip install opencv-python
```

### Error: "Conexión MQTT cerrada"
Verifica que Mosquitto esté corriendo:
```bash
docker ps
```
Deberías ver un contenedor `eclipse-mosquitto` activo.

### Error: "No se pudo abrir la cámara"
Verifica que la webcam esté conectada:
```bash
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### La web dice "Conexión MQTT cerrada"
1. Verifica que Mosquitto esté corriendo con WebSockets (puerto 9001)
2. Abre la consola del navegador (F12) para ver errores
3. Verifica el firewall de Windows

---

## 📂 Estructura del Proyecto

```
ProyectoFlask/
├── comprobarRostro.py          # Script principal (Flask + MQTT + Reconocimiento)
├── index.html                  # Interfaz web
├── script.js                   # Lógica MQTT WebSocket
├── style.css                   # Estilos
├── embeddings.txt              # Base de datos de embeddings faciales
├── names.txt                   # Nombres correspondientes
├── docker-compose.yml          # Configuración Docker para Mosquitto
├── start.bat                   # Script de inicio (Windows)
├── stop.bat                    # Script de parada (Windows)
├── requeriments.txt            # Dependencias Python
├── mosquitto/
│   └── config/
│       └── mosquitto.conf      # Configuración Mosquitto
└── docs/                       # Documentación adicional
```

---

## 🤝 Contribuir

Este es un proyecto educativo. Sugerencias y mejoras son bienvenidas.

## 📄 Licencia

MIT
