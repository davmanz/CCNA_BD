// study_exam.js - Funcionalidad Modo Estudio
document.addEventListener('DOMContentLoaded', () => {
    const questions = Array.from(document.querySelectorAll('.question'));
    if (!questions.length) return;

    let current = 0;
    const total = questions.length;

    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const finishBtn = document.getElementById('finishBtn');
    const counterEl = document.getElementById('counter');
    const progressEl = document.getElementById('pageProgress');

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

    const updateProgress = () => {
        // Actualizar contador con formato mejorado
        const currentNum = current + 1;
        
        counterEl.innerHTML = `<div class="stat-number">${currentNum}</div><div class="stat-label">Pregunta Actual</div>`;
        
        const pct = Math.round(((current + 1) / total) * 100);
        progressEl.style.width = `${pct}%`;

        // Actualizar botones
        prevBtn.disabled = current === 0;
        const isLast = current === total - 1;
        nextBtn.classList.toggle('hidden', isLast);
        finishBtn.classList.toggle('hidden', !isLast);
    };

    const show = (idx) => {
        // Remover clase active de todas las preguntas
        questions.forEach((q, i) => {
            q.classList.toggle('hidden', i !== idx);
            q.classList.toggle('active', i === idx);
        });
        
        current = idx;
        updateProgress();
        preloadImages(idx);
        
        // Animar las opciones de la pregunta actual
        const activeQuestion = questions[current];
        if (activeQuestion) {
            const options = activeQuestion.querySelectorAll('.option');
            options.forEach((option, index) => {
                option.style.animationDelay = `${index * 0.1}s`;
                option.classList.remove('fadeInOption');
                // Force reflow
                option.offsetHeight;
                option.classList.add('fadeInOption');
            });
        }

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

    // Event listeners principales
    prevBtn.addEventListener('click', () => {
        if (current > 0) {
            addTransitionEffect('prev');
            setTimeout(() => show(current - 1), 150);
        }
    });

    nextBtn.addEventListener('click', () => {
        if (current < total - 1) {
            addTransitionEffect('next');
            setTimeout(() => show(current + 1), 150);
        }
    });

    // Finalizar estudio
    finishBtn.addEventListener('click', () => {
        showCompletionMessage();
    });

    // Efecto de transición entre preguntas
    const addTransitionEffect = (direction) => {
        const activeQuestion = document.querySelector('.question.active');
        if (activeQuestion) {
            const slideClass = direction === 'next' ? 'slide-out-left' : 'slide-out-right';
            activeQuestion.classList.add(slideClass);
            
            setTimeout(() => {
                activeQuestion.classList.remove(slideClass);
            }, 300);
        }
    };

    // Mensaje de finalización
    const showCompletionMessage = () => {
        const container = document.querySelector('.exam-container');
        const completionScreen = document.createElement('div');
        completionScreen.className = 'completion-screen';
        completionScreen.innerHTML = `
            <div class="completion-content">
                <div class="completion-icon">🎓</div>
                <h2>¡Estudio Completado!</h2>
                <p>Has revisado todas las <strong>${total}</strong> preguntas del modo estudio.</p>
                <div class="completion-stats">
                    <div class="stat">
                        <span class="stat-value">${total}</span>
                        <span class="stat-label">Preguntas Estudiadas</span>
                    </div>
                </div>
                <div class="completion-actions">
                    <button onclick="restartStudy()" class="action-btn primary">
                        🔄 Estudiar Nuevamente
                    </button>
                    <a href="{% url 'examen' %}" class="action-btn secondary">
                        🏠 Volver al Menú
                    </a>
                </div>
            </div>
        `;
        
        completionScreen.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            animation: fadeIn 0.5s ease;
        `;
        
        document.body.appendChild(completionScreen);
    };

    // Función global para reiniciar estudio
    window.restartStudy = () => {
        const completionScreen = document.querySelector('.completion-screen');
        if (completionScreen) {
            completionScreen.remove();
        }
        show(0);
    };

    // Navegación por teclado mejorada
    document.addEventListener('keydown', (e) => {
        // Solo si no estamos escribiendo en un input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        switch(e.key) {
            case 'ArrowRight':
            case ' ': // Spacebar
                if (current < total - 1) {
                    e.preventDefault();
                    nextBtn.click();
                } else if (current === total - 1) {
                    e.preventDefault();
                    finishBtn.click();
                }
                break;
            case 'ArrowLeft':
                if (current > 0) {
                    e.preventDefault();
                    prevBtn.click();
                }
                break;
            case 'Home':
                e.preventDefault();
                show(0);
                break;
            case 'End':
                e.preventDefault();
                show(total - 1);
                break;
            case 'Escape':
                // Volver al menú principal
                window.location.href = '{% url "examen" %}';
                break;
        }
    });

    // Añadir indicadores de navegación por teclado
    const addKeyboardHints = () => {
        const nav = document.querySelector('.wizard-nav');
        if (nav) {
            const hints = document.createElement('div');
            hints.className = 'keyboard-hints';
            hints.innerHTML = `
                <small style="color: #666; margin-top: 10px; text-align: center; display: block;">
                    💡 Usa las teclas ←→ o Espacio para navegar | Inicio/Fin para saltar | Esc para salir
                </small>
            `;
            nav.appendChild(hints);
        }
    };

    // Efectos visuales adicionales para opciones
    const addOptionEffects = () => {
        questions.forEach(question => {
            const correctOptions = question.querySelectorAll('.option-correct');
            const incorrectOptions = question.querySelectorAll('.option-incorrect');
            
            correctOptions.forEach((option, index) => {
                option.addEventListener('mouseenter', () => {
                    option.style.transform = 'translateY(-3px) scale(1.02)';
                });
                
                option.addEventListener('mouseleave', () => {
                    option.style.transform = 'translateY(0) scale(1)';
                });
            });
            
            incorrectOptions.forEach((option, index) => {
                option.addEventListener('mouseenter', () => {
                    option.style.transform = 'translateY(-3px) scale(1.02)';
                });
                
                option.addEventListener('mouseleave', () => {
                    option.style.transform = 'translateY(0) scale(1)';
                });
            });
        });
    };

    // Auto-avance opcional (comentado por defecto)
    const enableAutoAdvance = (seconds = 15) => {
        let autoTimer;
        
        const startAutoTimer = () => {
            clearTimeout(autoTimer);
            autoTimer = setTimeout(() => {
                if (current < total - 1) {
                    nextBtn.click();
                }
            }, seconds * 1000);
        };
        
        const stopAutoTimer = () => {
            clearTimeout(autoTimer);
        };
        
        // Reiniciar timer al cambiar pregunta
        const originalShow = show;
        show = (idx) => {
            originalShow(idx);
            startAutoTimer();
        };
        
        // Pausar auto-avance cuando el usuario interactúa
        document.addEventListener('mousemove', stopAutoTimer);
        document.addEventListener('keydown', stopAutoTimer);
        
        // Iniciar timer
        startAutoTimer();
    };

    // Estadísticas de estudio (opcional)
    const trackStudyStats = () => {
        const startTime = Date.now();
        let questionTimes = [];
        let currentQuestionStart = startTime;
        
        const originalShow = show;
        show = (idx) => {
            // Registrar tiempo en pregunta anterior
            if (current >= 0) {
                questionTimes[current] = Date.now() - currentQuestionStart;
            }
            currentQuestionStart = Date.now();
            originalShow(idx);
        };
        
        // Al finalizar, mostrar estadísticas
        window.showStudyStats = () => {
            const totalTime = Date.now() - startTime;
            const avgTime = questionTimes.reduce((a, b) => a + b, 0) / questionTimes.length;
            
            console.log('Estadísticas de Estudio:', {
                totalTime: Math.round(totalTime / 1000) + 's',
                avgTimePerQuestion: Math.round(avgTime / 1000) + 's',
                questionTimes: questionTimes.map(t => Math.round(t / 1000) + 's')
            });
        };
    };

    // Inicialización mejorada
    const initialize = () => {
        addKeyboardHints();
        addOptionEffects();
        // trackStudyStats(); // Descomentar para activar estadísticas
        // enableAutoAdvance(20); // Descomentar para auto-avance cada 20 segundos
        
        show(0);
        
        console.log(`Modo Estudio inicializado: ${total} preguntas cargadas`);
        console.log('Controles: ←→ para navegar, Espacio para avanzar, Esc para salir');
    };

    // Inicializar todo
    initialize();

    // CSS adicional para efectos
    const additionalStyles = document.createElement('style');
    additionalStyles.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .slide-out-left {
            animation: slideOutLeft 0.3s ease-out;
        }
        
        .slide-out-right {
            animation: slideOutRight 0.3s ease-out;
        }
        
        @keyframes slideOutLeft {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(-50px); opacity: 0; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(50px); opacity: 0; }
        }
        
        .completion-content {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 500px;
            width: 90%;
            animation: bounceIn 0.6s ease;
        }
        
        @keyframes bounceIn {
            0% { transform: scale(0.3); opacity: 0; }
            50% { transform: scale(1.1); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        .completion-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .completion-content h2 {
            color: #4CAF50;
            margin-bottom: 15px;
            font-size: 2rem;
        }
        
        .completion-content p {
            color: #666;
            margin-bottom: 25px;
            font-size: 1.1rem;
        }
        
        .completion-stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 25px 0;
        }
        
        .completion-stats .stat {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .completion-stats .stat-value {
            display: block;
            font-size: 1.5rem;
            font-weight: bold;
            color: #4CAF50;
        }
        
        .completion-stats .stat-label {
            font-size: 0.9rem;
            color: #666;
        }
        
        .completion-actions {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
        }
        
        .action-btn.primary {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
        }
        
        .action-btn.secondary {
            background: linear-gradient(135deg, #6c757d, #5a6268);
            color: white;
        }
        
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
    `;
    document.head.appendChild(additionalStyles);
});