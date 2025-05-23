# Dockerfile

# Imagen base con Python
FROM python:3.10-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias
RUN pip install --no-cache-dir fastapi uvicorn pandas

# Exponer puerto requerido por el challenge
EXPOSE 8888

# Comando por defecto para lanzar la API
CMD ["uvicorn", "production_planner:app", "--host", "0.0.0.0", "--port", "8888"]
