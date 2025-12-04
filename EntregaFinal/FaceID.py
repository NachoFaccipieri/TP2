import os
# Ajustes para Pi con poca RAM: limitar hilos y reducir logs de TF
# Deben establecerse antes de importar TensorFlow/keras para que tengan efecto
#os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
#os.environ.setdefault('OMP_NUM_THREADS', '1')
#os.environ.setdefault('MKL_NUM_THREADS', '1')
#os.environ.setdefault('INTRA_OP_NUM_THREADS', '1')
#os.environ.setdefault('INTER_OP_NUM_THREADS', '1')

import cv2      # <--- Para la cámara
import sys      # <--- Para salir limpiamente
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json
import os
import threading
import paho.mqtt.client as mqtt
import time
import io
import base64
import RPi.GPIO as GPIO
from enum import Enum

# Flask imports
from flask import Flask, send_from_directory, jsonify, Response, send_file
from flask_cors import CORS

# ============================================================================
# CONFIGURACIÓN GPIO - LED RGB, SERVO, BOTÓN
# ============================================================================
# LED RGB (Cátodo Común)
PIN_LED_ROJO = 17
PIN_LED_VERDE = 27
PIN_LED_AZUL = 22
# Servo
PIN_SERVO = 14
# Botón
PIN_BOTON = 21

