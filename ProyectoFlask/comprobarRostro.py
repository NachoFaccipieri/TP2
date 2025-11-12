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

# Flask imports
from flask import Flask, send_from_directory, jsonify, Response, send_file
from flask_cors import CORS

# Config
BROKER = os.environ.get('MQTT_BROKER', 'localhost')
BROKER_PORT = int(os.environ.get('MQTT_PORT', '1883'))
TOPIC_REGISTRO = os.environ.get('TOPIC_REGISTRO', 'cerradura/registro')
TOPIC_TIMBRE = os.environ.get('TOPIC_TIMBRE', 'cerradura/timbre')
TOPIC_RESPUESTA = os.environ.get('TOPIC_RESPUESTA', 'cerradura/persona')
TOPIC_STATUS = os.environ.get('TOPIC_STATUS', 'cerradura/status')

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
        print(f'Conectado al broker MQTT {BROKER}:{BROKER_PORT}')
        client.subscribe(TOPIC_REGISTRO)
        client.subscribe(TOPIC_TIMBRE)
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
        client.publish(TOPIC_RESPUESTA, json.dumps({'ok': True, 'mensaje': 'Coincidencia encontrada', 'coincidencia': True, 'nombre': nombre, 'distancia': min_dist}))
        print(f'Coincidencia: {nombre} (distancia {min_dist:.4f})')
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
        else:
            print('Topic no manejado:', msg.topic)
    except Exception as e:
        print('Error al procesar mensaje:', e)


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
        print('Error al conectar al broker MQTT:', e)
        return

    # Loop MQTT en hilo separado
    mqtt_client.loop_forever()


def main_flask():
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


if __name__ == '__main__':
    # Usar Flask por defecto
    use_flask = os.environ.get('USE_FLASK', '1') == '1'
    if use_flask:
        main_flask()
    else:
        print('Servicio de reconocimiento listo. Esperando comandos MQTT...')
        main()