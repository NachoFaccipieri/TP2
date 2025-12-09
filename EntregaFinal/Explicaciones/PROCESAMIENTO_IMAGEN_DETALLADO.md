# 📷 PROCESAMIENTO DE IMAGEN - FaceID Completo

## Resumen Ejecutivo

```
ENTRADA: Imagen capturada con cámara (RGB, cualquier tamaño)
   ↓
MTCNN: Detecta rostro en la imagen
   ↓
PIL: Extrae y redimensiona rostro a 160x160
   ↓
FaceNet: Convierte rostro en "huella dactilar facial" (128 números)
   ↓
NumPy: Normaliza la huella (L2 normalization)
   ↓
SALIDA: Vector de 128 números entre -1 y 1 (embedding)
```

---

## 📸 PASO 1: Captura de Imagen (OpenCV)

### Función: `capture_frame()`

```python
def capture_frame(camera_index=0, save_last=True):
    """Captura un frame de la cámara"""
    global last_captured_image
    
    # Abre la cámara
    cap = cv2.VideoCapture(camera_index)
    #   ├─ camera_index=0 → Primera cámara USB/Raspberry Pi Camera
    #   └─ Retorna objeto VideoCapture
    
    if not cap.isOpened():
        return None, 'No se pudo abrir la cámara'
    
    # Captura UN frame
    ret, frame = cap.read()
    #   ├─ ret = True si fue exitoso
    #   └─ frame = numpy array BGR (altura, ancho, 3)
    #              ├─ OpenCV usa BGR, no RGB
    #              ├─ Shape: (480, 640, 3) típicamente
    #              └─ dtype: uint8 (0-255 por canal)
    
    cap.release()
    # Cierra la cámara para liberar recursos
    
    if not ret:
        return None, 'No se pudo capturar el frame'
    
    # Guarda una copia para mostrar después
    if save_last:
        with last_image_lock:
            last_captured_image = frame.copy()
            # Se guarda porque /api/camera/last la usa
    
    # Convierte BGR → RGB (OpenCV usa BGR, PIL usa RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #   ├─ OpenCV: BGR (Blue, Green, Red)
    #   ├─ PIL/RGB: RGB (Red, Green, Blue)
    #   └─ Los canales están invertidos, hay que corregir
    
    # Convierte array NumPy a imagen PIL
    img = Image.fromarray(frame_rgb)
    #   ├─ PIL es más fácil de manipular
    #   └─ Se necesita para redimensionamiento
    
    return img, None
```

### Ejemplo Visual

```
Cámara USB/Raspberry Pi
         ↓
OpenCV abre VideoCapture
         ↓
Captura 1 frame: numpy array
  Shape: (480, 640, 3)
  dtype: uint8
  Valores: 0-255 por pixel por canal
         ↓
Convierte BGR → RGB
  B: [255, 100, 50, ...]
  G: [100, 200, 150, ...]
  R: [50, 255, 100, ...]
         ↓
Crea PIL.Image
  Más fácil de manipular
         ↓
Retorna PIL.Image object
```

---

## 🔍 PASO 2: Detección de Rostro (MTCNN)

### Función: `generarEmbedding()` - Parte 1

```python
def generarEmbedding(img):
    """
    ENTRADA: PIL.Image (cualquier tamaño)
    SALIDA: numpy array de 128 números (embedding)
    """
    
    # Validar que sea RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convierte PIL.Image a numpy array
    img_array = np.asarray(img)
    #   ├─ Shape: (altura, ancho, 3)
    #   ├─ dtype: uint8
    #   └─ Valores: 0-255
    
    # ========== MTCNN: DETECTA ROSTROS ==========
    detections = detector.detect_faces(img_array)
    #   ├─ detector = MTCNN() (importado al inicio)
    #   ├─ Detecta TODOS los rostros en la imagen
    #   ├─ Retorna lista de diccionarios
    #   └─ Ejemplo:
    #      [
    #        {
    #          'box': [x, y, ancho, alto],
    #          'confidence': 0.98,
    #          'keypoints': {'left_eye': [...], ...}
    #        }
    #      ]
    
    if len(detections) == 0:
        return None  # No detectó ningún rostro
    
    # Toma el PRIMER rostro detectado (el más grande/confiado)
    x, y, w, h = detections[0]['box']
    #   ├─ x, y = posición superior-izquierda del rostro
    #   ├─ w = ancho del rostro
    #   ├─ h = alto del rostro
    #   └─ Pueden ser negativos en los bordes, por eso:
    
    x, y = abs(x), abs(y)  # Asegurar que no sean negativos
    
    # Extrae la región de interés (ROI) del rostro
    face = img_array[y:y+h, x:x+w]
    #   ├─ numpy slicing: [fila_inicio:fila_fin, col_inicio:col_fin]
    #   ├─ Extrae solo el área del rostro
    #   └─ Shape: (h, w, 3)
```

