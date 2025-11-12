# 📸 Visualización de Cámara en la Interfaz Web

## ✨ Funcionalidades Agregadas

### 1. **Endpoints HTTP para imágenes**

- **`/api/camera/snapshot`**: Captura una nueva foto y la devuelve
- **`/api/camera/last`**: Devuelve la última foto capturada
- **`/api/camera/last_base64`**: Devuelve la última foto en formato base64 (JSON)
- **`/api/status`**: Información del sistema

### 2. **Vista en Tiempo Real**

La página web ahora muestra:
- Vista previa de la cámara en tiempo real
- Botón para actualizar manualmente la imagen
- Actualización automática cada 5 segundos

### 3. **Cómo Funciona**

1. Cada vez que se captura una imagen (registro o timbre), se guarda en memoria
2. La página web solicita la última imagen capturada vía HTTP
3. La imagen se actualiza automáticamente cada 5 segundos
4. Puedes hacer clic en "🔄 Actualizar" para refrescar manualmente

## 🚀 Uso

### En la Raspberry Pi:

```bash
# Activar entorno virtual
source ~/tensorflow_project/venv/bin/activate

# Configurar variables
export MQTT_BROKER=localhost
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000

# Ejecutar
python3 comprobarRostro.py
```

### Desde tu navegador:

Accede a: `http://192.168.0.199:5000` (o la IP de tu Raspberry)

Verás:
- Vista de la cámara en la parte superior
- Botones de control (Registrar, Tocar timbre)
- Resultados de reconocimiento facial

## 🔧 Probar los Endpoints

### Desde el navegador:

- **Ver última imagen**: `http://192.168.0.199:5000/api/camera/last`
- **Capturar nueva**: `http://192.168.0.199:5000/api/camera/snapshot`
- **Estado del sistema**: `http://192.168.0.199:5000/api/status`

### Desde la terminal (en la Raspberry o tu PC):

```bash
# Ver imagen con curl
curl http://192.168.0.199:5000/api/camera/last --output ultima_foto.jpg

# Ver estado
curl http://192.168.0.199:5000/api/status

# Obtener imagen en base64
curl http://192.168.0.199:5000/api/camera/last_base64
```

## 📝 Notas

- La imagen se guarda en memoria (no en disco)
- Solo se mantiene la última imagen capturada
- La calidad JPEG está configurada en 85% para balance entre calidad y tamaño
- La actualización automática puede pausarse si cierras la pestaña

## 🎨 Personalización

### Cambiar intervalo de actualización automática:

Edita `script.js`, línea con `setInterval`:

```javascript
// Cambiar de 5000ms (5 seg) a 10000ms (10 seg)
setInterval(refreshCamera, 10000);
```

### Deshabilitar actualización automática:

Comenta la línea en `script.js`:

```javascript
// setInterval(refreshCamera, 5000);
```

### Cambiar calidad de imagen:

Edita `comprobarRostro.py`, busca `IMWRITE_JPEG_QUALITY`:

```python
# Cambiar de 85 a 95 para mayor calidad (más tamaño)
ret, buffer = cv2.imencode('.jpg', last_captured_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
```
