// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  history: [],
  isLoading: false,
  isRecording: false,
  mediaRecorder: null,
  audioChunks: []
};

// ── DOM ───────────────────────────────────────────────────────────────────────
const messagesEl  = document.getElementById('messages');
const inputEl     = document.getElementById('query-input');
const sendBtn     = document.getElementById('send-btn');
const micBtn      = document.getElementById('mic-btn');
const stepsEl     = document.getElementById('reasoning-steps');
const statusDot   = document.getElementById('status-dot');
const statusText  = document.getElementById('status-text');
const barFill     = document.getElementById('page-bar-fill');

// ── Progress Bar ─────────────────────────────────────────────────────────────
const progress = {
  _iv: null,
  start() {
    clearInterval(this._iv);
    barFill.style.opacity = '1';
    barFill.style.transition = 'none';
    barFill.style.width = '0%';
    let w = 0;
    this._iv = setInterval(() => {
      w += (87 - w) * 0.09 + 0.4;
      if (w >= 86) { clearInterval(this._iv); w = 86; }
      barFill.style.transition = 'width 0.2s ease';
      barFill.style.width = w + '%';
    }, 180);
  },
  done() {
    clearInterval(this._iv);
    barFill.style.transition = 'width 0.15s ease';
    barFill.style.width = '100%';
    setTimeout(() => {
      barFill.style.transition = 'opacity 0.35s ease';
      barFill.style.opacity = '0';
      setTimeout(() => { barFill.style.width = '0%'; }, 400);
    }, 180);
  }
};

// ── Starfield ─────────────────────────────────────────────────────────────────
function initStarfield() {
  const canvas = document.getElementById('starfield');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const makeStars = () => Array.from({ length: 220 }, () => {
    const roll = Math.random();
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: roll > 0.97 ? Math.random() * 1.5 + 1 : Math.random() * 0.9 + 0.2,
      speed: Math.random() * 0.012 + 0.003,
      angle: Math.random() * Math.PI * 2,
      twinkle: Math.random() * Math.PI * 2,
      twinkleSpeed: Math.random() * 0.018 + 0.004,
      color: roll > 0.97 ? '#C9A84B' : roll > 0.94 ? '#EF4444' : '#ffffff',
      baseOpacity: Math.random() * 0.5 + 0.3
    };
  });

  let stars = makeStars();

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(s => {
      s.twinkle += s.twinkleSpeed;
      const opacity = s.baseOpacity * (0.4 + 0.6 * Math.abs(Math.sin(s.twinkle)));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      if (s.color === '#ffffff') {
        ctx.fillStyle = `rgba(255,255,255,${opacity})`;
      } else if (s.color === '#C9A84B') {
        ctx.fillStyle = `rgba(201,168,75,${opacity})`;
      } else {
        ctx.fillStyle = `rgba(239,68,68,${opacity * 0.8})`;
      }
      ctx.fill();

      // Tiny cross glow for bright stars
      if (s.r > 1.2) {
        ctx.strokeStyle = s.color === '#C9A84B'
          ? `rgba(201,168,75,${opacity * 0.3})`
          : `rgba(255,255,255,${opacity * 0.2})`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(s.x - s.r * 3, s.y);
        ctx.lineTo(s.x + s.r * 3, s.y);
        ctx.moveTo(s.x, s.y - s.r * 3);
        ctx.lineTo(s.x, s.y + s.r * 3);
        ctx.stroke();
      }

      // Slow drift
      s.x += Math.cos(s.angle) * s.speed;
      s.y += Math.sin(s.angle) * s.speed;
      if (s.x < -5) s.x = canvas.width + 5;
      if (s.x > canvas.width + 5) s.x = -5;
      if (s.y < -5) s.y = canvas.height + 5;
      if (s.y > canvas.height + 5) s.y = -5;
    });
    requestAnimationFrame(draw);
  }
  draw();
}
initStarfield();

// ── Force Quotes ──────────────────────────────────────────────────────────────
const quotes = [
  '"Your lack of data is disturbing."',
  '"Search your query. You know it to be true."',
  '"Do or query not. There is no try."',
  '"The Force will be with your ETL job. Always."',
  '"I find your lack of schema... disturbing."',
  '"These are not the records you are looking for."',
  '"May the queries be with you."',
];
let qIdx = 0;
const quoteEl = document.getElementById('force-quote');
setInterval(() => {
  if (!quoteEl) return;
  qIdx = (qIdx + 1) % quotes.length;
  quoteEl.style.opacity = '0';
  setTimeout(() => { quoteEl.textContent = quotes[qIdx]; quoteEl.style.opacity = ''; }, 600);
}, 7000);

