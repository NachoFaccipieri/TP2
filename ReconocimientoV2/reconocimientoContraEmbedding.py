import imageio
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json

# Inicializar detector y modelo de embeddings
detector = MTCNN()
embedder = FaceNet()

#Función para obtener embedding de una imagen
def get_embedding(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.asarray(img)
    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None

    # Tomar el primer rostro detectado
    x, y, w, h = detections[0]['box']
    face = img_array[y:y+h, x:x+w]
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)
    embedding = embedder.embeddings(face)
    return embedding[0]

#Función para leer embeddings guardados
def load_embeddings(file_path="embeddings.txt"):
    embeddings = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                vec = json.loads(line.strip())
                embeddings.append(np.array(vec))
    except FileNotFoundError:
        print("No hay archivo de embeddings todavía.")
    return embeddings

#Cargar embeddings de la base
stored_embeddings = load_embeddings("embeddings.txt")
if not stored_embeddings:
    print("No hay rostros registrados en la base de datos.")
    exit()

#Capturar un frame de la cámara
reader = imageio.get_reader("<video0>")  # cámara en Linux
frame = reader.get_data(0)               # tomar primer frame
reader.close()

frame_img = Image.fromarray(frame)

frame_embedding = get_embedding(frame_img)
if frame_embedding is None:
    print("No se detectó rostro en el frame de la cámara")
    exit()

#Comparar con todos los embeddings guardados
distancias = [np.linalg.norm(frame_embedding - emb) for emb in stored_embeddings]
min_dist = min(distancias)
idx = distancias.index(min_dist)

print(f"Distancia mínima encontrada: {min_dist:.4f} (vs rostro #{idx+1})")

# Umbral ajustable
if min_dist < 1.0:
    print("Persona reconocida en la base de datos")
else:
    print("No coincide con ninguna persona registrada")
