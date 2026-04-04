const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const audioBtn = document.getElementById('audio-btn');
const recordingIndicator = document.getElementById('recording-indicator');
const stepsContainer = document.getElementById('steps-container');
const sidebarNav = document.getElementById('sidebar-nav');
let conversationHistory = [];

// Progress bar (YouTube-style)
const barFill = document.getElementById('page-bar-fill');
const progress = {
  _iv: null,
  start() {
    clearInterval(this._iv);
    barFill.style.transition = 'none';
    barFill.style.width = '0%';
    barFill.style.opacity = '1';
    let w = 0;
    this._iv = setInterval(() => {
      w += (86 - w) * 0.09 + 0.4;
      if (w >= 85) { clearInterval(this._iv); w = 85; }
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

// Tab Switching Logic
sidebarNav.querySelectorAll('li').forEach(li => {
    li.addEventListener('click', () => {
        const viewId = li.getAttribute('data-view');
        if (!viewId) return;

        // Update Sidebar UI
        sidebarNav.querySelectorAll('li').forEach(item => item.classList.remove('active'));
        li.classList.add('active');

        // Update Main View
        document.querySelectorAll('main, .console-view').forEach(view => {
            view.style.display = 'none';
        });
        document.getElementById(`view-${viewId}`).style.display = 'flex';
    });
});

// Chat UI
function addMessage(text, isUser = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user-message' : 'system-message'}`;
    
    msgDiv.innerHTML = `
        <div class="avatar"><i data-lucide="${isUser ? 'user' : 'bot'}"></i></div>
        <div class="message-content glass-panel">
            <p>${text.replace(/\n/g, '<br>')}</p>
        </div>
    `;
    
    chatHistory.appendChild(msgDiv);
    lucide.createIcons();
    msgDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function updateLog(status, detail, isPayload = false) {
    if (stepsContainer.innerHTML.includes('Waiting for query')) {
        stepsContainer.innerHTML = '';
    }
    
    const logDiv = document.createElement('div');
    logDiv.className = 'log-item' + (isPayload ? '' : ' processing');
    
    let content = detail;
    if (typeof detail === 'object') {
        content = `<pre style="font-size: 0.75rem; color: #66fcf1; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 8px; margin-top: 8px; overflow-x: auto;">${JSON.stringify(detail, null, 2)}</pre>`;
    }

    logDiv.innerHTML = `
        <div class="log-title"><i data-lucide="${isPayload ? 'code' : 'loader'}"></i> ${status}</div>
        <div class="log-detail">${content}</div>
    `;
    
    stepsContainer.appendChild(logDiv);
    lucide.createIcons();
    logDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function clearLogs() {
    stepsContainer.innerHTML = `
        <div class="empty-state">
            <i data-lucide="activity"></i>
            <p>Waiting for query...</p>
        </div>
    `;
}

// Handle Text Submission
sendBtn.addEventListener('click', async () => {
    const text = userInput.value.trim();
    if (!text) return;
    
    userInput.value = '';
    addMessage(text, true);
    clearLogs();
    progress.start();
    
    updateLog("Initializing Query", "Routing through Multi-Source Synthesis Engine...");
    
    conversationHistory.push({ role: 'user', content: text });
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, history: conversationHistory })
        });
        
        const data = await response.json();
        progress.done();
        
        if (!response.ok) {
            throw new Error(data.detail || "Unknown Server Error");
        }
        
        if (data.detailed_logs) {
            data.detailed_logs.forEach(log => {
                updateLog(log.step, log.payload, true);
            });
        }

        updateLog("Synthesis Complete", `Source: ${data.source}`);
        addMessage(data.response);
        conversationHistory.push({ role: 'assistant', content: data.response });
    } catch (err) {
        progress.done();
        addMessage(`Error: ${err.message}`);
        updateLog("Error", err.message);
    }
});

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// Audio Recording Setup
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

async function setupAudio() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            audioChunks = [];
            sendAudio(audioBlob);
        };
    } catch (err) {
        console.error("Microphone access denied:", err);
        // Don't alert if it's just a permission issue during background setup
    }
}
setupAudio();

// Click to Record Logic
audioBtn.addEventListener('click', () => {
    if (!mediaRecorder) return;
    
    if (!isRecording) {
        // Start Recording
        isRecording = true;
        audioBtn.classList.add('recording');
        recordingIndicator.style.display = 'flex';
        clearLogs();
        updateLog("Recording", "Microphone Active...");
        mediaRecorder.start();
    } else {
        // Stop Recording
        isRecording = false;
        audioBtn.classList.remove('recording');
        recordingIndicator.style.display = 'none';
        updateLog("Processing Audio", "Sending to Whisper v3...");
        mediaRecorder.stop();
    }
});


// Send Audio blob to FastAPI
async function sendAudio(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    formData.append("history", JSON.stringify(conversationHistory));
    progress.start();

    try {
        const response = await fetch('/chat/audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        progress.done();
        
        if (!response.ok) {
            throw new Error(data.detail || "Unknown Server Error");
        }

        addMessage(`[Transcribed via Whisper]: ${data.query}`, true);
        conversationHistory.push({ role: 'user', content: data.query });
        
        if (data.detailed_logs) {
            data.detailed_logs.forEach(log => {
                updateLog(log.step, log.payload, true);
            });
        }

        updateLog("Synthesis Complete", `Source: ${data.source}`);
        addMessage(data.response);
        conversationHistory.push({ role: 'assistant', content: data.response });
    } catch (err) {
        progress.done();
        addMessage(`Error: ${err.message}`);
        updateLog("Error", err.message);
    }
}
