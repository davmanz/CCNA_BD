import io
import csv
import json
import random
from .forms import CSVUploadForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion

def exam_view(request):
    if request.method == "POST":
        correct_answers = 0
        total_questions = 0
        
        # Verificar las respuestas de las preguntas de selección única
        single_choice_questions = SingleChoiceQuestion.objects.all()
        for question in single_choice_questions:
            total_questions += 1
            user_answer = request.POST.get(f"question_{question.id}")
            
            # Mapear la letra a la opción correspondiente
            option_mapping = {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
                'E': question.option_e
            }
            
            if user_answer and option_mapping.get(user_answer) == question.answer:
                correct_answers += 1
        
        # Verificar las respuestas de las preguntas de selección múltiple
        multiple_choice_questions = MultipleChoiceQuestion.objects.all()
        for question in multiple_choice_questions:
            total_questions += 1
            user_answers = request.POST.getlist(f"question_{question.id}")
            correct_answers_list = question.answer.split("-")
            
            # Mapear las letras a opciones
            user_options = []
            option_mapping = {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
                'E': question.option_e
            }
            
            for answer in user_answers:
                if answer in option_mapping:
                    user_options.append(option_mapping[answer])
            
            correct_options = []
            for answer in correct_answers_list:
                if answer in option_mapping:
                    correct_options.append(option_mapping[answer])
            
            if sorted(user_options) == sorted(correct_options):
                correct_answers += 1
        
        # Verificar las respuestas de las preguntas drag and drop
        drag_and_drop_questions = DragAndDropQuestion.objects.all()
        for question in drag_and_drop_questions:
            total_questions += 1
            user_answers_json = request.POST.get(f"question_{question.id}")
            
            if user_answers_json:
                try:
                    user_answers = json.loads(user_answers_json)
                    if sorted(user_answers) == sorted(question.correct_answers):
                        correct_answers += 1
                except json.JSONDecodeError:
                    pass  # Respuesta inválida
        
        # Calcular el puntaje
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        context = {
            'score': score, 
            'correct_answers': correct_answers, 
            'total_questions': total_questions
        }
        return render(request, 'exam/results.html', context)
    
    else:
        # Obtener todas las preguntas de cada tipo
        single_choice_questions = SingleChoiceQuestion.objects.all()
        multiple_choice_questions = MultipleChoiceQuestion.objects.all()
        drag_and_drop_questions = DragAndDropQuestion.objects.all()

        # Mezclar preguntas aleatoriamente
        questions = list(single_choice_questions) + list(multiple_choice_questions) + list(drag_and_drop_questions)
        random.shuffle(questions)

        context = {'questions': questions}
        return render(request, 'exam/index.html', context)

