import io
import csv
import json
import random
from .forms import CSVUploadForm
from django.shortcuts import render
from .models import SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect

def exam_view(request):
    """Vista principal - menú de opciones"""
    return render(request, 'exam/index.html')

def selection_exam_view(request):
    """Vista para preguntas de selección (SINGLE y MULTI)"""
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
        
        # Calcular el puntaje
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        context = {
            'score': score, 
            'correct_answers': correct_answers, 
            'total_questions': total_questions,
            'exam_type': 'selection'
        }
        return render(request, 'exam/results.html', context)
    
    else:
        # Obtener solo preguntas de selección (SINGLE y MULTI)
        single_choice_questions = SingleChoiceQuestion.objects.all()
        multiple_choice_questions = MultipleChoiceQuestion.objects.all()

        # Mezclar preguntas aleatoriamente
        questions = list(single_choice_questions) + list(multiple_choice_questions)
        random.shuffle(questions)

        context = {'questions': questions}
        return render(request, 'exam/selection_exam.html', context)

def drag_exam_view(request):
    """Vista para preguntas drag and drop"""
    if request.method == "POST":
        # Por ahora placeholder para cuando implementemos drag and drop
        correct_answers = 0
        total_questions = 0
        
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
            'total_questions': total_questions,
            'exam_type': 'drag'
        }
        return render(request, 'exam/results.html', context)
    
    else:
        # Por ahora mostrar página de "próximamente"
        return render(request, 'exam/drag_exam.html')

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

def study_mode(request):
    """
    Vista para el modo estudio - muestra preguntas con respuestas correctas
    Compatible con tus modelos: SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion
    """
    try:
        # Obtener preguntas de selección (como en tu selection_exam_view)
        single_choice_questions = SingleChoiceQuestion.objects.all()
        multiple_choice_questions = MultipleChoiceQuestion.objects.all()
        
        # Preparar datos para el template
        questions_data = []
        
        # Procesar preguntas de selección única
        for question in single_choice_questions:
            # Determinar cuál opción es la correcta
            correct_answers = []
            option_mapping = {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
                'E': question.option_e if question.option_e else None
            }
            
            # Encontrar la letra de la respuesta correcta
            for letter, option_text in option_mapping.items():
                if option_text == question.answer:
                    correct_answers.append(letter)
                    break
            
            questions_data.append({
                'id': question.id,
                'text': question.text,
                'question_type': 'SINGLE',
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'option_e': question.option_e if question.option_e else None,
                'correct_answers': correct_answers,
                'explanation': getattr(question, 'explanation', None),
                'has_image': getattr(question, 'has_image', False),
                'image_path': question.image_path
            })
        
        # Procesar preguntas de selección múltiple
        for question in multiple_choice_questions:
            # Las respuestas correctas están separadas por "-"
            correct_answer_texts = question.answer.split("-")
            correct_answers = []
            
            option_mapping = {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
                'E': question.option_e if question.option_e else None
            }
            
            # Encontrar las letras de las respuestas correctas
            for letter, option_text in option_mapping.items():
                if option_text in correct_answer_texts:
                    correct_answers.append(letter)
            
            questions_data.append({
                'id': question.id,
                'text': question.text,
                'question_type': 'MULTI',
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'option_e': question.option_e if question.option_e else None,
                'correct_answers': correct_answers,
                'explanation': getattr(question, 'explanation', None),
                'has_image': getattr(question, 'has_image', False),
                'image_path': question.image_path
            })
        
        # Mezclar preguntas aleatoriamente (como en tu vista original)
        random.shuffle(questions_data)
        
        context = {
            'questions': questions_data,
            'total_questions': len(questions_data),
            'mode': 'study'
        }
        
        return render(request, 'exam/study_exam.html', context)
        
    except Exception as e:
        # En caso de error, mostrar página con mensaje
        context = {
            'questions': [],
            'error_message': f'Error al cargar preguntas: {str(e)}'
        }
        return render(request, 'exam/study_exam.html', context)

