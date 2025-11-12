import os
# Ajustes para Pi con poca RAM
#if os.environ.get('RPI_LOW_RAM', '1') == '1':
#    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
#    os.environ.setdefault('OMP_NUM_THREADS', '1')
#    os.environ.setdefault('MKL_NUM_THREADS', '1')
#    os.environ.setdefault('INTRA_OP_NUM_THREADS', '1')
#    os.environ.setdefault('INTER_OP_NUM_THREADS', '1')

import cv2
import sys
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json
import threading
import paho.mqtt.client as mqtt
import time

# Flask imports
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Intento importar RPi.GPIO; si falla (PC dev), uso un mock mínimo
try:
    import RPi.GPIO as GPIO
    IS_RPI = True
except Exception:
    IS_RPI = False
    class MockGPIO:
        BCM = None
        OUT = IN = None
        PUD_DOWN = None
        def setmode(self, *_):
            pass
        def setup(self, *_):
            pass
        def output(self, *_):
            pass
        def input(self, *_):
            return 0
        def PWM(self, *_):
            class P:
                def start(self, *_):
                    pass
                def ChangeDutyCycle(self, *_):
                    pass
                def stop(self):
                    pass
            return P()
        def cleanup(self):
            pass
    GPIO = MockGPIO()

# --------------------------------------------------
# Configuración MQTT
# --------------------------------------------------
BROKER = os.environ.get('MQTT_BROKER', 'localhost')
BROKER_PORT = int(os.environ.get('MQTT_PORT', '1883'))
TOPIC_REGISTRO = os.environ.get('TOPIC_REGISTRO', 'cerradura/registro')
TOPIC_TIMBRE = os.environ.get('TOPIC_TIMBRE', 'cerradura/timbre')
TOPIC_RESPUESTA = os.environ.get('TOPIC_RESPUESTA', 'cerradura/persona')
TOPIC_STATUS = os.environ.get('TOPIC_STATUS', 'cerradura/status')
TOPIC_CONFIRM = os.environ.get('TOPIC_CONFIRM', 'cerradura/confirmacion')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
EMBED_FILE = os.environ.get('EMBED_FILE', os.path.join(APP_ROOT, 'embeddings.txt'))
NAMES_FILE = os.environ.get('NAMES_FILE', os.path.join(APP_ROOT, 'names.txt'))

# Crear archivos si no existen
try:
    embed_dir = os.path.dirname(EMBED_FILE) or APP_ROOT
    names_dir = os.path.dirname(NAMES_FILE) or APP_ROOT
    os.makedirs(embed_dir, exist_ok=True)
    os.makedirs(names_dir, exist_ok=True)
    open(EMBED_FILE, 'a', encoding='utf-8').close()
    open(NAMES_FILE, 'a', encoding='utf-8').close()
    try:
        os.chmod(EMBED_FILE, 0o664)
        os.chmod(NAMES_FILE, 0o664)
    except Exception:
        pass
except Exception as e:
    print('Advertencia: no se pudo crear archivos de embeddings/nombres:', e)

# --------------------------------------------------
# Inicializar Flask
# --------------------------------------------------
app = Flask(__name__, static_folder=APP_ROOT, static_url_path='')
CORS(app)  # Permitir CORS para WebSockets MQTT

# Variable global para el cliente MQTT (se inicializará en main)
mqtt_client = None

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
    """Endpoint de prueba para verificar que Flask está funcionando"""
    return jsonify({
        'status': 'ok',
        'mqtt_broker': BROKER,
        'mqtt_port': BROKER_PORT,
        'is_rpi': IS_RPI
    })

# --------------------------------------------------
# Cargar modelos TensorFlow
# --------------------------------------------------
print("Cargando MTCNN y FaceNet (TensorFlow)...")
try:
    detector = MTCNN()
    embedder = FaceNet()
    print("Modelos cargados.")
except Exception as e:
    print(f"Error al cargar modelos de TensorFlow: {e}")
    print("Esto probablemente sea un error de falta de memoria (RAM).")
    sys.exit(1)

# --------------------------------------------------
# Funciones de procesamiento facial
# --------------------------------------------------
def get_embedding_from_pil(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.asarray(img)

    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None

    x, y, w, h = detections[0]['box']
    x, y = abs(x), abs(y)
    face = img_array[y:y+h, x:x+w]

    print("Generando embedding...")
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)
    embedding = embedder.embeddings(face)[0]
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding


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


