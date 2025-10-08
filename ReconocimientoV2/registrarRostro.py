import imageio
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json

# Inicializar detector y modelo de embeddings
detector = MTCNN()
embedder = FaceNet()

# Función para obtener embedding de una imagen
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
    face = np.expand_dims(face, axis=0) 

    embedding = embedder.embeddings(face)[0]
    # Normalización L2
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

#Capturar un frame de la cámara
reader = imageio.get_reader("<video0>")  # cámara en Linux
frame = reader.get_data(0)               # tomar primer frame
reader.close()

# Convertir a PIL Image
frame_img = Image.fromarray(frame)

#Obtener embedding del frame
frame_embedding = get_embedding(frame_img)
if frame_embedding is None:
    print(" No se detectó rostro en el frame de la cámara")
    exit()

#Guardar embedding en archivo
output_file = "embeddings.txt"
embedding_list = frame_embedding.tolist()

with open(output_file, "a") as f:
    f.write(json.dumps(embedding_list) + "\n")

print(f"Embedding guardado en {output_file}")
