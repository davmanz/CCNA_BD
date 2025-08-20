from django.shortcuts import render
from .models import SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion
import random
from django.http import HttpResponseRedirect
from .forms import CSVUploadForm
from .models import SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion
import csv

def exam_view(request):
    if request.method == "POST":
        correct_answers = 0
        total_questions = 0
        
        # Verificar las respuestas de las preguntas de selección única
        single_choice_questions = SingleChoiceQuestion.objects.all()
        for question in single_choice_questions:
            total_questions += 1
            user_answer = request.POST.get(f"question_{question.id}")
            if user_answer == question.answer:
                correct_answers += 1
        
        # Verificar las respuestas de las preguntas de selección múltiple
        multiple_choice_questions = MultipleChoiceQuestion.objects.all()
        for question in multiple_choice_questions:
            total_questions += 1
            user_answers = request.POST.getlist(f"question_{question.id}")
            correct_answers_list = question.answer.split("-")
            if sorted(user_answers) == sorted(correct_answers_list):
                correct_answers += 1
        
        # Verificar las respuestas de las preguntas drag and drop
        drag_and_drop_questions = DragAndDropQuestion.objects.all()
        for question in drag_and_drop_questions:
            total_questions += 1
            # Asumiendo que las respuestas correctas y del usuario están en formato JSON
            user_answers = request.POST.getlist(f"question_{question.id}")
            correct_answers_list = question.correct_answers
            if sorted(user_answers) == sorted(correct_answers_list):
                correct_answers += 1
        
        # Calcular el puntaje
        score = (correct_answers / total_questions) * 100
        context = {'score': score, 'correct_answers': correct_answers, 'total_questions': total_questions}
        return render(request, 'exam/results.html', context)
    
    else:
        # Obtener todas las preguntas de cada tipo
        single_choice_questions = SingleChoiceQuestion.objects.all()
        multiple_choice_questions = MultipleChoiceQuestion.objects.all()
        drag_and_drop_questions = DragAndDropQuestion.objects.all()

        # Mezclar preguntas aleatoriamente
        questions = list(single_choice_questions) + list(multiple_choice_questions) + list(drag_and_drop_questions)
        random.shuffle(questions)  # Mezclar las preguntas al azar

        context = {'questions': questions}
        return render(request, 'exam/index.html', context)

def upload_csv_view(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            question_type = row['question_type']
            answer = row['Answer']

            option_mapping = {
                'A': row['OptionA'],
                'B': row['OptionB'],
                'C': row['OptionC'],
                'D': row['OptionD'],
                'E': row['OptionE']
            }

            # Cargar las preguntas según su tipo
            if question_type == 'SINGLE':
                SingleChoiceQuestion.objects.create(
                    text=row['Question'],
                    option_a=option_mapping['A'],
                    option_b=option_mapping['B'],
                    option_c=option_mapping['C'],
                    option_d=option_mapping['D'],
                    option_e=option_mapping.get('E', ''),
                    answer=option_mapping[answer]  # Guardar la respuesta correcta como texto
                )
            elif question_type == 'MULTI':
                MultipleChoiceQuestion.objects.create(
                    text=row['Question'],
                    option_a=option_mapping['A'],
                    option_b=option_mapping['B'],
                    option_c=option_mapping['C'],
                    option_d=option_mapping['D'],
                    option_e=option_mapping.get('E', ''),
                    answer=row['Answer'],  # Guardar las respuestas correctas
                )
            elif question_type == 'DRAG':
                DragAndDropQuestion.objects.create(
                    text=row['Question'],
                    options=row['OptionA'],  # Opciones en formato JSON si es necesario
                    correct_answers=row['Answer'],  # Respuestas correctas en formato JSON
                )

        return HttpResponseRedirect('/admin/')  # Redirigir al panel de administración una vez cargado el CSV

    form = CSVUploadForm()  # Crear un formulario vacío
    return render(request, 'exam/upload_csv.html', {'form': form})