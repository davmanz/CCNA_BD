from django.contrib import admin
from django.urls import path, include  # Importar 'include' para incluir las URLs de la aplicación 'questions'
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('questions.urls')),  # Incluir las URLs de la aplicación 'questions'
]

# Servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)