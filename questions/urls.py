from django.urls import path
from . import views  # Importar las vistas de la aplicación "questions"

urlpatterns = [
    path('', views.exam_view, name='examen'),  # Página principal con menú
    path('seleccion/', views.selection_exam_view, name='selection_exam'),  # Preguntas de selección
    path('drag-drop/', views.drag_exam_view, name='drag_exam'),  # Preguntas drag and drop
    path('cargar-csv/', views.upload_csv_view, name='upload_csv'),  # Ruta para cargar el CSV
    path('estudio/', views.study_mode, name='study_mode'),  # Ruta para el modo estudio
    path('practica/', views.practice_exam_view, name='practice_exam'),
    path('api/check-answer/', views.check_answer_api, name='check_answer_api'),
]