def capture_frame(camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None, 'No se pudo abrir la cámara'
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None, 'No se pudo capturar el frame'
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    return img, None

# --------------------------------------------------
# Manejadores MQTT
# --------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f'Conectado al broker MQTT {BROKER}:{BROKER_PORT}')
        client.subscribe(TOPIC_REGISTRO)
        client.subscribe(TOPIC_TIMBRE)
        client.subscribe(TOPIC_CONFIRM)
        client.publish(TOPIC_STATUS, 'servicio-listo')
    else:
        print('Error al conectar al broker MQTT, rc=', rc)


def handle_registro(client, payload):
    nombre = None
    try:
        data = json.loads(payload)
        nombre = data.get('nombre')
    except Exception:
        nombre = payload.decode() if isinstance(payload, bytes) else str(payload)

    if not nombre:
        client.publish(TOPIC_STATUS, 'registro: nombre no proporcionado')
        return

    client.publish(TOPIC_STATUS, f'Registrando rostro: {nombre}')
    img, err = capture_frame()
    if err:
        client.publish(TOPIC_STATUS, f'Error captura: {err}')
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': err}))
        return

    embedding = get_embedding_from_pil(img)
    if embedding is None:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': 'No se detectó rostro'}))
        return

    try:
        save_embedding(embedding, nombre)
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': f'Rostro {nombre} registrado'}))
        print(f'Rostro {nombre} registrado')
    except Exception as e:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': f'Error al guardar: {e}'}))


def handle_timbre(client):
    client.publish(TOPIC_STATUS, 'Evento timbre recibido: capturando')
    img, err = capture_frame()
    if err:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': False, 'mensaje': err, 'coincidencia': False}))
        return

    embedding = get_embedding_from_pil(img)
    if embedding is None:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No se detectó rostro', 'coincidencia': False}))
        return

    stored_embeddings, names = load_embeddings()
    if not stored_embeddings:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No hay rostros registrados', 'coincidencia': False}))
        return

    distancias = [float(np.linalg.norm(embedding - emb)) for emb in stored_embeddings]
    min_dist = min(distancias)
    idx = int(np.argmin(distancias))
    umbral = 1.0

    if min_dist < umbral:
        nombre = names[idx] if idx < len(names) else f'Persona #{idx+1}'
        payload = {'ok': True, 'mensaje': 'Coincidencia encontrada', 'coincidencia': True, 'nombre': nombre, 'distancia': min_dist}
        client.publish(TOPIC_RESPUESTA, json.dumps(payload))
        print(f'Coincidencia: {nombre} (distancia {min_dist:.4f})')

        confirmed = wait_for_confirmation(timeout=15)
        if confirmed is None:
            client.publish(TOPIC_STATUS, 'Sin respuesta de confirmación (timeout)')
            try:
                set_led_color('red')
            except Exception:
                pass
            client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'Sin confirmación', 'coincidencia': True, 'nombre': nombre, 'distancia': min_dist, 'confirmado': None}))
        elif confirmed:
            client.publish(TOPIC_STATUS, f'Acceso PERMITIDO para {nombre}')
            try:
                set_led_color('green')
            except Exception:
                pass
            client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'Acceso permitido', 'coincidencia': True, 'nombre': nombre, 'distancia': min_dist, 'confirmado': True}))
        else:
            client.publish(TOPIC_STATUS, f'Acceso DENEGADO para {nombre}')
            try:
                set_led_color('red')
            except Exception:
                pass
            client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'Acceso denegado', 'coincidencia': True, 'nombre': nombre, 'distancia': min_dist, 'confirmado': False}))
    else:
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'No coincide con la base', 'coincidencia': False, 'distancia': min_dist}))
        print(f'No coincidencia (min dist {min_dist:.4f})')


def on_message(client, userdata, msg):
    print(f'Mensaje en topic {msg.topic}: {msg.payload}')
    try:
        if msg.topic == TOPIC_REGISTRO:
            threading.Thread(target=handle_registro, args=(client, msg.payload)).start()
        elif msg.topic == TOPIC_TIMBRE:
            threading.Thread(target=handle_timbre, args=(client,)).start()
        elif msg.topic == TOPIC_CONFIRM:
            try:
                data = json.loads(msg.payload)
                permitir = bool(data.get('permitir')) if isinstance(data, dict) else None
            except Exception:
                txt = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)
                permitir = txt.lower() in ('1', 'true', 'si', 'sí', 'permitir')
            set_confirmation(permitir)
        else:
            print('Topic no manejado:', msg.topic)
    except Exception as e:
        print('Error al procesar mensaje:', e)

# --------------------------------------------------
# Confirmación sincronizada
# --------------------------------------------------
_confirm_event = threading.Event()
_confirm_value = None

def set_confirmation(value):
    global _confirm_value
    _confirm_value = value
    _confirm_event.set()

