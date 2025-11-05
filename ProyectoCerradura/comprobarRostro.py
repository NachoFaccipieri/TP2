import os
# Ajustes para Pi con poca RAM: limitar hilos y reducir logs de TF
# Deben establecerse antes de importar TensorFlow/keras para que tengan efecto
# Activar poniendo RPI_LOW_RAM=1 en el entorno (por defecto activado)
#if os.environ.get('RPI_LOW_RAM', '1') == '1':
#    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
#    os.environ.setdefault('OMP_NUM_THREADS', '1')
#    os.environ.setdefault('MKL_NUM_THREADS', '1')
#    os.environ.setdefault('INTRA_OP_NUM_THREADS', '1')
#    os.environ.setdefault('INTER_OP_NUM_THREADS', '1')

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

# Config
BROKER = os.environ.get('MQTT_BROKER', 'localhost')
BROKER_PORT = int(os.environ.get('MQTT_PORT', '1883'))
TOPIC_REGISTRO = os.environ.get('TOPIC_REGISTRO', 'cerradura/registro')
TOPIC_TIMBRE = os.environ.get('TOPIC_TIMBRE', 'cerradura/timbre')
TOPIC_RESPUESTA = os.environ.get('TOPIC_RESPUESTA', 'cerradura/persona')
TOPIC_STATUS = os.environ.get('TOPIC_STATUS', 'cerradura/status')
TOPIC_CONFIRM = os.environ.get('TOPIC_CONFIRM', 'cerradura/confirmacion')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
EMBED_FILE = os.path.join(APP_ROOT, 'embeddings.txt')
NAMES_FILE = os.path.join(APP_ROOT, 'names.txt')


print("Cargando MTCNN y FaceNet (TensorFlow)...")
try:
    detector = MTCNN()
    embedder = FaceNet()
    print("Modelos cargados.")
except Exception as e:
    print(f"Error al cargar modelos de TensorFlow: {e}")
    print("Esto probablemente sea un error de falta de memoria (RAM).")
    sys.exit(1)


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
    # payload puede ser JSON {'nombre': 'Mati'} o solo un nombre
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

        # Esperar confirmación desde la web (TOPIC_CONFIRM)
        # La web debe publicar JSON {'permitir': true/false} o un texto simple
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
            # manejar en hilo para no bloquear loop mqtt
            threading.Thread(target=handle_registro, args=(client, msg.payload)).start()
        elif msg.topic == TOPIC_TIMBRE:
            threading.Thread(target=handle_timbre, args=(client,)).start()
        elif msg.topic == TOPIC_CONFIRM:
            # Mensaje de confirmación desde la web
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


# --- Confirmación sincronizada ---
_confirm_event = threading.Event()
_confirm_value = None

def set_confirmation(value):
    """Establece la confirmación recibida desde la web y despierta al waiter."""
    global _confirm_value
    _confirm_value = value
    _confirm_event.set()

def wait_for_confirmation(timeout=15):
    """Espera que llegue una confirmación vía TOPIC_CONFIRM. Retorna True/False o None si timeout."""
    _confirm_event.clear()
    got = _confirm_event.wait(timeout)
    if not got:
        return None
    return bool(_confirm_value)


# --- LED RGB y botón (GPIO) ---
# Pines por defecto (pueden ajustarse vía variables de entorno)
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
    """Colores simples: 'red', 'green', 'blue', 'white', 'off'. Usa duty cycle 0-100."""
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
        # Si no hay PWM (mock) intentar output simple
        try:
            GPIO.output(LED_R_PIN, 1 if r>0 else 0)
            GPIO.output(LED_G_PIN, 1 if g>0 else 0)
            GPIO.output(LED_B_PIN, 1 if b>0 else 0)
        except Exception:
            pass

def button_watcher(client):
    """Hilo que vigila el pulsador y publica TOPIC_TIMBRE cuando se presiona."""
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
    """Hilo que permite simular el timbre desde teclado: presionar 't' + Enter publica TOPIC_TIMBRE."""
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
        else:
            # permitir otros comandos cortos en futuro
            pass


def main():
    client = mqtt.Client()
    # Soporte opcional de credenciales MQTT si el broker requiere autenticación
    MQTT_USER = os.environ.get('MQTT_USER')
    MQTT_PASS = os.environ.get('MQTT_PASS')
    if MQTT_USER:
        try:
            client.username_pw_set(MQTT_USER, MQTT_PASS)
        except Exception as e:
            print('Error al establecer credenciales MQTT:', e)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, BROKER_PORT, 60)
    except Exception as e:
        print('Error al conectar al broker MQTT:', e)
        sys.exit(1)

    # Inicializar GPIO y arrancar hilo de pulsador
    try:
        init_gpio()
        threading.Thread(target=button_watcher, args=(client,), daemon=True).start()
        # Hilo opcional para simular timbre desde teclado (útil si no hay pulsador)
        try:
            threading.Thread(target=keyboard_watcher, args=(client,), daemon=True).start()
        except Exception:
            pass
    except Exception as e:
        print('No se pudo inicializar GPIO o hilo de botón:', e)

    # loop_forever bloqueará el hilo principal
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print('Interrumpido por teclado, saliendo...')
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass


if __name__ == '__main__':
    print('Servicio de reconocimiento listo. Esperando comandos MQTT...')
    main()