### Visualización MTCNN

```
Imagen original (640x480)
┌─────────────────────────────────────────────┐
│                                               │
│     👤  ← Rostro detectado                   │
│   (MTCNN dibuja un recuadro aquí)            │
│   ├─ x=100, y=50                            │
│   ├─ w=150, h=180                           │
│                                               │
│                                               │
└─────────────────────────────────────────────┘

MTCNN retorna:
  'box': [100, 50, 150, 180]
  
Se extrae:
  face = img[50:230, 100:250]  ← Solo el rostro
```

---

## 📐 PASO 3: Redimensionamiento (PIL)

### Función: `generarEmbedding()` - Parte 2

```python
def generarEmbedding(img):
    # ... (código anterior)
    
    # face = array de cualquier tamaño
    # Ejemplo: (180, 150, 3) si el rostro detectado tiene eso
    
    # ========== REDIMENSIONA A 160x160 ==========
    # FaceNet REQUIERE exactamente 160x160
    
    face = Image.fromarray(face).resize((160, 160))
    #   ├─ Convierte numpy array → PIL.Image
    #   ├─ .resize((160, 160)) redimensiona
    #   ├─ Nueva shape: (160, 160, 3)
    #   └─ IMPORTANTE: Distorsiona si la relación aspecto no es 1:1
    
    # Convierte de vuelta a numpy array
    face = np.asarray(face)
    #   ├─ Shape: (160, 160, 3)
    #   ├─ dtype: uint8
    #   └─ Valores: 0-255
    
    # ========== PREPARAR PARA FACENET ==========
    # FaceNet espera un batch (lote), aunque sea de 1 imagen
    
    face = np.expand_dims(face, axis=0)
    #   ├─ Agrega dimensión batch
    #   ├─ Antes: (160, 160, 3)
    #   ├─ Después: (1, 160, 160, 3)  ← Batch de 1
    #   └─ Ahora FaceNet puede procesar
```

### Visualización del Redimensionamiento

```
Rostro extraído: (180, 150, 3)
┌─────────────────────────────┐
│        👤                    │  ← Rectangular
└─────────────────────────────┘

.resize((160, 160)) aplica escalado bilineal
         ↓
Rostro redimensionado: (160, 160, 3)
┌────────────────────────────────┐
│          👤                     │  ← Cuadrado
│                                 │
└────────────────────────────────┘

np.expand_dims(axis=0)
         ↓
Batch: (1, 160, 160, 3)
  [
    Imagen 1: (160, 160, 3)
  ]
```

---

## 🧠 PASO 4: Generación de Embedding (FaceNet)

### Función: `generarEmbedding()` - Parte 3

```python
def generarEmbedding(img):
    # ... (código anterior)
    
    # face = (1, 160, 160, 3) - Batch de 1 imagen
    
    # ========== FACENET: GENERA EMBEDDING ==========
    print("Generando embedding...")
    
    embedding = embedder.embeddings(face)[0]
    #   ├─ embedder = FaceNet() (importado al inicio)
    #   ├─ FaceNet es una red neuronal convolucional
    #   ├─ embedder.embeddings(face) retorna:
    #   │  ├─ Array shape: (1, 128) si batch_size=1
    #   │  └─ Cada elemento = un vector de 128 números
    #   ├─ [0] → Toma el primer (único) embedding
    #   └─ embedding = array de 128 números
    
    # embedding = [0.123, -0.456, 0.789, ..., -0.234]  ← 128 números
```

### ¿Qué es FaceNet?

```
FaceNet es una red neuronal entrenada para:
1. Tomar una imagen de rostro (160x160x3)
2. Extraer características faciales
3. Convertirlas en un vector de 128 números

Este vector se llama EMBEDDING o "huella dactilar facial"

Propiedades importantes:
├─ Rostros similares → embeddings similares
├─ Rostros diferentes → embeddings diferentes
├─ Invariante a:
│  ├─ Pose (ángulo de la cabeza)
│  ├─ Iluminación
│  ├─ Expresión facial
│  └─ Edad (dentro de límites)
├─ Resultado: 128 números float32
└─ Normalmente entre -1 y 1 (después de normalizar)
```

### Arquitectura Simplificada

```
INPUT: (160, 160, 3)
   ↓
Conv2D(64, 3x3) → ReLU → BatchNorm
   ↓
Conv2D(64, 3x3) → ReLU → BatchNorm
   ↓
MaxPool(2x2)  [ahora 80x80x64]
   ↓
Conv2D(128, 3x3) → ReLU → BatchNorm
   ↓
[... más capas convolucionales ...]
   ↓
GlobalAveragePooling  [flatten]
   ↓
Dense(128)  ← AQUI se genera el embedding
   ↓
Dense(512)  ← Layer interno adicional
   ↓
OUTPUT: 128 números (embedding)
```