# Configurar GPIO
try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Configurar LEDs como salida
    GPIO.setup(PIN_LED_ROJO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_LED_VERDE, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_LED_AZUL, GPIO.OUT, initial=GPIO.LOW)
    
    # Configurar servo PWM (50 Hz)
    GPIO.setup(PIN_SERVO, GPIO.OUT)
    servo_pwm = GPIO.PWM(PIN_SERVO, 50)
    servo_pwm.start(0)
    
    # Configurar botón como entrada con pull-up
    GPIO.setup(PIN_BOTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    GPIO_INITIALIZED = True
except Exception as e:
    print(f"Error al inicializar GPIO: {e}")
    GPIO_INITIALIZED = False

# ============================================================================
# MÁQUINA DE ESTADOS - LED
# ============================================================================
class LEDState(Enum):
    AMARILLO_TITILANTE = 1  # Startup/procesando registro
    AZUL_SOLIDO = 2          # Listo
    VERDE_10S = 3            # Acceso permitido (10 segundos)
    ROJO_10S = 4             # Acceso denegado (10 segundos)
    AMARILLO_SOLIDO = 5      # Procesando reconocimiento
    AZUL_TITILANTE = 6       # Registrando (titilante)

class ServoState(Enum):
    CERRADO = 0
    ABIERTO = 1

# ============================================================================
# MÁQUINA DE ESTADOS - APLICACIÓN
# ============================================================================
class AppState(Enum):
    INICIALIZANDO = 0
    ESPERANDO = 1
    PROCESANDO_RECONOCIMIENTO = 2
    ESPERANDO_CONFIRMACION = 3
    ESPERANDO_REGISTRO = 4
    REGISTRANDO = 5

# Variables globales de estado
current_app_state = AppState.INICIALIZANDO
current_led_state = LEDState.AMARILLO_TITILANTE
current_servo_state = ServoState.CERRADO
led_blink_thread = None
servo_open_timer = None
led_state_lock = threading.Lock()
app_state_lock = threading.Lock()
boton_presionado_flag = False
registro_solicitado_flag = False

# Config
BROKER = os.environ.get('MQTT_BROKER', 'localhost')
BROKER_PORT = int(os.environ.get('MQTT_PORT', '1883'))
TOPIC_REGISTRO = os.environ.get('TOPIC_REGISTRO', 'cerradura/registro')
TOPIC_TIMBRE = os.environ.get('TOPIC_TIMBRE', 'cerradura/timbre')
TOPIC_RESPUESTA = os.environ.get('TOPIC_RESPUESTA', 'cerradura/persona')
TOPIC_STATUS = os.environ.get('TOPIC_STATUS', 'cerradura/status')
TOPIC_CONFIRMACION = os.environ.get('TOPIC_CONFIRMACION', 'cerradura/confirmacion')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
EMBED_FILE = os.path.join(APP_ROOT, 'embeddings.txt')
NAMES_FILE = os.path.join(APP_ROOT, 'names.txt')

# Configuración Flask
app = Flask(__name__, static_folder=APP_ROOT, static_url_path='')
CORS(app)

# Variable global para almacenar la última imagen capturada
last_captured_image = None
last_image_lock = threading.Lock()
mqtt_client = None
last_recognized_person = None  # Almacena la última persona reconocida para la confirmación


print("Cargando MTCNN y FaceNet (TensorFlow)...")
try:
    detector = MTCNN()
    embedder = FaceNet()
    print("Modelos cargados.")
except Exception as e:
    print(f"Error al cargar modelos de TensorFlow: {e}")
    print("Esto probablemente sea un error de falta de memoria (RAM).")
    sys.exit(1)


# ============================================================================
# FUNCIONES DE CONTROL DE LED (Lógica Cátodo Común)
# HIGH = Enciende, LOW = Apaga
# ============================================================================
def apagar_todos_leds():
    """Apaga todos los LEDs"""
    if GPIO_INITIALIZED:
        GPIO.output(PIN_LED_ROJO, GPIO.LOW)
        GPIO.output(PIN_LED_VERDE, GPIO.LOW)
        GPIO.output(PIN_LED_AZUL, GPIO.LOW)

def set_led(rojo=False, verde=False, azul=False):
    """Establece el estado del LED RGB de forma directa"""
    if GPIO_INITIALIZED:
        GPIO.output(PIN_LED_ROJO, GPIO.HIGH if rojo else GPIO.LOW)
        GPIO.output(PIN_LED_VERDE, GPIO.HIGH if verde else GPIO.LOW)
        GPIO.output(PIN_LED_AZUL, GPIO.HIGH if azul else GPIO.LOW)

def cambiar_estado_led(nuevo_estado):
    """Cambia el estado del LED según la máquina de estados"""
    global current_led_state, led_blink_thread
    
    with led_state_lock:
        if current_led_state == nuevo_estado:
            return  # Ya está en ese estado
        
        # Detener hilo de parpadeo anterior si existe
        current_led_state = nuevo_estado
        
        if nuevo_estado == LEDState.AZUL_SOLIDO:
            apagar_todos_leds()
            set_led(azul=True)
            print("[LED] Estado: AZUL SOLIDO")
            
        elif nuevo_estado == LEDState.AMARILLO_TITILANTE:
            # Amarillo = Rojo + Verde
            if led_blink_thread:
                # Esperar a que termine el hilo anterior
                pass
            led_blink_thread = threading.Thread(target=_led_parpadeo, args=(0.5, 'amarillo'), daemon=True)
            led_blink_thread.start()
            print("[LED] Estado: AMARILLO TITILANTE")
            
        elif nuevo_estado == LEDState.VERDE_10S:
            apagar_todos_leds()
            set_led(verde=True)
            print("[LED] Estado: VERDE 10 segundos")
            # Programar vuelta a azul después de 10 segundos
            threading.Timer(10.0, lambda: cambiar_estado_led(LEDState.AZUL_SOLIDO)).start()
            
        elif nuevo_estado == LEDState.ROJO_10S:
            apagar_todos_leds()
            set_led(rojo=True)
            print("[LED] Estado: ROJO 10 segundos")
            # Programar vuelta a azul después de 10 segundos
            threading.Timer(10.0, lambda: cambiar_estado_led(LEDState.AZUL_SOLIDO)).start()
            
        elif nuevo_estado == LEDState.AMARILLO_SOLIDO:
            apagar_todos_leds()
            set_led(rojo=True, verde=True)  # Amarillo = Rojo + Verde
            print("[LED] Estado: AMARILLO SOLIDO")
            
        elif nuevo_estado == LEDState.AZUL_TITILANTE:
            if led_blink_thread:
                pass
            led_blink_thread = threading.Thread(target=_led_parpadeo, args=(0.5, 'azul'), daemon=True)
            led_blink_thread.start()
            print("[LED] Estado: AZUL TITILANTE")

def _led_parpadeo(intervalo, color):
    """Parpadea el LED del color especificado"""
    rojo = color == 'amarillo'
    verde = color == 'amarillo'
    azul = color == 'azul'
    
    # Parpadeo continuo hasta que cambie el estado
    while True:
        with led_state_lock:
            # Comprobar si deberíamos seguir parpadeando
            estado_actual = current_led_state
        
        if estado_actual not in [LEDState.AMARILLO_TITILANTE, LEDState.AZUL_TITILANTE]:
            break  # Salir si el estado cambió
        
        set_led(rojo, verde, azul)
        time.sleep(intervalo)
        apagar_todos_leds()
        time.sleep(intervalo)

# ============================================================================
# FUNCIONES DE CONTROL DE SERVO
# ============================================================================
def set_servo_angle(angle):
    """Establece el ángulo del servo (0-180 grados)"""
    if not GPIO_INITIALIZED:
        return
    
    angle = max(0, min(180, angle))  # Limitar a 0-180
    # Mapear 0-180° a 5-10% duty cycle
    duty = 5 + (angle / 180) * 5
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)  # Detener PWM continuo

