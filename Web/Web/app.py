import cv2
from flask import Flask, jsonify  # <--- AGREGADO
from flask_cors import CORS      # <--- AGREGADO
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json
import sys # <-- Lo mantenemos solo para el error de carga inicial

# --- 0. Inicializar Flask ---
app = Flask(__name__)
# CORS es VITAL para permitir que tu web (en 8080) llame a esta API (en 5000)
CORS(app) 

# --- 1. Cargar modelos (GLOBAL) ---
# Esto se ejecuta UNA SOLA VEZ cuando el servidor `python3 app.py` arranca.
print("Cargando MTCNN y FaceNet (TensorFlow)...")
try:
    detector = MTCNN()
    embedder = FaceNet()
    print("Modelos cargados. Servidor listo.")
except Exception as e:
    print(f"Error fatal al cargar modelos de TensorFlow: {e}")
    print("El servidor no puede arrancar sin los modelos.")
    sys.exit() # <-- Aquí sí podemos usar sys.exit, porque el servidor no puede arrancar

# --- 2. Funciones auxiliares (Sin cambios) ---
def get_embedding(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.asarray(img)
    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None
    x, y, w, h = detections[0]['box']
    x, y = abs(x), abs(y)
    face = img_array[y:y+h, x:x+w]
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)
    embedding = embedder.embeddings(face)
    return embedding[0]

def load_embeddings(file_path="embeddings.txt"):
    embeddings = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                vec = json.loads(line.strip())
                embeddings.append(np.array(vec))
    except FileNotFoundError:
        print("⚠️ No hay archivo de embeddings todavía.")
    return embeddings

# --- 3. La ruta de la API de reconocimiento ---
# Toda la lógica de tu script se mueve aquí.
# Se ejecutará CADA VEZ que tu web llame a http://...:5000/api/recognize
@app.route("/api/recognize")
def recognize_face():
    print("Petición recibida. Iniciando reconocimiento...")

    # --- Cargar embeddings de la base ---
    stored_embeddings = load_embeddings("embeddings.txt")
    if not stored_embeddings:
        print("Error: No hay rostros registrados en la base.")
        # Reemplazamos sys.exit() con un JSON de error
        return jsonify({"status": "error", "message": "No hay rostros registrados en la base de datos"}), 500

    # --- Capturar frame de la cámara ---
    print("📸 Capturando foto de la cámara...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error fatal: No se pudo abrir la cámara.")
        return jsonify({"status": "error", "message": "No se pudo abrir la cámara"}), 500

    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Error: No se pudo capturar el frame.")
        return jsonify({"status": "error", "message": "No se pudo capturar el frame"}), 500
    
    print("¡Foto capturada!")

    # --- Procesar la imagen capturada ---
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_img = Image.fromarray(frame_rgb)
    
    frame_embedding = get_embedding(frame_img)
    if frame_embedding is None:
        print("No se detectó rostro en el frame.")
        return jsonify({"status": "error", "message": "No se detectó rostro en el frame"}), 400

    # --- Comparar con todos los embeddings guardados ---
    print("Comparando rostro capturado con la base de datos...")
    distancias = [np.linalg.norm(frame_embedding - emb) for emb in stored_embeddings]
    min_dist = min(distancias)
    idx = distancias.index(min_dist)

    threshold = 1.0  # Umbral ajustable
    is_match = bool(min_dist < threshold) # Convertir a booleano de Python

    print("---------------------------------")
    print(f"Distancia mínima: {min_dist:.4f} (Rostro #{idx+1})")
    print(f"Resultado: {'✅ Reconocido' if is_match else '❌ Desconocido'}")
    print("---------------------------------")

    # --- Devolver el resultado como JSON a la página web ---
    return jsonify({
        "status": "success",
        "match": is_match,
        "distance": round(min_dist, 4),
        "closest_match_index": idx + 1
    })

# --- 4. El punto de entrada para ejecutar el servidor ---
if __name__ == '__main__':
    # Usamos host='0.0.0.0' para que sea visible en tu red (ej. 192.168.1.84)
    app.run(host='0.0.0.0', port=5000)