def upload_csv_view(request):
    # Confirmación para aplicar cambios
    if request.method == 'POST' and request.POST.get('confirm') == '1':
        proposed = json.loads(request.POST['proposed_changes'])
        created = updated = 0

        for item in proposed:
            qtype = item['question_type']
            np_code = item['np']
            payload = item['new']  # datos ya normalizados

            if qtype == 'SINGLE':
                obj, created_flag = SingleChoiceQuestion.objects.get_or_create(np=np_code, defaults=payload)
                if not created_flag:
                    for k, v in payload.items():
                        setattr(obj, k, v)
                    obj.save()
                created += int(created_flag)
                updated += int(not created_flag)

            elif qtype == 'MULTI':
                obj, created_flag = MultipleChoiceQuestion.objects.get_or_create(np=np_code, defaults=payload)
                if not created_flag:
                    for k, v in payload.items():
                        setattr(obj, k, v)
                    obj.save()
                created += int(created_flag)
                updated += int(not created_flag)

            elif qtype == 'DRAG':
                obj, created_flag = DragAndDropQuestion.objects.get_or_create(np=np_code, defaults=payload)
                if not created_flag:
                    for k, v in payload.items():
                        setattr(obj, k, v)
                    obj.save()
                created += int(created_flag)
                updated += int(not created_flag)

        msg = f"✅ Cambios aplicados: {created} creadas, {updated} actualizadas"
        return render(request, 'exam/upload_csv.html', {'form': CSVUploadForm(), 'success_message': msg})

    # Subida/validación inicial del CSV
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            csv_content = csv_file.read().decode('utf-8')
            validation_errors = validate_csv_content(csv_content)
            if validation_errors:
                return render(request, 'exam/upload_csv.html', {'form': CSVUploadForm(), 'validation_errors': validation_errors})

            reader = csv.DictReader(io.StringIO(csv_content), quotechar='"')
            proposed_changes = []  # lista de {row, np, question_type, action, diff, new}

            for idx, row in enumerate(reader, start=2):  # empieza en 2 por cabecera
                qtype = row['question_type'].strip().upper()
                answer_raw = row['Answer'].strip()
                has_image = row.get('Image', '0').strip() == '1'
                np_code = row.get('NP', '').strip()  # <-- clave

                # Derivar image_filename
                image_filename = None
                if has_image:
                    if 'ImageFile' in row and row['ImageFile'].strip():
                        image_filename = row['ImageFile'].strip()
                    elif np_code:
                        image_filename = f"{np_code.replace('Q','')}.png"

                # Normalizar opciones
                opt = {
                    'A': row['OptionA'],
                    'B': row['OptionB'],
                    'C': row['OptionC'],
                    'D': row['OptionD'],
                    'E': row.get('OptionE', '')
                }

                # Construir payload "new" homogéneo según tipo
                if qtype == 'SINGLE':
                    payload = {
                        'np': np_code,
                        'text': row['Question'],
                        'option_a': opt['A'],
                        'option_b': opt['B'],
                        'option_c': opt['C'],
                        'option_d': opt['D'],
                        'option_e': opt.get('E', ''),
                        'answer': opt[answer_raw],  # letra -> texto
                        'has_image': has_image,
                        'image_filename': image_filename
                    }
                    try:
                        obj = SingleChoiceQuestion.objects.get(np=np_code)
                        action, diff = _diff_model(obj, payload, fields=[
                            'text','option_a','option_b','option_c','option_d','option_e','answer','has_image','image_filename'
                        ])
                    except SingleChoiceQuestion.DoesNotExist:
                        obj = None
                        action, diff = 'CREATE', payload  # todo el payload

                elif qtype == 'MULTI':
                    letters = [x.strip() for x in answer_raw.split('-')]
                    answer_texts = [opt[l] for l in letters if l in opt]
                    payload = {
                        'np': np_code,
                        'text': row['Question'],
                        'option_a': opt['A'],
                        'option_b': opt['B'],
                        'option_c': opt['C'],
                        'option_d': opt['D'],
                        'option_e': opt.get('E', ''),
                        'answer': '-'.join(answer_texts),
                        'has_image': has_image,
                        'image_filename': image_filename
                    }
                    try:
                        obj = MultipleChoiceQuestion.objects.get(np=np_code)
                        action, diff = _diff_model(obj, payload, fields=[
                            'text','option_a','option_b','option_c','option_d','option_e','answer','has_image','image_filename'
                        ])
                    except MultipleChoiceQuestion.DoesNotExist:
                        obj = None
                        action, diff = 'CREATE', payload

                elif qtype == 'DRAG':
                    options = json.loads(row['OptionA'])
                    correct_answers = json.loads(row['Answer'])
                    payload = {
                        'np': np_code,
                        'text': row['Question'],
                        'options': options,
                        'correct_answers': correct_answers,
                        'has_image': has_image,
                        'image_filename': image_filename
                    }
                    try:
                        obj = DragAndDropQuestion.objects.get(np=np_code)
                        action, diff = _diff_model(obj, payload, fields=[
                            'text','options','correct_answers','has_image','image_filename'
                        ])
                    except DragAndDropQuestion.DoesNotExist:
                        obj = None
                        action, diff = 'CREATE', payload
                else:
                    continue  # tipo no válido, ya lo filtró validate

                if action in ('CREATE','UPDATE'):
                    proposed_changes.append({
                        'row': idx,
                        'np': np_code,
                        'question_type': qtype,
                        'action': action,
                        'diff': diff,   # en UPDATE: {campo: {"old":..., "new":...}}
                        'new': payload  # para aplicar si confirman
                    })

            # Mostrar pantalla de confirmación
            return render(request, 'exam/upload_csv.html', {
                'form': CSVUploadForm(),
                'proposed_changes': proposed_changes,
                'pending_confirmation': True,
                'proposed_changes_json': json.dumps(proposed_changes, ensure_ascii=False)
            })

        except Exception as e:
            return render(request, 'exam/upload_csv.html', {'form': CSVUploadForm(), 'error': f'Error procesando el archivo CSV: {str(e)}'})

    # GET o sin archivo
    return render(request, 'exam/upload_csv.html', {'form': CSVUploadForm()})


