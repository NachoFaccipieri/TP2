Optimización para Raspberry Pi con 1GB RAM

Esta guía rápida contiene recomendaciones para que `comprobarRostro.py` pueda correr en una Raspberry Pi con poca memoria.

1) Aumentar swap (recomendado)

Si la Pi tiene 1GB de RAM, TensorFlow puede quedarse sin memoria. Crear un swapfile de 1-2GB puede ayudar:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Para hacerlo persistente:
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

2) Ejecutar en virtualenv y usar dependencias mínimas

Crear y activar un virtualenv reduce conflictos:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requeriments.txt
```

3) Limitar hilos y logs de TensorFlow

En `comprobarRostro.py` ya agregamos las variables de entorno antes de importar TF/keras:

- `TF_CPP_MIN_LOG_LEVEL=2` reduce logs
- `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `INTRA_OP_NUM_THREADS=1`, `INTER_OP_NUM_THREADS=1` limitan hilos

También seteamos estas variables en el unit file systemd.

4) Considerar modelos más ligeros o alternativas

Las librerías `mtcnn` + `keras-facenet` usan TensorFlow y consumen mucha memoria. Opciones:

- Usar un servicio externo más potente para el modelado (si está disponible).
- Experimentar con modelos tflite o herramientas más ligeras (requiere adaptación).

5) Arranque automático y supervisión

Agregar el service systemd (docs/systemd_comprobarrostro.service). Ajustá `WorkingDirectory` y `ExecStart` según la ubicación del proyecto y del intérprete de Python (virtualenv si usás uno).

6) Logs y debugging

- Consultá logs con: `sudo journalctl -u comprobarrostro.service -f`.
- Si falla al cargar TF (out-of-memory), verás errores en el log; entonces aumentá swap o bajar el tamaño de batch si corresponde.

7) Recomendación práctica para pruebas locales

Si tenés problemas con memoria, probá primero en tu PC local (más RAM) y una vez que funcione, mové a la Pi y usá swap + límites de hilos o considerá usar un Pi con más memoria.

Si querés, genero una variante que use un detector más ligero (p. ej. Haar cascades) y un pipeline de comparación simple — esto puede funcionar con menos RAM pero afectará la calidad del reconocimiento. ¿Querés que prepare esa variante ligera como fallback?
