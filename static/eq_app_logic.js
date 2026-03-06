// --- Global State ---
let currentFileContent = "";
let currentFileName = "";
let typingInterval = null; // Timer for text typing effect
let isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

// --- Elements ---
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const fileIndicator = document.getElementById('fileIndicator');
const fileNameSpan = document.getElementById('fileName');
const welcomeScreen = document.getElementById('welcomeScreen');
const langSelect = document.getElementById('langSelect');
const voiceSettingsPanel = document.getElementById('voiceSettingsPanel');

let currentLang = localStorage.getItem('eq_lang') || 'en';

function updateUIText() {
    const t = MESSAGES_I18N[currentLang] || MESSAGES_I18N.en;

    // Static Elements
    const welcomeTitle = document.querySelector('.welcome-title');
    if (welcomeTitle) {
        // Use the global EQ_USER variable passed from Jinja
        welcomeTitle.innerText = t.welcome.replace('{{username}}', window.EQ_USER.username);
    }

    const welcomeSubtitle = document.querySelector('.welcome-subtitle');
    if (welcomeSubtitle) welcomeSubtitle.innerText = t.subtitle;

    userInput.placeholder = t.type_placeholder;

    // Update direction for Arabic
    if (currentLang === 'ar') {
        document.body.style.direction = 'rtl';
        document.querySelector('.chat-input-area').style.direction = 'rtl';
    } else {
        document.body.style.direction = 'ltr';
        document.querySelector('.chat-input-area').style.direction = 'ltr';
    }
}

function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('eq_lang', lang);
    updateUIText();
}

// --- Feedback Function ---
function sendFeedback() {
    Swal.fire({
        title: 'Share Your Thoughts',
        text: "EQ loves hearing from you. What's on your mind?",
        input: 'textarea',
        inputPlaceholder: 'Type your feedback here...',
        showCancelButton: true,
        confirmButtonText: 'Send to EQ',
        confirmButtonColor: 'var(--primary)',
        cancelButtonColor: '#333',
        background: '#111',
        color: '#fff',
        customClass: {
            input: 'swal-custom-textarea'
        }
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            const feedback = result.value;
            const recipient = 'championsmail18@gmail.com';
            const userEmail = window.EQ_USER.email;
            const subject = encodeURIComponent(`EQ App Feedback from ${window.EQ_USER.username}`);
            const body = encodeURIComponent(`From: ${userEmail}\n\nFeedback:\n${feedback}`);
            window.location.href = `mailto:${recipient}?subject=${subject}&body=${body}`;
            Swal.fire({
                title: 'Thank You!',
                text: 'Your feedback makes EQ better.',
                icon: 'success',
                timer: 2000,
                showConfirmButton: false,
                background: '#111',
                color: '#fff'
            });
        }
    });
}

function toggleVoiceSettings() {
    voiceSettingsPanel.classList.toggle('active');
    voiceSettingsPanel.style.display = voiceSettingsPanel.classList.contains('active') ? 'flex' : 'none';
}

// --- Chat Logic ---
function parseMarkdown(text) {
    let html = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:var(--primary); text-decoration:underline;">$1</a>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/```([\s\S]*?)```/g, '<pre>$1</pre>');
    html = html.replace(/\[DOWNLOAD:\s*([^\]]+)\]/g, (match, filename) => {
        return `<button onclick="downloadCode(this, '${filename.trim()}')" style="margin-top:8px;padding:6px 12px;background:var(--primary);border:none;border-radius:4px;cursor:pointer;color:#000;font-weight:500;">Download ${filename.trim()}</button>`;
    });
    return html;
}

window.downloadCode = function (btn, filename) {
    const messageDiv = btn.closest('.message');
    let pre = messageDiv.querySelectorAll('pre');
    if (pre.length === 0) return;
    const content = pre[pre.length - 1].textContent;
    if (filename.toLowerCase().endsWith('.pdf')) {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.text(doc.splitTextToSize(content, 180), 20, 20);
        doc.save(filename);
    } else {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; a.click();
    }
};

function addUserMessage(text) {
    if (welcomeScreen && welcomeScreen.parentNode) welcomeScreen.remove();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    const contentSpan = document.createElement('div');
    contentSpan.className = 'message-content';
    contentSpan.innerText = (currentFileName ? text + `\n[Attached: ${currentFileName}]` : text);
    messageDiv.appendChild(contentSpan);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addEQMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message eq-message';
    messageDiv.innerHTML = parseMarkdown(text);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    const t = MESSAGES_I18N[currentLang] || MESSAGES_I18N.en;
    const textSpan = document.createElement('span');
    textSpan.innerText = t.thinking || 'Thinking';
    typingDiv.appendChild(textSpan);
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        typingDiv.appendChild(dot);
    }
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingDiv;
}

