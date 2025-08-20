from django.contrib import admin
from django.urls import path, include  # Importar 'include' para incluir las URLs de la aplicación 'questions'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('questions.urls')),  # Incluir las URLs de la aplicación 'questions'
]
