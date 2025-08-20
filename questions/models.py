from django.db import models

class SingleChoiceQuestion(models.Model):
    text = models.TextField()  # Pregunta
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    option_e = models.CharField(max_length=255, blank=True, null=True)
    answer = models.CharField(max_length=255)  # Respuesta correcta como texto (Amarillo, Rojo, etc.)

    def __str__(self):
        return self.text

    @property
    def question_type(self):
        return 'SINGLE'


class MultipleChoiceQuestion(models.Model):
    text = models.TextField()  # Pregunta
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    option_e = models.CharField(max_length=255, blank=True, null=True)
    answer = models.CharField(max_length=255)  # Puede ser "A-B" para varias respuestas correctas

    def __str__(self):
        return self.text

    @property
    def question_type(self):
        return 'MULTI'


class DragAndDropQuestion(models.Model):
    text = models.TextField()  # Pregunta
    options = models.JSONField()  # Lista de opciones a arrastrar
    correct_answers = models.JSONField()  # Respuestas correctas asociadas a cada opción

    def __str__(self):
        return self.text

    @property
    def question_type(self):
        return 'DRAG'
