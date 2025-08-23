// practice_exam.js
document.addEventListener('DOMContentLoaded', () => {
    const questions = Array.from(document.querySelectorAll('.question'));
    if (!questions.length) return;
  
    // Reusar loaders si quieres (de tu selection_exam.js). Aquí hago lo básico:
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const posCard = document.getElementById('posCard');
    const liveScore = document.getElementById('liveScore');
    const progressEl = document.getElementById('pageProgress');
    const csrfToken = document.getElementById('csrfToken')?.value;
  
    let current = 0;
    const total = questions.length;
  
    // Estadísticas
    let attempted = 0;
    let correctCount = 0;
  
    // Estado por pregunta para evitar doble verificación
    const locked = new Set(); // ids bloqueados (qid)
    const debouncers = new Map(); // index -> timeout id
  
    const updateHeader = () => {
      posCard.innerHTML = `<div class="stat-number">${current + 1}</div><div class="stat-label">Pregunta Actual</div>`;
      liveScore.innerHTML = `<div class="stat-number">${correctCount} / ${attempted}</div><div class="stat-label">Aciertos / Intentadas</div>`;
      progressEl.style.width = `${Math.round(((current + 1)/ total) * 100)}%`;
      prevBtn.disabled = current === 0;
    };
  
    const show = (idx) => {
      questions.forEach((q, i) => {
        q.classList.toggle('hidden', i !== idx);
        q.classList.toggle('active', i === idx);
      });
      current = idx;
      updateHeader();
    };
  
    const markLocked = (fieldset) => {
      fieldset.classList.add('locked');
      fieldset.querySelectorAll('input').forEach(i => { i.disabled = true; });
      const qid = fieldset.dataset.qid;
      if (qid) locked.add(qid);
    };
  
    const clearVisual = (fieldset) => {
      fieldset.querySelectorAll('.option').forEach(o => {
        o.classList.remove('correct', 'wrong', 'selected');
        o.style.transform = '';
      });
      fieldset.querySelector('.result-badge').textContent = '';
    };
  
    const paintSelection = (fieldset) => {
      // pinta .selected al elegir
      const inputs = Array.from(fieldset.querySelectorAll('input'));
      inputs.forEach(inp => {
        const opt = inp.closest('.option');
        if (!opt) return;
        if (inp.type === 'radio') {
          opt.classList.toggle('selected', inp.checked);
        } else {
          opt.classList.toggle('selected', inp.checked);
        }
      });
    };
  
    const feedback = (fieldset, result, userLetters) => {
      // result: {correct, correct_letters:[...], explain}
      const inputs = Array.from(fieldset.querySelectorAll('input'));
      const byLetter = new Map();
      inputs.forEach(inp => byLetter.set(inp.value, inp));
  
      // Pinta correctas en verde
      result.correct_letters.forEach(letter => {
        const inp = byLetter.get(letter);
        if (inp) {
          const opt = inp.closest('.option');
          if (opt) opt.classList.add('correct');
        }
      });
  
      // Si falló, pinta errores del usuario en rojo
      if (!result.correct) {
        (userLetters || []).forEach(letter => {
          if (!result.correct_letters.includes(letter)) {
            const inp = byLetter.get(letter);
            if (inp) {
              const opt = inp.closest('.option');
              if (opt) opt.classList.add('wrong');
            }
          }
        });
      }
  
      const badge = fieldset.querySelector('.result-badge');
      badge.innerHTML = result.correct
        ? `<span class="result-ok">✅ Correcto</span>`
        : `<span class="result-bad">❌ Incorrecto. Respuesta: ${result.correct_letters.join(', ')}</span>`;
  
      // estadísticas
      attempted += 1;
      if (result.correct) correctCount += 1;
      updateHeader();
  
      // bloquear para evitar “adivinar”
      markLocked(fieldset);
    };
  
    const postCheck = async (payload) => {
      const body = new URLSearchParams();
      Object.entries(payload).forEach(([k, v]) => {
        if (Array.isArray(v)) {
          v.forEach(item => body.append(k, item));
        } else {
          body.append(k, v);
        }
      });
  
      const res = await fetch('/api/check-answer/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    };
  
    const debounceCheck = (idx, fn) => {
      if (debouncers.has(idx)) {
        clearTimeout(debouncers.get(idx));
      }
      const id = setTimeout(fn, 250); // 250 ms
      debouncers.set(idx, id);
    };
  
    // SINGLE: verificar al marcar
    const handleSingle = (fieldset) => {
      const qid = fieldset.dataset.qid;
      if (locked.has(qid)) return;
  
      const selected = fieldset.querySelector('input[type="radio"]:checked');
      if (!selected) return;
  
      const userLetter = selected.value;
  
      debounceCheck(fieldset.dataset.index || 0, async () => {
        try {
          const result = await postCheck({
            question_id: qid,
            question_type: 'SINGLE',
            answer: userLetter
          });
          feedback(fieldset, result, [userLetter]);
  
          // Auto-avanzar suave en 1100 ms (opcional)
          setTimeout(() => {
            if (current < questions.length - 1) show(current + 1);
          }, 1100);
  
        } catch (e) {
          const badge = fieldset.querySelector('.result-badge');
          badge.innerHTML = `<span class="result-bad">⚠️ No se pudo verificar. Intenta de nuevo.</span>`;
        }
      });
    };
  
    // MULTI: requiere “Confirmar selección”
    const handleMultiConfirm = (fieldset) => {
      const qid = fieldset.dataset.qid;
      if (locked.has(qid)) return;
  
      const checked = Array.from(fieldset.querySelectorAll('input[type="checkbox"]:checked'))
                           .map(i => i.value);
      if (!checked.length) {
        // micro feedback
        fieldset.classList.add('shake');
        setTimeout(() => fieldset.classList.remove('shake'), 400);
        return;
      }
  
      debounceCheck(fieldset.dataset.index || 0, async () => {
        try {
          const result = await postCheck({
            question_id: qid,
            question_type: 'MULTI',
            answer: checked // lista
          });
          feedback(fieldset, result, checked);
        } catch (e) {
          const badge = fieldset.querySelector('.result-badge');
          badge.innerHTML = `<span class="result-bad">⚠️ No se pudo verificar. Intenta de nuevo.</span>`;
        }
      });
    };
  
    // Listeners por pregunta
    questions.forEach((fieldset, idx) => {
      fieldset.dataset.index = idx;
  
      // efecto “selected”
      fieldset.addEventListener('change', (e) => {
        if (e.target.matches('input[type="radio"], input[type="checkbox"]')) {
          paintSelection(fieldset);
          if (fieldset.dataset.qtype === 'SINGLE') {
            handleSingle(fieldset);
          }
        }
      });
  
      // Confirmar en MULTI
      const confirmBtn = fieldset.querySelector('.confirm-multi');
      if (confirmBtn) {
        confirmBtn.addEventListener('click', () => handleMultiConfirm(fieldset));
      }
    });
  
    // Navegación
    prevBtn.addEventListener('click', () => {
      if (current > 0) show(current - 1);
    });
    nextBtn.addEventListener('click', () => {
      if (current < total - 1) show(current + 1);
    });
  
    // Inicio
    updateHeader();
    show(0);
  });
  