---

## 📊 PASO 5: Normalización L2 (NumPy)

### Función: `generarEmbedding()` - Parte 4

```python
def generarEmbedding(img):
    # ... (código anterior)
    
    embedding = embedder.embeddings(face)[0]
    # embedding = [0.123, -0.456, 0.789, ..., -0.234]
    
    # ========== NORMALIZACIÓN L2 ==========
    # L2 norm: ||v|| = sqrt(v1² + v2² + ... + v128²)
    
    norm = np.linalg.norm(embedding)
    #   ├─ np.linalg.norm() calcula la norma L2
    #   ├─ Ejemplo numérico:
    #   │  embedding = [3, 4]
    #   │  norm = sqrt(3² + 4²) = sqrt(25) = 5
    #   │
    #   └─ Para embedding real: norm ≈ 1.5-2.5 típicamente
    
    if norm > 0:
        embedding = embedding / norm
        #   ├─ Divide cada elemento por la norma
        #   ├─ Ejemplo:
        #   │  embedding = [3/5, 4/5] = [0.6, 0.8]
        #   │
        #   └─ Ahora ||embedding|| = 1 exactamente
    
    return embedding
    # Retorna vector unitario: magnitud = 1
```

### ¿Por qué normalizar?

```
SIN normalización:
├─ embedding1 = [0.5, 0.3, 0.7, ...]  → norm ≈ 2.1
├─ embedding2 = [0.5, 0.3, 0.7, ...]  → norm ≈ 2.1
└─ ¿Son iguales? Sí, pero...
   El modelo podría aprender a generar
   embeddings de diferentes magnitudes

CON normalización L2:
├─ embedding1 = [0.238, 0.143, 0.333, ...]  → norm = 1.0
├─ embedding2 = [0.238, 0.143, 0.333, ...]  → norm = 1.0
└─ ¿Son iguales? Sí, y además:
   Todos los embeddings tienen magnitud 1
   Ahora solo importa la DIRECCIÓN, no la magnitud
   
VENTAJA: Distancia entre embeddings más consistente
```

### Ejemplo Numérico Completo

```
Embedding RAW de FaceNet:
embedding = [0.250, -0.180, 0.340, ..., -0.120]  ← 128 números
(valores varían, típicamente entre -1 y 1)

Cálculo de norma L2:
norm = sqrt(0.250² + (-0.180)² + 0.340² + ... + (-0.120)²)
     = sqrt(0.0625 + 0.0324 + 0.1156 + ... + 0.0144)
     = sqrt(aproximadamente 1.8)
     ≈ 1.34

Normalización L2:
embedding_normalizado = embedding / 1.34
                      = [0.250/1.34, -0.180/1.34, 0.340/1.34, ..., -0.120/1.34]
                      = [0.187, -0.134, 0.254, ..., -0.090]

Verificación:
norm_nuevo = sqrt(0.187² + (-0.134)² + 0.254² + ... + (-0.090)²)
           = sqrt(0.0349 + 0.0180 + 0.0645 + ... + 0.0081)
           = sqrt(exactamente 1.0)
           = 1.0 ✓
```

---

## 🔄 Flujo Completo Visual

```
╔═════════════════════════════════════════════════════════════════╗
║                  PROCESAMIENTO COMPLETO DE IMAGEN              ║
╚═════════════════════════════════════════════════════════════════╝

ENTRADA
   │
   ├─ Formato: Imagen física (640x480 aprox)
   ├─ Source: Cámara USB / Raspberry Pi Camera
   └─ Objetivo: Obtener embedding para comparar

PASO 1: OpenCV - capture_frame()
   │
   ├─ cv2.VideoCapture(0)
   ├─ cv2.cvtColor(BGR → RGB)
   └─ Image.fromarray()
   │
   └─> PIL.Image (cualquier tamaño, RGB)

PASO 2: MTCNN - Detector de Rostros
   │
   ├─ detector.detect_faces(img_array)
   ├─ Busca TODOS los rostros
   ├─ Retorna: caja delimitadora (x, y, w, h)
   └─ Extrae región del rostro
   │
   └─> numpy array (h, w, 3) - Solo rostro

PASO 3: PIL - Redimensionamiento
   │
   ├─ Image.fromarray(face)
   ├─ .resize((160, 160))
   ├─ np.asarray()
   ├─ np.expand_dims() → Batch de 1
   └─ (1, 160, 160, 3)
   │
   └─> numpy array (1, 160, 160, 3) - Listo para FaceNet

PASO 4: FaceNet - Generador de Embeddings
   │
   ├─ embedder.embeddings(face)
   ├─ Red neuronal convolucional
   ├─ 14+ capas entrenadas
   ├─ Extrae características faciales
   └─ Retorna: (1, 128)
   │
   ├─> embedding[0] = array de 128 números
   └─> Valores: típicamente entre -1 y 1

PASO 5: NumPy - Normalización L2
   │
   ├─ np.linalg.norm(embedding)
   ├─ Calcula ||v|| = sqrt(suma de cuadrados)
   ├─ embedding = embedding / norm
   └─ Resultado: vector unitario (magnitud = 1)
   │
   └─> embedding normalizado (128 números, ||v|| = 1)

SALIDA
   │
   └─ array de 128 números float32, normalizados L2
      Listo para guardar o comparar con otros embeddings
```

