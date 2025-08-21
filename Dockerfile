# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establecer el directorio de trabajo
WORKDIR /usr/src/app

# Instalar dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Exponer el puerto en el que correrá Gunicorn
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "ccna_exam.wsgi:application", "--bind", "0.0.0.0:8000"]
