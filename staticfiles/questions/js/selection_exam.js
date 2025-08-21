// selection_exam.js - Funcionalidad Mejorada
document.addEventListener('DOMContentLoaded', () => {
    const questions = Array.from(document.querySelectorAll('.question'));
    if (!questions.length) return;

    let current = 0;
    const total = questions.length;

    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const finishBtn = document.getElementById('finishBtn');
    const counterEl = document.getElementById('counter');
    const answeredEl = document.getElementById('answered');
    const progressEl = document.getElementById('pageProgress');
    const form = document.getElementById('examForm');

    // Cache de imágenes cargadas
    const imageCache = new Map();

    // Función para cargar imagen progresivamente
    const loadImage = async (questionIndex) => {
        const question = questions[questionIndex];
        if (!question) return;

        const imageElement = question.querySelector('.question-image img');
        if (!imageElement || imageCache.has(questionIndex)) return;

        const imageSrc = imageElement.src;
        if (!imageSrc || imageSrc.includes('data:') || imageSrc === '') return;

        try {
            // Crear loader si no existe
            let loader = question.querySelector('.image-loader');
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'image-loader';
                loader.innerHTML = '<div class="loader-spinner"></div>';
                
                const imageContainer = question.querySelector('.question-image');
                if (imageContainer) {
                    imageContainer.prepend(loader);
                    imageElement.style.display = 'none';
                }
            }

            // Precargar imagen
            const img = new Image();
            
            img.onload = () => {
                // Crear contenedor con efecto
                const container = document.createElement('div');
                container.className = 'image-container';
                
                const newImg = imageElement.cloneNode(true);
                newImg.style.opacity = '0';
                newImg.style.transition = 'opacity 0.5s ease';
                newImg.style.display = 'block';
                container.appendChild(newImg);
                
                // Reemplazar loader con imagen
                if (loader && loader.parentNode) {
                    loader.replaceWith(container);
                }
                
                // Fade in effect
                setTimeout(() => {
                    newImg.style.opacity = '1';
                }, 100);

                imageCache.set(questionIndex, container);
            };

            img.onerror = () => {
                // Si falla, ocultar el contenedor de imagen
                if (loader && loader.parentNode) {
                    loader.style.display = 'none';
                }
                console.warn(`Error loading image for question ${questionIndex + 1}`);
            };

            img.src = imageSrc;
            
        } catch (error) {
            console.error('Error in loadImage:', error);
        }
    };

    // Precargar imagen actual y siguiente
    const preloadImages = (currentIndex) => {
        loadImage(currentIndex);
        if (currentIndex + 1 < total) {
            setTimeout(() => loadImage(currentIndex + 1), 300);
        }
    };

    const isAnswered = (fieldset) => {
        const inputs = fieldset.querySelectorAll('input[type="radio"], input[type="checkbox"]');
        const name = inputs.length ? inputs[0].name : null;
        if (!name) return false;
        
        if (inputs[0].type === 'radio') {
            return [...inputs].some(i => i.checked);
        }
        return [...inputs].some(i => i.checked);
    };

    const countAnswered = () =>
        questions.reduce((acc, q) => acc + (isAnswered(q) ? 1 : 0), 0);

    const updateProgress = () => {
        // Actualizar contadores con formato mejorado
        const currentNum = current + 1;
        const answeredCount = countAnswered();
        
        counterEl.innerHTML = `<div class="stat-number">${currentNum}</div><div class="stat-label">Pregunta Actual</div>`;
        answeredEl.innerHTML = `<div class="stat-number">${answeredCount}</div><div class="stat-label">Respondidas</div>`;
        
        const pct = Math.round(((current + 1) / total) * 100);
        progressEl.style.width = `${pct}%`;

        // Actualizar botones
        prevBtn.disabled = current === 0;
        const isLast = current === total - 1;
        nextBtn.classList.toggle('hidden', isLast);
        finishBtn.classList.toggle('hidden', !isLast);
    };

    const show = (idx) => {
        questions.forEach((q, i) => {
            q.classList.toggle('hidden', i !== idx);
            q.classList.toggle('active', i === idx);
        });
        current = idx;
        updateProgress();
        preloadImages(idx);

        // Smooth scroll a la pregunta activa con delay
        setTimeout(() => {
            const activeQuestion = document.querySelector('.question.active');
            if (activeQuestion) {
                activeQuestion.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }, 100);
    };

    const validateCurrent = () => {
        const q = questions[current];
        if (isAnswered(q)) return true;

        // Animación shake mejorada
        q.classList.add('shake');
        setTimeout(() => q.classList.remove('shake'), 500);

        // Mensaje de validación mejorado
        const existing = q.querySelector('.validation-hint');
        if (!existing) {
            const hint = document.createElement('div');
            hint.className = 'validation-hint';
            hint.innerHTML = '⚠️ Selecciona al menos una opción para continuar.';
            q.appendChild(hint);
            setTimeout(() => {
                if (hint.parentNode) {
                    hint.remove();
                }
            }, 3000);
        }
        return false;
    };

    // Event listeners principales
    prevBtn.addEventListener('click', () => {
        if (current > 0) show(current - 1);
    });

    nextBtn.addEventListener('click', () => {
        if (!validateCurrent()) return;
        if (current < total - 1) show(current + 1);
    });

    // Manejo del envío del formulario
    form.addEventListener('submit', (e) => {
        if (!validateCurrent()) {
            e.preventDefault();
            return;
        }
        // El formulario se enviará normalmente a Django
    });

    // Feedback visual mejorado para respuestas seleccionadas
    form.addEventListener('change', (e) => {
        if (e.target.matches('input[type="radio"], input[type="checkbox"]')) {
            updateProgress();
            
            // Añadir feedback visual para opciones seleccionadas
            const option = e.target.closest('.option');
            const allOptions = option.parentNode.querySelectorAll('.option');
            
            if (e.target.type === 'radio') {
                // Para radio buttons, solo uno puede estar seleccionado
                allOptions.forEach(opt => opt.classList.remove('selected'));
                if (e.target.checked) {
                    option.classList.add('selected');
                }
            } else {
                // Para checkboxes, múltiples pueden estar seleccionados
                option.classList.toggle('selected', e.target.checked);
            }

            // Efecto de confirmación
            option.style.transform = 'scale(1.02)';
            setTimeout(() => {
                option.style.transform = '';
            }, 150);
        }
    });

    // Navegación por teclado mejorada
    document.addEventListener('keydown', (e) => {
        // Solo si no estamos escribiendo en un input
        if (e.target.tagName === 'INPUT') return;

        switch(e.key) {
            case 'ArrowRight':
                if (current < total - 1 && validateCurrent()) {
                    e.preventDefault();
                    show(current + 1);
                }
                break;
            case 'ArrowLeft':
                if (current > 0) {
                    e.preventDefault();
                    show(current - 1);
                }
                break;
            case 'Enter':
                if (e.target.closest('.option')) {
                    e.preventDefault();
                    const input = e.target.closest('.option').querySelector('input');
                    if (input) {
                        input.checked = !input.checked;
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
                break;
        }
    });

    // Mejorar la experiencia de hover en opciones
    const addOptionInteractivity = () => {
        questions.forEach(question => {
            const options = question.querySelectorAll('.option');
            options.forEach(option => {
                option.addEventListener('mouseenter', () => {
                    option.style.transform = 'translateY(-2px)';
                });
                
                option.addEventListener('mouseleave', () => {
                    if (!option.classList.contains('selected')) {
                        option.style.transform = '';
                    }
                });
            });
        });
    };

    // Inicialización mejorada
    const initialize = () => {
        // Configurar formato mejorado del progreso inicial
        counterEl.className = 'stat-card';
        answeredEl.className = 'stat-card';
        
        // Añadir clase total para mostrar información adicional
        const totalInfo = document.createElement('div');
        totalInfo.className = 'stat-card';
        totalInfo.innerHTML = `<div class="stat-number">${total}</div><div class="stat-label">Total Preguntas</div>`;
        
        // Insertar después del contador de respondidas
        if (answeredEl.parentNode) {
            answeredEl.parentNode.insertBefore(totalInfo, answeredEl.nextSibling);
        }

        addOptionInteractivity();
        show(0);
        
        console.log(`Examen inicializado: ${total} preguntas cargadas`);
    };

    // Inicializar todo
    initialize();
});