def wait_for_confirmation(timeout=15):
    _confirm_event.clear()
    got = _confirm_event.wait(timeout)
    if not got:
        return None
    return bool(_confirm_value)

# --------------------------------------------------
# GPIO (LED y botón)
# --------------------------------------------------
LED_R_PIN = int(os.environ.get('LED_R_PIN', '17'))
LED_G_PIN = int(os.environ.get('LED_G_PIN', '27'))
LED_B_PIN = int(os.environ.get('LED_B_PIN', '22'))
BUTTON_PIN = int(os.environ.get('BUTTON_PIN', '23'))

_pwm_r = _pwm_g = _pwm_b = None

def init_gpio():
    global _pwm_r, _pwm_g, _pwm_b
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_R_PIN, GPIO.OUT)
        GPIO.setup(LED_G_PIN, GPIO.OUT)
        GPIO.setup(LED_B_PIN, GPIO.OUT)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        _pwm_r = GPIO.PWM(LED_R_PIN, 100)
        _pwm_g = GPIO.PWM(LED_G_PIN, 100)
        _pwm_b = GPIO.PWM(LED_B_PIN, 100)
        _pwm_r.start(0)
        _pwm_g.start(0)
        _pwm_b.start(0)
    except Exception as e:
        print('init_gpio:', e)

def set_led_color(color):
    try:
        if color == 'red':
            r,g,b = 100,0,0
        elif color == 'green':
            r,g,b = 0,100,0
        elif color == 'blue':
            r,g,b = 0,0,100
        elif color == 'white':
            r,g,b = 100,100,100
        else:
            r,g,b = 0,0,0
        if _pwm_r:
            _pwm_r.ChangeDutyCycle(r)
        if _pwm_g:
            _pwm_g.ChangeDutyCycle(g)
        if _pwm_b:
            _pwm_b.ChangeDutyCycle(b)
    except Exception as e:
        try:
            GPIO.output(LED_R_PIN, 1 if r>0 else 0)
            GPIO.output(LED_G_PIN, 1 if g>0 else 0)
            GPIO.output(LED_B_PIN, 1 if b>0 else 0)
        except Exception:
            pass

def button_watcher(client):
    last_state = 0
    while True:
        try:
            state = GPIO.input(BUTTON_PIN)
        except Exception:
            state = 0
        if state and not last_state:
            print('Pulsador detectado: publicando timbre')
            try:
                client.publish(TOPIC_TIMBRE, 'pulsador')
            except Exception as e:
                print('Error publicando timbre desde pulsador:', e)
        last_state = state
        time.sleep(0.1)


def keyboard_watcher(client):
    print("[Teclado] Presiona 't' + Enter para simular timbre. Ctrl+C para salir.")
    while True:
        try:
            txt = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if txt == 't':
            print("[Teclado] Simulando timbre (publicando tópico)")
            try:
                client.publish(TOPIC_TIMBRE, 'teclado')
            except Exception as e:
                print('Error publicando timbre desde teclado:', e)

# --------------------------------------------------
# Función para iniciar MQTT en hilo separado
# --------------------------------------------------
def start_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    
    MQTT_USER = os.environ.get('MQTT_USER')
    MQTT_PASS = os.environ.get('MQTT_PASS')
    if MQTT_USER:
        try:
            mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        except Exception as e:
            print('Error al establecer credenciales MQTT:', e)
    
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(BROKER, BROKER_PORT, 60)
    except Exception as e:
        print('Error al conectar al broker MQTT:', e)
        return

    # Inicializar GPIO y arrancar hilo de pulsador
    try:
        init_gpio()
        threading.Thread(target=button_watcher, args=(mqtt_client,), daemon=True).start()
        try:
            threading.Thread(target=keyboard_watcher, args=(mqtt_client,), daemon=True).start()
        except Exception:
            pass
    except Exception as e:
        print('No se pudo inicializar GPIO o hilo de botón:', e)

    # Loop MQTT en hilo separado
    mqtt_client.loop_forever()

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    print('Servicio de reconocimiento listo. Esperando comandos MQTT...')
    
    # Iniciar MQTT en hilo separado
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Esperar un momento para que MQTT se conecte
    time.sleep(2)
    
    # Iniciar Flask (bloquea el hilo principal)
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', '5000'))
    
    print(f'Iniciando servidor Flask en http://{FLASK_HOST}:{FLASK_PORT}')
    print(f'Accede a la interfaz web desde: http://<IP_RASPBERRY>:{FLASK_PORT}')
    
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print('Interrumpido por teclado, saliendo...')
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass


if __name__ == '__main__':
    main()
