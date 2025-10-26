import cv2      # <--- Para la cámara
import sys      # <--- Para salir limpiamente
from mtcnn import MTCNN
from keras_facenet import FaceNet
import numpy as np
from PIL import Image
import json

# --- 0. Cargar modelos (UNA SOLA VEZ) ---
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

# --- 1. Cargar embeddings de la base (UNA SOLA VEZ) ---
print("Cargando base de datos de embeddings...")
stored_embeddings = load_embeddings("embeddings.txt")
if not stored_embeddings:
    print("No hay rostros registrados en la base de datos.")
    sys.exit() 

print("\n" + "="*40)
print("   Sistema listo. El programa está en espera.")
print("   Presiona 't' y luego [Enter] para capturar.")
print("   Escribe 'q' y luego [Enter] para salir.")
print("="*40)

# --- BUCLE DE ESPERA EN TERMINAL ---
while True:
    # El programa se frena aquí, esperando tu input en la terminal
    comando = input("\nEsperando comando ('t' o 'q'): ")

    if comando.lower() == 'q':
        print("Saliendo...")
        break

    if comando.lower() == 't':
        # --- 2. Capturar un frame (SOLO AL PRESIONAR 't') ---
        print("📸 Iniciando cámara y capturando foto...")
        cap = cv2.VideoCapture(0)  # Abre la cámara
        
        if not cap.isOpened():
            print("Error fatal: No se pudo abrir la cámara con OpenCV.")
            continue # Vuelve al inicio del bucle

        # Lee un solo frame
        ret, frame = cap.read() 
        # Suelta la cámara inmediatamente
        cap.release() 

        if not ret:
            print("Error: No se pudo capturar el frame con OpenCV.")
            continue # Vuelve al inicio del bucle

        print("¡Foto capturada!")

        # --- Corrección de color CRUCIAL ---
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_img = Image.fromarray(frame_rgb)
        # -----------------------------------------------------------------

        # --- 3. Procesar la imagen capturada ---
        # (Esto sigue siendo la parte lenta, ~19 segundos)
        frame_embedding = get_embedding(frame_img) 
        if frame_embedding is None:
            print("❌ No se detectó rostro en el frame de la cámara")
            continue # Vuelve al inicio del bucle

        # --- 4. Comparar con todos los embeddings guardados ---
        print("Comparando rostro capturado con la base de datos...")
        distancias = [np.linalg.norm(frame_embedding - emb) for emb in stored_embeddings]
        min_dist = min(distancias)
        idx = distancias.index(min_dist)

        print("---------------------------------")
        print(f"Distancia mínima encontrada: {min_dist:.4f} (vs rostro #{idx+1})")

        if min_dist < 1.0:
            print("✅ Persona reconocida en la base de datos")
        else:
            print("❌ No coincide con ninguna persona registrada")
        print("---------------------------------")
    
    else:
        print("Comando no reconocido. Intenta de nuevo.")

print("Programa terminado.")
