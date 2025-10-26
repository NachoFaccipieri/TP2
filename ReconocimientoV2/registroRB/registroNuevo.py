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

# --- Función para obtener embedding de una imagen ---
def get_embedding(img):
    # Convertir a RGB si no lo está
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    print("Detectando rostro...")
    img_array = np.asarray(img)
    detections = detector.detect_faces(img_array)
    
    if len(detections) == 0:
        return None

    # Tomar el primer rostro detectado
    x, y, w, h = detections[0]['box']
    x, y = abs(x), abs(y) # Asegurar que no sean negativos
    face = img_array[y:y+h, x:x+w]
    
    print("Generando embedding...")
    # Redimensionar a 160x160 para FaceNet
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)  # batch de 1

    embedding = embedder.embeddings(face)[0]
    # Normalización L2 (buena práctica)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

# --- 1. Capturar un frame de la cámara (BLOQUE CORREGIDO CON OPENCV) ---
print("📸 Iniciando cámara y capturando foto...")
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

# --- 2. Obtener embedding del frame ---
frame_embedding = get_embedding(frame_img)
if frame_embedding is None:
    print("❌ No se detectó rostro en el frame de la cámara")
    sys.exit()

# --- 3. Guardar embedding en archivo ---
output_file = "embeddings.txt"
embedding_list = frame_embedding.tolist()

try:
    with open(output_file, "a") as f:
        f.write(json.dumps(embedding_list) + "\n")
    
    print(f"✅ Embedding guardado en {output_file}")

except Exception as e:
    print(f"Error al guardar el archivo: {e}")
