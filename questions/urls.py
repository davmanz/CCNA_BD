from django.urls import path
from . import views  # Importar las vistas de la aplicación "questions"

urlpatterns = [
    path('', views.exam_view, name='examen'),  # Página principal con menú
    path('seleccion/', views.selection_exam_view, name='selection_exam'),  # Preguntas de selección
    path('drag-drop/', views.drag_exam_view, name='drag_exam'),  # Preguntas drag and drop
    path('cargar-csv/', views.upload_csv_view, name='upload_csv'),  # Ruta para cargar el CSV
]
