#!/bin/bash

# Ejecutar las migraciones
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py createsuperuser --username admin --password admin --email admin@admin.com