def _diff_model(obj, payload, fields):
    """Compara obj vs payload y devuelve ('UPDATE', diff) o ('SKIP', {})"""
    if obj is None:
        return 'CREATE', payload
    diff = {}
    for f in fields:
        old = getattr(obj, f)
        new = payload[f]
        if old != new:
            diff[f] = {"old": old, "new": new}
    return ('UPDATE', diff) if diff else ('SKIP', {})

def validate_csv_content(csv_content):
    """Valida el contenido del CSV antes de cargarlo"""
    errors = []
    
    try:
        reader = csv.DictReader(io.StringIO(csv_content), quotechar='"')
        
        # Verificar columnas requeridas básicas
        required_columns = ['Question', 'OptionA', 'OptionB', 'OptionC', 'OptionD', 'Answer', 'question_type', 'Image']
        missing_columns = [col for col in required_columns if col not in reader.fieldnames]
        
        if missing_columns:
            errors.append(f"❌ Columnas faltantes: {', '.join(missing_columns)}")
            return errors
        
        # Verificar si hay columna ImageFile para nombres personalizados
        has_imagefile_column = 'ImageFile' in reader.fieldnames
        has_np_column = 'NP' in reader.fieldnames
        
        if not has_imagefile_column and not has_np_column:
            errors.append("❌ Se requiere al menos una columna 'ImageFile' (nombre del archivo) o 'NP' (número de pregunta)")
            return errors
        
        # Validar cada fila
        row_number = 1
        for row in reader:
            row_number += 1
            row_errors = []
            
            # Validar que no esté vacía la pregunta
            if not row['Question'].strip():
                row_errors.append("Pregunta vacía")
            
            # Validar question_type
            question_type = row['question_type'].strip().upper()
            if question_type not in ['SINGLE', 'MULTI', 'DRAG']:
                row_errors.append(f"question_type inválido: '{question_type}' (debe ser SINGLE, MULTI o DRAG)")
            
            # Validar Image (debe ser 0 o 1)
            image_value = row.get('Image', '').strip()
            if image_value not in ['0', '1']:
                row_errors.append(f"Image debe ser 0 o 1, encontrado: '{image_value}'")
            
            # Si tiene imagen, validar que haya nombre de archivo
            if image_value == '1':
                has_filename = False
                if has_imagefile_column and row.get('ImageFile', '').strip():
                    has_filename = True
                elif has_np_column and row.get('NP', '').strip():
                    has_filename = True
                
                if not has_filename:
                    row_errors.append("Si Image=1, debe especificar ImageFile o NP para determinar el archivo")
            
            # Validar opciones básicas
            if not row['OptionA'].strip():
                row_errors.append("OptionA vacía")
            if not row['OptionB'].strip():
                row_errors.append("OptionB vacía")
            if not row['OptionC'].strip():
                row_errors.append("OptionC vacía")
            if not row['OptionD'].strip():
                row_errors.append("OptionD vacía")
            
            # Validar Answer según el tipo
            answer = row['Answer'].strip()
            if question_type == 'SINGLE':
                if answer not in ['A', 'B', 'C', 'D', 'E']:
                    row_errors.append(f"Answer inválido para SINGLE: '{answer}' (debe ser A, B, C, D o E)")
            
            elif question_type == 'MULTI':
                if '-' not in answer:
                    row_errors.append(f"Answer inválido para MULTI: '{answer}' (debe tener formato A-B-C)")
                else:
                    answer_letters = answer.split('-')
                    for letter in answer_letters:
                        if letter.strip() not in ['A', 'B', 'C', 'D', 'E']:
                            row_errors.append(f"Letra inválida en MULTI: '{letter}' (debe ser A, B, C, D o E)")
            
            elif question_type == 'DRAG':
                try:
                    json.loads(row['OptionA'])
                    json.loads(row['Answer'])
                except json.JSONDecodeError:
                    row_errors.append("DRAG requiere JSON válido en OptionA y Answer")
            
            # Si hay errores en esta fila, agregarlos
            if row_errors:
                errors.append(f"🔴 Línea {row_number}: {'; '.join(row_errors)}")
        
        # Límite de errores mostrados
        if len(errors) > 10:
            errors = errors[:10]
            errors.append("... (más errores omitidos)")
            
    except Exception as e:
        errors.append(f"❌ Error leyendo CSV: {str(e)}")
    
    return errors