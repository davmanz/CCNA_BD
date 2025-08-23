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

# Copiar el script de entrada al contenedor
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

# Dar permisos de ejecución al script
RUN chmod +x /usr/src/app/entrypoint.sh

# Exponer el puerto en el que correrá Gunicorn
EXPOSE 8000

# Comando para ejecutar la aplicación (usando el entrypoint)
CMD ["/usr/src/app/entrypoint.sh"]
