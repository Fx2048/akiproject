# Imagen base con GROMACS preinstalado
FROM gromacs/gromacs:2023.1

# Instalar Python y dependencias
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar código
COPY app.py .
COPY md_engine.py .

# Crear directorios de trabajo
RUN mkdir -p /tmp/md_uploads /tmp/md_results

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "600", "app:app"]