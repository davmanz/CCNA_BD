// practice_exam.js
document.addEventListener('DOMContentLoaded', () => {
  const questions = Array.from(document.querySelectorAll('.question'));
  if (!questions.length) return;

  const prevBtn     = document.getElementById('prevBtn');
  const nextBtn     = document.getElementById('nextBtn');
  const posCard     = document.getElementById('posCard');
  const liveScore   = document.getElementById('liveScore');
  const progressEl  = document.getElementById('pageProgress');
  const csrfToken   = document.getElementById('csrfToken')?.value;

  let current = 0;
  const total = questions.length;

  // Estado por pregunta: qid -> { attempted, correct, pending, lastReqId, abortCtl }
  const qState = new Map();

  const getQid = (fieldset) => fieldset?.dataset?.qid;

  const ensureState = (qid) => {
    if (!qState.has(qid)) {
      qState.set(qid, { attempted:false, correct:false, pending:false, lastReqId:0, abortCtl:null });
    }
    return qState.get(qid);
  };

  // --- UI helpers ---
  const recomputeScore = () => {
    let attempted = 0, correct = 0;
    for (const s of qState.values()) {
      if (s.attempted) attempted++;
      if (s.correct)   correct++;
    }
    liveScore.innerHTML = `
      <div class="stat-number">${correct} / ${attempted}</div>
      <div class="stat-label">Aciertos / Intentadas</div>`;
  };

  const updateHeader = () => {
    posCard.innerHTML = `<div class="stat-number">${current + 1}</div><div class="stat-label">Pregunta Actual</div>`;
    progressEl.style.width = `${Math.round(((current + 1) / total) * 100)}%`;
    prevBtn.disabled = current === 0;

    const fs = questions[current];
    const qid = getQid(fs);
    const st  = ensureState(qid);
    // “Siguiente” habilitado solo si la actual fue validada y no está pendiente
    nextBtn.disabled = !(st.attempted && !st.pending);
  };

  const show = (idx) => {
    questions.forEach((q, i) => {
      q.classList.toggle('hidden', i !== idx);
      q.classList.toggle('active', i === idx);
    });
    current = idx;
    updateHeader();
  };

  const setPending = (fieldset, isPending, message = null) => {
    const qid = getQid(fieldset);
    const st  = ensureState(qid);
    st.pending = isPending;

    // Deshabilitar/rehabilitar inputs
    fieldset.querySelectorAll('input').forEach(i => { i.disabled = isPending; });

    // Deshabilitar “Confirmar” si existe (MULTI)
    const confirmBtn = fieldset.querySelector('.confirm-multi');
    if (confirmBtn) confirmBtn.disabled = isPending;

    // Mensaje
    const badge = fieldset.querySelector('.result-badge');
    if (isPending) {
      badge.innerHTML = message ?? `<span class="result-pending">⏳ Verificando…</span>`;
    } else if (!message) {
      // no limpiar feedback existente
    }

    updateHeader();
  };

  const paintSelection = (fieldset) => {
    const inputs = Array.from(fieldset.querySelectorAll('input'));
    inputs.forEach(inp => {
      const opt = inp.closest('.option');
      if (!opt) return;
      opt.classList.toggle('selected', inp.checked);
    });
  };

  const lockQuestion = (fieldset) => {
    fieldset.classList.add('locked');
    fieldset.querySelectorAll('input').forEach(i => { i.disabled = true; });
    const confirmBtn = fieldset.querySelector('.confirm-multi');
    if (confirmBtn) confirmBtn.disabled = true;
  };

  const paintFeedback = (fieldset, result, userLetters) => {
    // result: { correct:boolean, correct_letters:[...], explain? }
    const inputs = Array.from(fieldset.querySelectorAll('input'));
    const byLetter = new Map();
    inputs.forEach(inp => byLetter.set(inp.value, inp));

    result.correct_letters.forEach(letter => {
      const inp = byLetter.get(letter);
      if (inp) inp.closest('.option')?.classList.add('correct');
    });

    const chosen = Array.isArray(userLetters) ? userLetters : [userLetters].filter(Boolean);
    if (!result.correct) {
      chosen.forEach(letter => {
        if (!result.correct_letters.includes(letter)) {
          const inp = byLetter.get(letter);
          if (inp) inp.closest('.option')?.classList.add('wrong');
        }
      });
    }

    const badge = fieldset.querySelector('.result-badge');
    badge.innerHTML = result.correct
      ? `<span class="result-ok">✅ Correcto</span>`
      : `<span class="result-bad">❌ Incorrecto. Respuesta: ${result.correct_letters.join(', ')}</span>`;
  };

  // --- Red segura con cancelación + timeout + requestId ---
  const withTimeout = (p, ms = 8000) =>
    Promise.race([ p, new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms)) ]);

  const safeCheck = async (fieldset, payload) => {
    const qid = getQid(fieldset);
    const st  = ensureState(qid);

    // Cancelar solicitud previa
    if (st.abortCtl) st.abortCtl.abort();
    st.abortCtl = new AbortController();
    st.lastReqId += 1;
    const myReq = st.lastReqId;

    // Body form-urlencoded
    const body = new URLSearchParams();
    Object.entries(payload).forEach(([k, v]) => {
      if (Array.isArray(v)) v.forEach(item => body.append(k, item));
      else body.append(k, v);
    });

    setPending(fieldset, true);

    try {
      const res = await withTimeout(fetch('/api/check-answer/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
        signal: st.abortCtl.signal
      }));

      // Ignorar respuestas viejas
      if (myReq !== st.lastReqId) return { stale:true };

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();

      if (!st.attempted) st.attempted = true;
      st.correct = !!json.correct;

      setPending(fieldset, false);
      // Aseguramos pasar letras como array para SINGLE/MULTI
      const uLetters = Array.isArray(payload.answer) ? payload.answer : [payload.answer];
      paintFeedback(fieldset, json, uLetters);
      lockQuestion(fieldset);

      recomputeScore();
      updateHeader();

      return { ok:true, data:json };

    } catch (err) {
      if (err.name === 'AbortError') return { aborted:true };

      // Si NO es la solicitud vigente, ignorar el error (evita pisar feedback con "Reintentar")
      if (myReq !== st.lastReqId) return { stale:true };

      // Timeout o fallo real de la solicitud vigente -> mostrar Reintentar
      const badge = fieldset.querySelector('.result-badge');
      const isTimeout = String(err.message || '').toLowerCase().includes('timeout');
      const msg = isTimeout ? 'Se agotó el tiempo de espera.' : 'No se pudo verificar.';

      badge.innerHTML = `
        <span class="result-bad">⚠️ ${msg}</span>
        <button type="button" class="retry-btn">Reintentar</button>
      `;

      setPending(fieldset, false, badge.innerHTML);

      const retry = fieldset.querySelector('.retry-btn');
      if (retry) {
        retry.addEventListener('click', () => {
          safeCheck(fieldset, payload);
        }, { once:true });
      }

      return { error: err };

    } finally {
      if (myReq === st.lastReqId) st.abortCtl = null;
      updateHeader();
    }
  };

  // --- Handlers ---
  const handleSingle = (fieldset) => {
    const qid = getQid(fieldset);
    const st  = ensureState(qid);
    if (st.attempted || st.pending) return;

    const selected = fieldset.querySelector('input[type="radio"]:checked');
    if (!selected) return;

    safeCheck(fieldset, {
      question_id   : qid,
      question_type : 'SINGLE',
      answer        : selected.value
    });
  };

  const handleMultiConfirm = (fieldset) => {
    const qid = getQid(fieldset);
    const st  = ensureState(qid);
    if (st.attempted || st.pending) return;

    const checked = Array.from(fieldset.querySelectorAll('input[type="checkbox"]:checked')).map(i => i.value);
    if (!checked.length) {
      fieldset.classList.add('shake');
      setTimeout(() => fieldset.classList.remove('shake'), 400);
      return;
    }

    // Usar la safeCheck GLOBAL
    safeCheck(fieldset, {
      question_id   : qid,
      question_type : 'MULTI',
      answer        : checked
    });
  };

  // --- Listeners por pregunta ---
  questions.forEach((fieldset, idx) => {
    fieldset.dataset.index = idx;

    fieldset.addEventListener('change', (e) => {
      if (e.target.matches('input[type="radio"], input[type="checkbox"]')) {
        paintSelection(fieldset);
        if (fieldset.dataset.qtype === 'SINGLE') {
          handleSingle(fieldset);
        }
      }
    });

    const confirmBtn = fieldset.querySelector('.confirm-multi');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => handleMultiConfirm(fieldset));
    }
  });

  // --- Navegación ---
  prevBtn.addEventListener('click', () => { if (current > 0) show(current - 1); });
  nextBtn.addEventListener('click', () => { if (current < total - 1) show(current + 1); });

  // --- Inicio ---
  recomputeScore();
  show(0);
});
