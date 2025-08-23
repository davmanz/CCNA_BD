from django.db import models

class SingleChoiceQuestion(models.Model):
    np = models.CharField(max_length=20, unique=True)
    text = models.TextField()  # Pregunta
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    option_e = models.TextField(blank=True, null=True)
    answer = models.TextField()  # Respuesta correcta como texto
    has_image = models.BooleanField(default=False)  # ¿Tiene imagen?
    image_filename = models.CharField(max_length=100, blank=True, null=True)  # Nombre del archivo (ej: "1.png", "uid123.png")

    def __str__(self):
        return self.text

    @property
    def question_type(self):
        return 'SINGLE'
    
    @property
    def image_path(self):
        """Retorna la ruta completa de la imagen si existe"""
        if self.has_image and self.image_filename:
            return f'images/{self.image_filename}'
        return None


class MultipleChoiceQuestion(models.Model):
    np = models.CharField(max_length=20, unique=True)
    text = models.TextField()  # Pregunta
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    option_e = models.TextField(blank=True, null=True)
    answer = models.TextField()  # Puede ser "A-B" para varias respuestas correctas
    has_image = models.BooleanField(default=False)  # ¿Tiene imagen?
    image_filename = models.CharField(max_length=100, blank=True, null=True)  # Nombre del archivo

    def __str__(self):
        return self.text

    @property
    def question_type(self):
        return 'MULTI'
    
    @property
    def image_path(self):
        """Retorna la ruta completa de la imagen si existe"""
        if self.has_image and self.image_filename:
            return f'images/{self.image_filename}'
        return None


class DragAndDropQuestion(models.Model):
    np = models.CharField(max_length=20, unique=True)
    text = models.TextField()  # Pregunta
    options = models.JSONField()  # Lista de opciones a arrastrar
    correct_answers = models.JSONField()  # Respuestas correctas asociadas a cada opción
    has_image = models.BooleanField(default=False)  # ¿Tiene imagen?
    image_filename = models.CharField(max_length=100, blank=True, null=True)  # Nombre del archivo

    def __str__(self):
        return self.text

    @property
    def question_type(self):
        return 'DRAG'
    
    @property
    def image_path(self):
        """Retorna la ruta completa de la imagen si existe"""
        if self.has_image and self.image_filename:
            return f'images/{self.image_filename}'
        return None