def abrir_puerta():
    """Abre la puerta (servo 90 grados) por 10 segundos"""
    global current_servo_state, servo_open_timer
    
    if not GPIO_INITIALIZED:
        return
    
    print("[SERVO] Abriendo puerta...")
    current_servo_state = ServoState.ABIERTO
    set_servo_angle(90)  # 90 grados = abierto
    
    # Cancelar timer anterior si existe
    if servo_open_timer:
        servo_open_timer.cancel()
    
    # Programar cierre después de 10 segundos
    servo_open_timer = threading.Timer(10.0, cerrar_puerta)
    servo_open_timer.start()

def cerrar_puerta():
    """Cierra la puerta (servo 0 grados)"""
    global current_servo_state, servo_open_timer
    
    if not GPIO_INITIALIZED:
        return
    
    print("[SERVO] Cerrando puerta...")
    current_servo_state = ServoState.CERRADO
    set_servo_angle(0)  # 0 grados = cerrado
    servo_open_timer = None

# ============================================================================
# FUNCIONES DE CONTROL DE BOTÓN
# ============================================================================
def on_boton_presionado(channel):
    """Callback cuando se presiona el botón"""
    global boton_presionado_flag
    
    print("[BOTON] Botón presionado")
    boton_presionado_flag = True
    
    with app_state_lock:
        estado_actual = current_app_state
    
    # Lógica según el estado actual
    if estado_actual == AppState.ESPERANDO:
        # Inicia reconocimiento
        print("[BOTON] Iniciando reconocimiento...")
        iniciar_reconocimiento()
    
    elif estado_actual == AppState.ESPERANDO_REGISTRO:
        # Inicia registro
        print("[BOTON] Iniciando registro...")
        iniciar_registro()

def setup_boton():
    """Configura el evento del botón"""
    if GPIO_INITIALIZED:
        # Usar edge detection para detectar presión (caída de flanco)
        GPIO.add_event_detect(PIN_BOTON, GPIO.FALLING, callback=on_boton_presionado, bouncetime=200)
        print("[BOTON] Botón configurado en GPIO", PIN_BOTON)

