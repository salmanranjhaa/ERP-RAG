const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const audioBtn = document.getElementById('audio-btn');
const recordingIndicator = document.getElementById('recording-indicator');
const stepsContainer = document.getElementById('steps-container');

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
    chatHistory.scrollTo(0, chatHistory.scrollHeight);
}

function updateLog(status, detail) {
    if (stepsContainer.innerHTML.includes('Waiting for query')) {
        stepsContainer.innerHTML = '';
    }
    
    const logDiv = document.createElement('div');
    logDiv.className = 'log-item processing';
    logDiv.innerHTML = `
        <div class="log-title"><i data-lucide="loader"></i> ${status}</div>
        <div class="log-detail">${detail}</div>
    `;
    
    stepsContainer.appendChild(logDiv);
    lucide.createIcons();
    stepsContainer.scrollTo(0, stepsContainer.scrollHeight);
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
    
    updateLog("Initializing Query", "Routing through MoE Engine...");
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Unknown Server Error");
        }
        
        updateLog("Agent Source Result", data.source ? data.source.toString() : "No source");
        addMessage(data.response);
    } catch (err) {
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
        alert("Microphone access is required for Voice Chat.");
    }
}
setupAudio();

// Hold to Record Logic
audioBtn.addEventListener('mousedown', () => {
    if (!mediaRecorder) return;
    isRecording = true;
    audioBtn.classList.add('recording');
    recordingIndicator.style.display = 'flex';
    clearLogs();
    updateLog("Recording", "Microphone Active...");
    mediaRecorder.start();
});

audioBtn.addEventListener('mouseup', () => {
    if (!isRecording) return;
    isRecording = false;
    audioBtn.classList.remove('recording');
    recordingIndicator.style.display = 'none';
    updateLog("Processing Audio", "Sending to Whisper v3...");
    mediaRecorder.stop();
});

audioBtn.addEventListener('mouseleave', () => { // Catch drag-offs
    if (isRecording) {
        audioBtn.dispatchEvent(new Event('mouseup'));
    }
});

// Send Audio blob to FastAPI
async function sendAudio(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    try {
        const response = await fetch('/chat/audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Unknown Server Error");
        }

        addMessage(`[Transcribed via Whisper]: ${data.query}`, true);
        
        updateLog("Agent Source Result", data.source ? data.source.toString() : "No source");
        addMessage(data.response);
    } catch (err) {
        addMessage(`Error: ${err.message}`);
        updateLog("Error", err.message);
    }
}
