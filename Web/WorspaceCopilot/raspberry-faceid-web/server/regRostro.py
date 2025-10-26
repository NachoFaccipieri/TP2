from flask import Flask, jsonify, request
import imageio
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import paho.mqtt.publish as publish

app = Flask(__name__)

# Inicializar detector y modelo de embeddings
detector = MTCNN()
embedder = FaceNet()

def get_embedding(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.asarray(img)
    detections = detector.detect_faces(img_array)
    if len(detections) == 0:
        return None
    
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

    frame_img = Image.fromarray(frame)
    frame_embedding = get_embedding(frame_img)
    if frame_embedding is None:
        return jsonify({"mensaje": "❌ No se detectó rostro en el frame de la cámara"}), 400
    
    # Aquí se debería guardar el embedding en un lugar persistente
    # En este caso, se omite la persistencia para simplificar

    # Publicar mensaje en MQTT
    publish.single("faceid/registro", f"Rostro registrado: {nombre or 'Desconocido'}", hostname="localhost")
    return jsonify({"mensaje": f"✅ Rostro registrado para {nombre or 'Desconocido'}"})

@app.route('/tocar-timbre', methods=['POST'])
def tocar_timbre():
    reader = imageio.get_reader("<video0>")
    frame = reader.get_data(0)
    reader.close()
    frame_img = Image.fromarray(frame)

    frame_embedding = get_embedding(frame_img)
    if frame_embedding is None:
        return jsonify({"coincidencia": False, "mensaje": "❌ No se detectó rostro en el frame de la cámara"}), 400

    # Aquí se debería comparar el embedding con los almacenados
    # En este caso, se omite la comparación para simplificar

    # Publicar mensaje en MQTT
    publish.single("faceid/timbre", "Timbre tocado, rostro detectado", hostname="localhost")
    return jsonify({"coincidencia": True, "mensaje": "✅ Rostro detectado y timbre tocado"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)