// ── Health Check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    if (data.ready) {
      statusDot.classList.add('online');
      statusText.textContent = 'Fleet online · Groq LPU';
    } else {
      statusText.textContent = 'Agent initializing...';
      setTimeout(checkHealth, 3000);
    }
  } catch {
    statusText.textContent = 'Fleet offline';
    setTimeout(checkHealth, 5000);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function setQuery(btn) {
  inputEl.value = btn.textContent.trim();
  autoResize();
  inputEl.focus();
}

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
}

function scrollToBottom(el) { el.scrollTop = el.scrollHeight; }

function formatTime() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>');
}

// ── Message Rendering ─────────────────────────────────────────────────────────
function appendMessage(role, content) {
  const welcome = messagesEl.querySelector('.welcome-msg');
  if (welcome) welcome.remove();

  const msg = document.createElement('div');
  msg.className = `msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'agent' ? '◈' : 'CMD';

  const contentEl = document.createElement('div');
  contentEl.className = 'msg-content';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = escapeHtml(content);

  const meta = document.createElement('div');
  meta.className = 'msg-meta';
  meta.textContent = formatTime();

  contentEl.appendChild(bubble);
  contentEl.appendChild(meta);
  msg.appendChild(avatar);
  msg.appendChild(contentEl);
  messagesEl.appendChild(msg);
  scrollToBottom(messagesEl);
}

function showTyping() {
  const msg = document.createElement('div');
  msg.className = 'msg agent';
  msg.id = 'typing-msg';
  msg.innerHTML = `
    <div class="msg-avatar">◈</div>
    <div class="msg-content">
      <div class="msg-bubble" style="padding:10px 16px">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>`;
  messagesEl.appendChild(msg);
  scrollToBottom(messagesEl);
}

function removeTyping() {
  const t = document.getElementById('typing-msg');
  if (t) t.remove();
}

// ── Reasoning Panel ───────────────────────────────────────────────────────────
function clearReasoning() {
  stepsEl.innerHTML = `<div class="step-thinking"><div class="spinner"></div> Initiating ReACT loop...<div class="load-bar" style="margin-left:auto;width:60px"><div class="load-bar-fill"></div></div></div>`;
}

function addReasoningStep(stepNum, content, isDone) {
  const thinking = stepsEl.querySelector('.step-thinking');
  if (thinking) thinking.remove();

  const card = document.createElement('div');
  card.className = `step-card ${isDone ? 'done' : 'active'}`;
  card.id = `step-${stepNum}`;

  let label = `STEP ${stepNum}`;
  if (/thought:/i.test(content))          label = `STEP ${stepNum} · THOUGHT`;
  else if (/action\s*input:/i.test(content)) label = `STEP ${stepNum} · TOOL INPUT`;
  else if (/action:/i.test(content))      label = `STEP ${stepNum} · ACTION`;
  else if (/observation:/i.test(content)) label = `STEP ${stepNum} · OBSERVATION`;
  else if (isDone)                        label = `STEP ${stepNum} · ANSWER`;

  card.innerHTML = `
    <div class="step-header">
      <span class="step-num">REACT</span>
      <span class="step-label">${label}</span>
    </div>
    <div class="step-body">${escapeHtml(content.substring(0, 700))}${content.length > 700 ? '...' : ''}</div>`;

  stepsEl.appendChild(card);
  scrollToBottom(stepsEl);

  const prev = document.getElementById(`step-${stepNum - 1}`);
  if (prev) prev.classList.remove('active');

  if (!isDone) {
    const thinking = document.createElement('div');
    thinking.className = 'step-thinking';
    thinking.innerHTML = `<div class="spinner"></div> Reasoning...<div class="load-bar" style="margin-left:auto;width:60px"><div class="load-bar-fill"></div></div>`;
    stepsEl.appendChild(thinking);
    scrollToBottom(stepsEl);
  }
}

function addReasoningSummary(totalSteps) {
  const thinking = stepsEl.querySelector('.step-thinking');
  if (thinking) thinking.remove();
  const s = document.createElement('div');
  s.className = 'summary-card';
  s.innerHTML = `<div class="summary-label">SYNTHESIS COMPLETE</div><p>Resolved in ${totalSteps} step${totalSteps !== 1 ? 's' : ''}. The Force is with this query.</p>`;
  stepsEl.appendChild(s);
  scrollToBottom(stepsEl);
}

function showIdleReasoning(msg = 'Awaiting next transmission...') {
  stepsEl.innerHTML = `
    <div class="reasoning-idle">
      <div class="idle-icon">◈</div>
      <p>${msg}</p>
      <p class="idle-sub">The full ReACT loop — every Thought, Action, and Observation — appears here in real time.</p>
    </div>`;
}

// ── Chat ──────────────────────────────────────────────────────────────────────
async function sendMessage(customQuery) {
  const query = customQuery || inputEl.value.trim();
  if (!query || state.isLoading) return;

  if (!customQuery) { inputEl.value = ''; inputEl.style.height = 'auto'; }

  state.isLoading = true;
  sendBtn.disabled = true;
  progress.start();

  appendMessage('user', query);
  showTyping();
  clearReasoning();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, history: state.history })
    });
    const data = await res.json();
    removeTyping();
    progress.done();

    if (data.detail) {
      appendMessage('agent', `Error: ${data.detail}`);
      showIdleReasoning('Error in the Force.');
    } else {
      appendMessage('agent', data.response || 'No response received.');

      if (data.reasoning_chain?.length > 0) {
        stepsEl.innerHTML = '';
        data.reasoning_chain.forEach(step => addReasoningStep(step.step, step.content, step.is_done));
        addReasoningSummary(data.total_steps || data.reasoning_chain.length);
      } else {
        showIdleReasoning('Synthesis complete.');
      }

      state.history.push(
        { role: 'user', content: query },
        { role: 'assistant', content: data.response || '' }
      );
      if (state.history.length > 20) state.history = state.history.slice(-20);
    }
  } catch (err) {
    removeTyping();
    progress.done();
    appendMessage('agent', 'Transmission lost. Please try again.');
    showIdleReasoning('Connection lost.');
  } finally {
    state.isLoading = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

// ── Audio ─────────────────────────────────────────────────────────────────────
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.audioChunks = [];
    state.mediaRecorder = new MediaRecorder(stream);
    state.mediaRecorder.ondataavailable = e => { if (e.data.size > 0) state.audioChunks.push(e.data); };
    state.mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      await sendAudio(new Blob(state.audioChunks, { type: 'audio/webm' }));
    };
    state.mediaRecorder.start();
    state.isRecording = true;
    micBtn.classList.add('recording');
  } catch { alert('Microphone access denied.'); }
}

function stopRecording() {
  if (state.mediaRecorder && state.isRecording) {
    state.mediaRecorder.stop();
    state.isRecording = false;
    micBtn.classList.remove('recording');
  }
}

async function sendAudio(blob) {
  state.isLoading = true;
  sendBtn.disabled = true;
  progress.start();
  showTyping();
  clearReasoning();

  const formData = new FormData();
  formData.append('audio', blob, 'recording.webm');
  formData.append('history', JSON.stringify(state.history));

  try {
    const res = await fetch('/chat/audio', { method: 'POST', body: formData });
    const data = await res.json();
    removeTyping();
    progress.done();

    if (data.query) appendMessage('user', `🎤 ${data.query}`);
    if (data.response) {
      appendMessage('agent', data.response);
      if (data.reasoning_chain?.length > 0) {
        stepsEl.innerHTML = '';
        data.reasoning_chain.forEach(step => addReasoningStep(step.step, step.content, step.is_done));
        addReasoningSummary(data.total_steps || data.reasoning_chain.length);
      }
      state.history.push(
        { role: 'user', content: data.query || '' },
        { role: 'assistant', content: data.response }
      );
    }
  } catch {
    removeTyping();
    progress.done();
    appendMessage('agent', 'Audio transmission failed.');
    showIdleReasoning('Error.');
  } finally {
    state.isLoading = false;
    sendBtn.disabled = false;
  }
}

// ── Events ────────────────────────────────────────────────────────────────────
sendBtn.addEventListener('click', () => sendMessage());
inputEl.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
inputEl.addEventListener('input', autoResize);
micBtn.addEventListener('mousedown', startRecording);
micBtn.addEventListener('mouseup', stopRecording);
micBtn.addEventListener('mouseleave', stopRecording);
micBtn.addEventListener('touchstart', e => { e.preventDefault(); startRecording(); });
micBtn.addEventListener('touchend', e => { e.preventDefault(); stopRecording(); });

// ── Init ──────────────────────────────────────────────────────────────────────
checkHealth();
