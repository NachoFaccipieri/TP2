FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema (ajustar si faltan librerías para tu modelo)
RUN apt-get update && \
    apt-get install -y build-essential libgl1 libglib2.0-0 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "regRostro.py"]