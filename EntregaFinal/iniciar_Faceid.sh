#!/bin/bash

# 1. Definir rutas (EDITA ESTO)
# Ejemplo: /home/pi/mi_entorno/bin/activate
RUTA_VENV="/home/grupoa3b/tensorflow_project/venv/bin/activate"

# Ejemplo: /home/pi/ProyectoCerradura
RUTA_PROYECTO="/home/grupoa3b/tensorflow_project/entregaFinal/TP2/EntregaFinal/"

# 2. Esperar un poco a que la red esté lista (opcional pero recomendado en RPi)
sleep 10

# 3. Ir al directorio del proyecto (CRITICO para que encuentre embeddings.txt)
cd "$RUTA_PROYECTO"

# 4. Activar el entorno virtual
source "$RUTA_VENV"

# 5. Ejecutar el script (usando python del venv activo
# Redirigimos logs a un archivo para poder depurar si falla
python FaceID.py > /home/grupoa3b/faceid_log.txt 2>&1