async function eqRespond(userMessage) {
    const typingIndicator = showTyping();
    let prompt = userMessage;
    if (currentFileContent) {
        prompt += `\n\n[USER UPLOADED FILE CONTENT (${currentFileName})]:\n${currentFileContent}`;
        clearFile();
    }

    try {
        let userId = localStorage.getItem('eq_user_id') || 'guest_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('eq_user_id', userId);

        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: prompt,
                user_id: userId,
                language: currentLang === 'pcm' ? 'pidgin' : (currentLang === 'en' ? 'english' : currentLang),
                local_time: new Date().toLocaleString()
            })
        });

        const data = await res.json();
        if (typingIndicator.parentNode) typingIndicator.remove();
        if (data.alert) alert(data.alert);
        addEQMessage(data.response);

    } catch (error) {
        if (typingIndicator.parentNode) typingIndicator.remove();
        addEQMessage("Hey — I'm having trouble connecting to the cloud right now ☁️");
    }
}

function handleSend() {
    const message = userInput.value.trim();
    if (message || currentFileContent) {
        addUserMessage(message || "(File Upload)");
        userInput.value = '';
        eqRespond(message || "Analyze this file.");
    }
}

sendButton.addEventListener('click', handleSend);
userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { handleSend(); } });

userInput.addEventListener('input', () => {
    const hasText = userInput.value.trim().length > 0;
    sendButton.style.opacity = hasText ? '1' : '0';
    sendButton.style.visibility = hasText ? 'visible' : 'hidden';
    sendButton.style.pointerEvents = hasText ? 'all' : 'none';
});

uploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const userId = localStorage.getItem('eq_user_id');
    if (userId) formData.append('user_id', userId);

    try {
        uploadBtn.style.opacity = '0.5';
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (!data.error) {
            currentFileContent = data.full_content || data.content;
            currentFileName = data.filename;
            fileIndicator.classList.add('active');
            fileNameSpan.textContent = data.filename;
        }
    } catch (err) { alert('Upload failed'); }
    finally { uploadBtn.style.opacity = '1'; fileInput.value = ''; }
});

window.clearFile = function () { currentFileContent = ""; currentFileName = ""; fileIndicator.classList.remove('active'); };

async function checkPreferences() {
    try {
        const res = await fetch('/preferences');
        const data = await res.json();
        if (data.personality_description) document.getElementById('prefAboutMe').value = data.personality_description;
        if (data.response_style) document.getElementById('prefStyle').value = data.response_style;
        if (data.tone) document.getElementById('prefTone').value = data.tone;
        if (data.theme) { document.getElementById('prefTheme').value = data.theme; applyThemeToBody(data.theme); }
        if (!data.personality_description) document.getElementById('onboardingOverlay').classList.add('active');
    } catch (err) { console.error("Failed to load preferences:", err); }
}

window.applyThemeToBody = function (theme) {
    document.body.classList.remove('theme-midnight-neon', 'theme-calm-forest', 'theme-ocean-breeze', 'theme-sunset-rose');
    if (theme === 'Midnight Neon') document.body.classList.add('theme-midnight-neon');
    else if (theme === 'Calm Forest') document.body.classList.add('theme-calm-forest');
    else if (theme === 'Ocean Breeze') document.body.classList.add('theme-ocean-breeze');
    else if (theme === 'Sunset Rose') document.body.classList.add('theme-sunset-rose');
};

async function submitOnboarding() {
    const personality = document.getElementById('onboardingAbout').value.trim();
    if (!personality) return;
    const prefs = {
        personality_description: personality,
        response_style: document.getElementById('onboardingStyle').value,
        tone: document.getElementById('onboardingTone').value,
        theme: document.getElementById('onboardingTheme').value
    };
    const success = await updatePreferences(prefs);
    if (success) {
        document.getElementById('onboardingOverlay').classList.remove('active');
        checkPreferences(); // Sync
    }
}
window.submitOnboarding = submitOnboarding;

async function updatePreferences(prefs) {
    try {
        const res = await fetch('/preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prefs)
        });
        return (await res.json()).success;
    } catch (err) { return false; }
}

window.addEventListener('load', () => {
    updateUIText();
    checkPreferences();
});

// PWA Install
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('logoInstall')?.classList.add('install-ready');
    const welcomeInstallBtn = document.getElementById('welcomeInstallBtn');
    if (welcomeInstallBtn) welcomeInstallBtn.style.display = 'inline-block';
});
