# questions/forms.py
from django import forms

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()  # Campo para subir el archivo CSV