def get_embedding_from_pil(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.asarray(img)

    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None

    # Tomar el primer rostro detectado
    x, y, w, h = detections[0]['box']
    x, y = abs(x), abs(y) # Asegurar que no sean negativos
    face = img_array[y:y+h, x:x+w]

    print("Generando embedding...")
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)
    embedding = embedder.embeddings(face)[0]
    # Normalización L2
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding


def cambiar_estado_app(nuevo_estado):
    """Cambia el estado de la aplicación"""
    global current_app_state
    
    with app_state_lock:
        if current_app_state != nuevo_estado:
            print(f"[APP STATE] {current_app_state.name} -> {nuevo_estado.name}")
            current_app_state = nuevo_estado

def iniciar_reconocimiento():
    """Inicia el proceso de reconocimiento desde el botón físico"""
    global mqtt_client
    
    cambiar_estado_app(AppState.PROCESANDO_RECONOCIMIENTO)
    cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
    
    if mqtt_client:
        mqtt_client.publish(TOPIC_TIMBRE, 'ping')

def iniciar_registro():
    """Inicia el proceso de registro desde el botón físico"""
    global mqtt_client, registro_solicitado_flag
    
    if not registro_solicitado_flag:
        print("[APP] No hay registro solicitado, ignorando presión de botón")
        return
    
    cambiar_estado_app(AppState.REGISTRANDO)
    cambiar_estado_led(LEDState.AZUL_TITILANTE)
    
    if mqtt_client:
        # El nombre debería haberse solicitado desde la web
        # Aquí simplemente publicamos el evento para que comience el registro
        mqtt_client.publish(TOPIC_REGISTRO, 'registrando_desde_boton')

def load_embeddings(file_path=EMBED_FILE, names_path=NAMES_FILE):
    embeddings = []
    names = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    vec = json.loads(line)
                    embeddings.append(np.array(vec))
                except Exception:
                    continue
    if os.path.exists(names_path):
        with open(names_path, 'r', encoding='utf-8') as f:
            for line in f:
                names.append(line.strip())
    return embeddings, names


def save_embedding(embedding, nombre, file_path=EMBED_FILE, names_path=NAMES_FILE):
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(embedding.tolist()) + '\n')
    with open(names_path, 'a', encoding='utf-8') as f:
        f.write(nombre + '\n')


def capture_frame(camera_index=0, save_last=True):
    """Captura un frame de la cámara y opcionalmente lo guarda como última imagen"""
    global last_captured_image
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None, 'No se pudo abrir la cámara'
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None, 'No se pudo capturar el frame'
    
    # Guardar copia del frame original (BGR para OpenCV)
    if save_last:
        with last_image_lock:
            last_captured_image = frame.copy()
    
    # Convertir a RGB para procesamiento facial
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    return img, None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f'[MQTT] Conectado al broker MQTT {BROKER}:{BROKER_PORT}')
        client.subscribe(TOPIC_REGISTRO)
        client.subscribe(TOPIC_TIMBRE)
        client.subscribe(TOPIC_CONFIRMACION)
        
        # Indicar que estamos listos
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        client.publish(TOPIC_STATUS, 'servicio-listo')
    else:
        print(f'[MQTT] Error al conectar al broker MQTT, rc={rc}')


