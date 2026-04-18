// hãy di chuyển tới branch MASTER
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const auditList = document.getElementById('audit-list');

// Metric Elements
const mTotal = document.getElementById('m-total');
const mRate = document.getElementById('m-rate');
const mHitl = document.getElementById('m-hitl');
const mLatency = document.getElementById('m-latency');

const bRateLimit = document.getElementById('b-rate-limit');
const bInputGuard = document.getElementById('b-input-guard');
const bOutputJudge = document.getElementById('b-output-judge');

// Modal Elements
const modal = document.getElementById('modal');
const modalJson = document.getElementById('modal-json');
const closeModal = document.querySelector('.close-modal');

const AGENT_API_KEY = "my-super-secret-key-123";
let userId = "user_" + Math.floor(Math.random() * 10000);

// Init
updateMetrics();
setInterval(updateMetrics, 5000); // Poll metrics every 5s

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;
    
    await sendMessage(message);
});

async function sendPrompt(text) {
    userInput.value = text;
    await sendMessage(text);
}

async function sendMessage(text) {
    appendMessage(text, 'user');
    userInput.value = '';
    
    const typingMsg = appendMessage('...', 'bot typing');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-API-Key': AGENT_API_KEY
            },
            body: JSON.stringify({ user_id: userId, message: text })
        });
        
        const data = await response.json();
        chatMessages.removeChild(typingMsg);
        
        const isBlocked = data.metadata.status === 'BLOCKED';
        const isFlagged = data.metadata.status === 'FLAGGED';
        
        const botMsg = appendMessage(data.response, 'bot', data.metadata);
        if (isBlocked) botMsg.classList.add('blocked');
        
        updateMetrics();
        updateAudit();
        
    } catch (err) {
        chatMessages.removeChild(typingMsg);
        appendMessage('Security connection error: ' + err.message, 'system');
    }
}

function appendMessage(text, type, meta = null) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.innerText = text;
    
    if (meta) {
        const metaDiv = document.createElement('span');
        metaDiv.className = 'meta';
        const layerInfo = meta.layer ? `Layer: ${meta.layer} | ` : '';
        metaDiv.innerText = `${layerInfo}Latency: ${parseFloat(meta.latency).toFixed(2)}s | Status: ${meta.status}`;
        div.appendChild(metaDiv);
        
        div.addEventListener('click', () => {
            showInspect(meta);
        });
    }
    
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
}

async function updateMetrics() {
    try {
        const res = await fetch('/api/metrics', {
            headers: { 'X-API-Key': AGENT_API_KEY }
        });
        const data = await res.json();
        
        mTotal.innerText = data.total_requests;
        mRate.innerText = data.block_rate;
        mHitl.innerText = data.hitl_required;
        mLatency.innerText = data.avg_latency;
        
        // Progress bars
        const total = data.total_requests || 1;
        bRateLimit.style.width = ((data.layer_blocks.RateLimit || 0) / total * 100) + '%';
        bInputGuard.style.width = ((data.layer_blocks.InputGuard || 0) / total * 100) + '%';
        bOutputJudge.style.width = ((data.layer_blocks.OutputJudge || 0) / total * 100) + '%';
        
    } catch (err) { console.warn('Metric error:', err); }
}

async function updateAudit() {
    try {
        const res = await fetch('/api/audit', {
            headers: { 'X-API-Key': AGENT_API_KEY }
        });
        const logs = await res.json();
        
        auditList.innerHTML = '';
        logs.reverse().forEach(log => {
            const item = document.createElement('div');
            item.className = 'audit-item glass';
            item.innerHTML = `
                <span>${log.input.substring(0, 20)}...</span>
                <span class="audit-tag tag-${log.status.toLowerCase()}">${log.status}</span>
            `;
            item.onclick = () => showInspect(log);
            auditList.appendChild(item);
        });
    } catch (err) { console.warn('Audit error:', err); }
}

function showInspect(data) {
    modalJson.innerText = JSON.stringify(data, null, 4);
    modal.style.display = 'block';
}

closeModal.onclick = () => modal.style.display = 'none';
window.onclick = (e) => { if (e.target == modal) modal.style.display = 'none'; }