def practice_exam_view(request):
    """
    Modo práctica: muestra preguntas con verificación inmediata vía AJAX.
    Reutiliza modelos actuales (SingleChoiceQuestion, MultipleChoiceQuestion).
    """
    # Cargar preguntas
    single_choice_questions = SingleChoiceQuestion.objects.all()
    multiple_choice_questions = MultipleChoiceQuestion.objects.all()

    # Unificamos para el template. Importante: NO incluir la respuesta correcta en HTML
    questions = []
    for q in single_choice_questions:
        questions.append({
            'id': q.id,
            'question_type': 'SINGLE',
            'text': q.text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'option_e': q.option_e,
            'has_image': q.has_image,
            'image_path': q.image_path,
        })
    for q in multiple_choice_questions:
        questions.append({
            'id': q.id,
            'question_type': 'MULTI',
            'text': q.text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'option_e': q.option_e,
            'has_image': q.has_image,
            'image_path': q.image_path,
        })

    import random
    random.shuffle(questions)

    return render(request, 'exam/practice_exam.html', {'questions': questions})

@require_POST
def check_answer_api(request):
    """
    Endpoint de verificación inmediata.
    Espera:
      - question_id (int)
      - question_type ('SINGLE' | 'MULTI')
      - answer: para SINGLE -> 'A'|'B'|'C'|'D'|'E'
                para MULTI  -> lista de letras ['A','D',...]
    Respuesta:
      { correct: bool, correct_letters: ['B'] o ['A','D'], explain: str|null }
    """
    try:
        qid = int(request.POST.get('question_id', '').strip())
        qtype = (request.POST.get('question_type', '') or '').strip().upper()
        if not qid or qtype not in ('SINGLE', 'MULTI'):
            return HttpResponseBadRequest('Invalid payload')

        if qtype == 'SINGLE':
            user_letter = (request.POST.get('answer', '') or '').strip().upper()
            if user_letter not in ('A','B','C','D','E'):
                return HttpResponseBadRequest('Invalid answer for SINGLE')

            q = SingleChoiceQuestion.objects.get(id=qid)

            option_mapping = {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d,
                'E': q.option_e
            }
            # Verdadero si el texto de la letra elegida coincide con la respuesta guardada
            is_correct = (option_mapping.get(user_letter) == q.answer)

            # Hallar la(s) letra(s) correcta(s) (en SINGLE será 1 letra)
            correct_letters = []
            for letter, text in option_mapping.items():
                if text == q.answer:
                    correct_letters.append(letter)
                    break

            return JsonResponse({
                'correct': is_correct,
                'correct_letters': correct_letters,
                'explain': getattr(q, 'explanation', None)
            })

        elif qtype == 'MULTI':
            # answer puede llegar como lista (JS) o como string 'A,B'
            ans = request.POST.getlist('answer')
            if not ans:
                # intentar coma-separado
                raw = (request.POST.get('answer', '') or '').strip()
                ans = [x.strip().upper() for x in raw.split(',') if x.strip()]
            user_letters = sorted({x for x in ans if x in ('A','B','C','D','E')})
            if not user_letters:
                return HttpResponseBadRequest('Invalid answer list for MULTI')

            q = MultipleChoiceQuestion.objects.get(id=qid)

            option_mapping = {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d,
                'E': q.option_e
            }

            # En tu almacenamiento, MultipleChoiceQuestion.answer es textos unidos por "-"
            correct_texts = [t.strip() for t in q.answer.split('-') if t.strip()]
            # Mapear letras correctas comparando textos
            correct_letters = []
            for letter, text in option_mapping.items():
                if text and text in correct_texts:
                    correct_letters.append(letter)
            correct_letters = sorted(correct_letters)

            is_correct = (sorted(user_letters) == correct_letters)

            return JsonResponse({
                'correct': is_correct,
                'correct_letters': correct_letters,
                'explain': getattr(q, 'explanation', None)
            })

    except (ValueError, SingleChoiceQuestion.DoesNotExist, MultipleChoiceQuestion.DoesNotExist) as e:
        return HttpResponseBadRequest(f'Error: {str(e)}')

