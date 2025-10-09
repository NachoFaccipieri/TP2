from flask import Flask, jsonify, request
from pymongo import MongoClient
import imageio
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Conexión a MongoDB (ajustá el host si usás Docker)
client = MongoClient('mongodb://localhost:27017/')
db = client['faceid']
collection = db['embeddings']

# Inicializar detector y modelo de embeddings
detector = MTCNN()
embedder = FaceNet()

def get_embedding(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    #Convertir a NumpyArray
    img_array = np.asarray(img)
    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None
    
    #Tomar el primer rostro detectado
    x, y, w, h = detections[0]['box']
    face = img_array[y:y+h, x:x+w]
    face = Image.fromarray(face).resize((160, 160))
    face = np.asarray(face)
    face = np.expand_dims(face, axis=0)

    embedding = embedder.embeddings(face)[0]
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

@app.route('/registrar-rostro', methods=['POST'])
def registrar_rostro():
    data = request.get_json()
    nombre = data.get("nombre") if data else None

    reader = imageio.get_reader("<video0>")
    frame = reader.get_data(0)
    reader.close()

    #Convertir a PIL Image
    frame_img = Image.fromarray(frame)

    #2: Obtener embedding del frame
    frame_embedding = get_embedding(frame_img)
    if frame_embedding is None:
        return jsonify({"mensaje": "❌ No se detectó rostro en el frame de la cámara"}), 400
    
    #3: Guardar en MongoDB
    embedding_list = frame_embedding.tolist()
    collection.insert_one({"embedding": embedding_list, "nombre": nombre or "Desconocido"})
    return jsonify({"mensaje": f"✅ Embedding guardado en MongoDB para {nombre or 'Desconocido'}"})

@app.route('/tocar-timbre', methods=['POST'])
def tocar_timbre():
    # 1. Capturar frame de la cámara
    reader = imageio.get_reader("<video0>")
    frame = reader.get_data(0)
    reader.close()
    frame_img = Image.fromarray(frame)

    # 2. Obtener embedding del frame
    frame_embedding = get_embedding(frame_img)
    if frame_embedding is None:
        return jsonify({"coincidencia": False, "mensaje": "❌ No se detectó rostro en el frame de la cámara"}), 400

    # 3. Leer embeddings guardados desde MongoDB
    embeddings = list(collection.find({}))
    if not embeddings:
        return jsonify({"coincidencia": False, "mensaje": "No hay rostros registrados en la base de datos."}), 400

    # 4. Comparar con todos los embeddings guardados
    distancias = [np.linalg.norm(frame_embedding - np.array(emb['embedding'])) for emb in embeddings]
    min_dist = min(distancias)
    idx = distancias.index(min_dist)

    # Umbral típico ~1.0 (ajustable)
    if min_dist < 1.0:
        nombre = embeddings[idx].get("nombre", "Desconocido")
        return jsonify({
            "coincidencia": True,
            "mensaje": f"✅ Persona reconocida: {nombre} (distancia: {min_dist:.4f})",
            "nombre": nombre
        })
    else:
        return jsonify({
            "coincidencia": False,
            "mensaje": "❌ No coincide con ninguna persona registrada"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