def handle_registro(client, payload):
    """Maneja el evento de registro de nuevo rostro"""
    global registro_solicitado_flag
    
    # payload puede ser JSON {'nombre': 'Mati'} o solo un nombre
    nombre = None
    try:
        data = json.loads(payload)
        nombre = data.get('nombre')
    except Exception:
        nombre = payload.decode() if isinstance(payload, bytes) else str(payload)

    if not nombre or nombre == 'registrando_desde_boton':
        # El nombre se solicita desde web, aquí solo marcamos que se solicita
        print("[REGISTRO] Esperando presión de botón para capturar...")
        registro_solicitado_flag = True
        cambiar_estado_app(AppState.ESPERANDO_REGISTRO)
        cambiar_estado_led(LEDState.AZUL_TITILANTE)
        client.publish(TOPIC_STATUS, 'Presiona el botón físico para registrar nuevo rostro')
        return

    print(f"[REGISTRO] Registrando rostro para: {nombre}")
    cambiar_estado_app(AppState.REGISTRANDO)
    cambiar_estado_led(LEDState.AZUL_TITILANTE)
    
    client.publish(TOPIC_STATUS, f'Registrando rostro: {nombre}')
    img, err = capture_frame()
    if err:
        client.publish(TOPIC_STATUS, f'Error captura: {err}')
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': err}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        registro_solicitado_flag = False
        return

    embedding = get_embedding_from_pil(img)
    if embedding is None:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': 'No se detectó rostro'}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        registro_solicitado_flag = False
        return

    try:
        save_embedding(embedding, nombre)
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': f'Rostro {nombre} registrado'}))
        print(f'[REGISTRO] Rostro {nombre} registrado exitosamente')
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
    except Exception as e:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': f'Error al guardar: {e}'}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
    
    registro_solicitado_flag = False


def handle_timbre(client):
    """Maneja el evento del timbre (reconocimiento de rostro)"""
    global last_recognized_person
    
    print("[TIMBRE] Procesando reconocimiento...")
    cambiar_estado_app(AppState.PROCESANDO_RECONOCIMIENTO)
    cambiar_estado_led(LEDState.AMARILLO_SOLIDO)
    
    client.publish(TOPIC_STATUS, 'Evento timbre recibido: capturando')
    img, err = capture_frame()
    if err:
        print(f"[TIMBRE] Error de captura: {err}")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': err, 'coincidencia': False}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return

    embedding = get_embedding_from_pil(img)
    if embedding is None:
        print("[TIMBRE] No se detectó rostro")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No se detectó rostro', 'coincidencia': False}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return

    stored_embeddings, names = load_embeddings()
    if not stored_embeddings:
        print("[TIMBRE] No hay rostros registrados")
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No hay rostros registrados', 'coincidencia': False}))
        cambiar_estado_app(AppState.ESPERANDO)
        cambiar_estado_led(LEDState.AZUL_SOLIDO)
        return

    distancias = [float(np.linalg.norm(embedding - emb)) for emb in stored_embeddings]
    min_dist = min(distancias)
    idx = int(np.argmin(distancias))
    umbral = 0.8  # Umbral de distancia para coincidencia

    # Cambiar a estado esperando confirmación
    cambiar_estado_app(AppState.ESPERANDO_CONFIRMACION)

    if min_dist < umbral:
        nombre = names[idx] if idx < len(names) else f'Persona #{idx+1}'
        print(f'[TIMBRE] Coincidencia: {nombre} (distancia {min_dist:.4f})')
        last_recognized_person = {'nombre': nombre, 'distancia': min_dist}
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
        client.publish(TOPIC_RESPUESTA, json.dumps({
            'ok': True,
            'mensaje': 'No coincide con la base',
            'coincidencia': False,
            'distancia': min_dist
        }))


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
        client.publish(TOPIC_STATUS, '✅ Acceso permitido - Puerta abierta 10 segundos')
    else:
        print("[CONFIRMACION] Acceso DENEGADO")
        cambiar_estado_led(LEDState.ROJO_10S)
        client.publish(TOPIC_STATUS, '❌ Acceso denegado')
    
    cambiar_estado_app(AppState.ESPERANDO)

def on_message(client, userdata, msg):
    print(f'[MQTT] Mensaje en topic {msg.topic}: {msg.payload}')
    try:
        if msg.topic == TOPIC_REGISTRO:
            # manejar en hilo para no bloquear loop mqtt
            threading.Thread(target=handle_registro, args=(client, msg.payload)).start()
        elif msg.topic == TOPIC_TIMBRE:
            threading.Thread(target=handle_timbre, args=(client,)).start()
        elif msg.topic == TOPIC_CONFIRMACION:
            threading.Thread(target=handle_confirmacion, args=(client, msg.payload)).start()
        else:
            print(f'[MQTT] Topic no manejado: {msg.topic}')
    except Exception as e:
        print(f'[MQTT] Error al procesar mensaje: {e}')


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
        client.loop_forever()
    except KeyboardInterrupt:
        print('Interrumpido por teclado, saliendo...')


