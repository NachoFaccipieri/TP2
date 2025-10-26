# import imageio  <--- ELIMINADO
import cv2      # <--- AGREGADO: Para la cámara
import sys      # <--- AGREGADO: Para salir limpiamente
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json

# --- 0. Cargar modelos ---
print("Cargando MTCNN y FaceNet (TensorFlow)...")
try:
    detector = MTCNN()
    embedder = FaceNet()
    print("Modelos cargados.")
except Exception as e:
    print(f"Error al cargar modelos de TensorFlow: {e}")
    print("Esto probablemente sea un error de falta de memoria (RAM).")
    sys.exit()
print("Termino detector y embedder")
# --- Función para obtener embedding de una imagen ---
def get_embedding(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.asarray(img)
    
    print("Detectando rostro...")
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
    embedding = embedder.embeddings(face)
    return embedding[0]

# --- Función para leer embeddings guardados ---
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

# --- 1. Cargar embeddings de la base ---
print("Cargando base de datos de embeddings...")
stored_embeddings = load_embeddings("embeddings.txt")
if not stored_embeddings:
    print("No hay rostros registrados en la base de datos.")
    sys.exit() # Usamos sys.exit

# --- 2. Capturar un frame de la cámara (BLOQUE CORREGIDO CON OPENCV) ---
print("📸 Capturando foto de la cámara...")
cap = cv2.VideoCapture(0)  # El '0' es /dev/video0

if not cap.isOpened():
    print("Error fatal: No se pudo abrir la cámara con OpenCV.")
    sys.exit()

# Leer un solo frame
ret, frame = cap.read() 
# Soltar la cámara inmediatamente
cap.release() 

if not ret:
    print("Error: No se pudo capturar el frame con OpenCV.")
    sys.exit()

print("¡Foto capturada!")

# --- Corrección de color CRUCIAL ---
# OpenCV lee en BGR, pero PIL/FaceNet esperan RGB
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# Convertir a imagen PIL (el resto de tu script no cambia)
frame_img = Image.fromarray(frame_rgb)
# -----------------------------------------------------------------

# --- 3. Procesar la imagen capturada ---
frame_embedding = get_embedding(frame_img)
if frame_embedding is None:
    print("No se detectó rostro en el frame de la cámara")
    sys.exit()

# --- 4. Comparar con todos los embeddings guardados ---
print("Comparando rostro capturado con la base de datos...")
distancias = [np.linalg.norm(frame_embedding - emb) for emb in stored_embeddings]
min_dist = min(distancias)
idx = distancias.index(min_dist)

print("---------------------------------")
print(f"Distancia mínima encontrada: {min_dist:.4f} (vs rostro #{idx+1})")

# Umbral ajustable
if min_dist < 1.0:
    print("✅ Persona reconocida en la base de datos")
else:
    print("❌ No coincide con ninguna persona registrada")
print("---------------------------------")
