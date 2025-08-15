# Usa una imagen base oficial de Python más ligera
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Asegura que la salida de Python se muestre en la terminal sin buffer
ENV PYTHONUNBUFFERED=1

# Instala solo las dependencias esenciales del sistema
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    default-libmysqlclient-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia e instala las dependencias primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instala las dependencias con optimizaciones de espacio
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación al contenedor
COPY . .

# Damos permisos de ejecución
RUN chmod +x wait-for-db.sh

# Limpia archivos temporales para reducir el tamaño de la imagen
RUN find /usr/local -name '*.pyc' -delete && \
    find /usr/local -name '__pycache__' -delete