# --------------------------------------------------
# Rutas Flask
# --------------------------------------------------
@app.route('/')
def index():
    """Servir index.html"""
    return send_from_directory(APP_ROOT, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos (CSS, JS, etc)"""
    return send_from_directory(APP_ROOT, filename)

@app.route('/api/status')
def api_status():
    """Endpoint de estado del sistema"""
    return jsonify({
        'status': 'ok',
        'mqtt_broker': BROKER,
        'mqtt_port': BROKER_PORT,
        'has_image': last_captured_image is not None
    })

@app.route('/api/camera/snapshot')
def camera_snapshot():
    """Captura y devuelve una imagen de la cámara en tiempo real"""
    img, err = capture_frame(save_last=True)
    if err:
        return jsonify({'error': err}), 500
    
    with last_image_lock:
        if last_captured_image is None:
            return jsonify({'error': 'No hay imagen disponible'}), 404
        
        # Convertir a JPEG
        ret, buffer = cv2.imencode('.jpg', last_captured_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            return jsonify({'error': 'Error al codificar imagen'}), 500
        
        return Response(buffer.tobytes(), mimetype='image/jpeg')

@app.route('/api/camera/last')
def get_last_image():
    """Devuelve la última imagen capturada"""
    with last_image_lock:
        if last_captured_image is None:
            return jsonify({'error': 'No hay imagen disponible'}), 404
        
        # Convertir a JPEG
        ret, buffer = cv2.imencode('.jpg', last_captured_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            return jsonify({'error': 'Error al codificar imagen'}), 500
        
        return Response(buffer.tobytes(), mimetype='image/jpeg')

@app.route('/api/camera/last_base64')
def get_last_image_base64():
    """Devuelve la última imagen en formato base64 (útil para MQTT)"""
    with last_image_lock:
        if last_captured_image is None:
            return jsonify({'error': 'No hay imagen disponible'}), 404
        
        # Convertir a JPEG y luego a base64
        ret, buffer = cv2.imencode('.jpg', last_captured_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            return jsonify({'error': 'Error al codificar imagen'}), 500
        
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({
            'image': img_base64,
            'timestamp': time.time()
        })


# --------------------------------------------------
# Función para iniciar MQTT en hilo separado
# --------------------------------------------------
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
    mqtt_client.loop_forever()


def main_flask():
    print('[APP] Servicio de reconocimiento iniciando...')
    
    # Inicializar barrera en posición cerrada
    if GPIO_INITIALIZED:
        cerrar_puerta()
    
    # Configurar botón físico
    setup_boton()
    
    # Iniciar MQTT en hilo separado
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Esperar un momento para que MQTT se conecte
    time.sleep(2)
    
    # Iniciar Flask (bloquea el hilo principal)
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', '5000'))
    
    print(f'[APP] Iniciando servidor Flask en http://{FLASK_HOST}:{FLASK_PORT}')
    print(f'[APP] Accede a la interfaz web desde: http://<IP_RASPBERRY>:{FLASK_PORT}')
    print('[APP] Sistema listo - esperando eventos...')
    
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print('[APP] Interrumpido por teclado, saliendo...')
        if GPIO_INITIALIZED:
            GPIO.cleanup()
        sys.exit(0)


if __name__ == '__main__':
    # Usar Flask por defecto
    use_flask = os.environ.get('USE_FLASK', '1') == '1'
    if use_flask:
        main_flask()
    else:
        print('Servicio de reconocimiento listo. Esperando comandos MQTT...')
        main()