---

## 💾 Flujo en el Código Real

```python
def iniciar_registro():
    # Paso 1: Captura
    img, err = capture_frame()
    # → retorna PIL.Image
    
    # Paso 2-5: Procesa
    embedding = generarEmbedding(img)
    # → retorna array(128,) normalizado
    
    # Guarda
    save_embedding(embedding, "Nacho")
    # → guarda en embeddings.txt
```

---

## 📊 Tabla Resumen

| Paso | Función | Input | Processing | Output |
|------|---------|-------|-----------|--------|
| 1 | `capture_frame()` | Cámara USB | OpenCV VideoCapture | PIL.Image (RGB) |
| 2 | `generarEmbedding()` (MTCNN) | PIL.Image | Detección de rostro | array(h,w,3) |
| 3 | `generarEmbedding()` (PIL) | array(h,w,3) | Redimensiona 160x160 | array(1,160,160,3) |
| 4 | `generarEmbedding()` (FaceNet) | array(1,160,160,3) | Red neuronal | array(1,128) |
| 5 | `generarEmbedding()` (NumPy) | array(128) | Normalización L2 | array(128) normalizado |

---

## 🔍 Ejemplo Paso a Paso Real

```
Usuario presiona botón → iniciar_registro() se ejecuta

1️⃣ capture_frame():
   - Abre /dev/video0 (cámara)
   - Lee 1 frame: BGR (480, 640, 3) uint8
   - Convierte a RGB
   - Retorna: PIL.Image objeto

2️⃣ generarEmbedding() - MTCNN:
   - Detecta rostro en posición (100, 80, 200, 240)
   - Extrae región: img_array[80:320, 100:300]
   - Resultado: array (240, 200, 3)

3️⃣ generarEmbedding() - PIL:
   - Convierte a PIL.Image
   - Redimensiona a (160, 160)
   - Expande dims: (1, 160, 160, 3)

4️⃣ generarEmbedding() - FaceNet:
   - Pasa por 14 capas convolucionales
   - Extrae características
   - Retorna: array (1, 128)
     ejemplo: [0.23, -0.15, 0.42, ..., -0.08]
   - Toma [0]: array (128,)

5️⃣ generarEmbedding() - NumPy L2:
   - norm = sqrt(suma de (0.23² + (-0.15)² + ... + (-0.08)²))
          = 1.56
   - embedding = embedding / 1.56
   - Resultado: [0.147, -0.096, 0.269, ..., -0.051]
   - Nueva norm = 1.0 ✓

6️⃣ save_embedding():
   - Guarda en embeddings.txt:
     [0.147, -0.096, 0.269, ..., -0.051]
   - Guarda en names.txt:
     Nacho

✅ Registro completado
```

---

## 🎓 Puntos Clave

1. **OpenCV captura**: Imagen RGB estándar
2. **MTCNN detecta**: Dónde está el rostro
3. **PIL redimensiona**: A tamaño fijo (160x160)
4. **FaceNet convierte**: A "huella dactilar" (128 números)
5. **NumPy normaliza**: Para comparación consistente
6. **Resultado**: Vector de 128 números que representa características faciales únicas

---

## 🚀 Uso Posterior (Reconocimiento)

Cuando alguien timbra:

```python
# Procesa imagen igual que en registro
new_embedding = generarEmbedding(img)  # array(128,) normalizado

# Carga embeddings guardados
stored_embeddings, names = load_embeddings()

# Calcula distancias
distancias = [np.linalg.norm(new_embedding - emb) for emb in stored_embeddings]

# Encuentra similitud más cercana
min_dist = min(distancias)

if min_dist < 0.8:  # Si distancia < umbral
    print(f"Coincidencia: {names[idx]}")
else:
    print("No coincide")
```

**¿Por qué funciona?**
- Embeddings normalizados de rostros similares → distancia pequeña
- Embeddings de rostros diferentes → distancia grande

