from django.urls import path
from . import views  # Importar las vistas de la aplicación "questions"

urlpatterns = [
    path('', views.exam_view, name='examen'),  # Ruta para mostrar el examen
    path('cargar-csv/', views.upload_csv_view, name='upload_csv'),  # Ruta para cargar el CSV
]
