import imageio
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image

# Inicializar detector y modelo de embeddings
detector = MTCNN()
embedder = FaceNet()

# --- Función para obtener embedding de una imagen ---
def get_embedding(img):
    # Convertir a RGB si no lo está
    if img.mode != 'RGB':
        img = img.convert('RGB')
    # Convertir a numpy array
    img_array = np.asarray(img)
    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None

    # Tomar el primer rostro detectado
    x, y, w, h = detections[0]['box']
    face = img_array[y:y+h, x:x+w]
    # Redimensionar a 160x160 para FaceNet
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)  # batch de 1
    embedding = embedder.embeddings(face)
    return embedding[0]

# --- 1. Embedding de la foto de referencia ---
ref_img = Image.open("referencia.jpeg")  # o ruta absoluta
ref_embedding = get_embedding(ref_img)
if ref_embedding is None:
    print("No se detectó rostro en la foto de referencia")
    exit()

# --- 2. Capturar un frame de la cámara ---
reader = imageio.get_reader("<video0>")  # cámara en Linux
frame = reader.get_data(0)               # tomar primer frame
reader.close()

# Convertir a PIL Image
frame_img = Image.fromarray(frame)

frame_embedding = get_embedding(frame_img)
if frame_embedding is None:
    print("No se detectó rostro en el frame de la cámara")
    exit()

# --- 3. Comparar embeddings ---
dist = np.linalg.norm(ref_embedding - frame_embedding)
print(f"Distancia entre rostros: {dist:.4f}")

if dist < 1.0:
    print("Probablemente es la MISMA persona ✅")
else:
    print("Son personas diferentes ❌")
