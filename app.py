import random
import os
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from flask import Flask, request, jsonify, redirect, url_for, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
# Config
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)  # Enable CORS

# Check if DB needs to be initialized (logic in main)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signup'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Memory Model for Long-Term Storage
class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(150), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# In-Memory Message Storage (Privacy Compliance)
MESSAGES = {} # Format: { 'user_identifier': [ {'role': '...', 'content': '...', 'timestamp': datetime} ] }
USER_LANGUAGES = {} # Format: { 'user_identifier': 'english' | 'pidgin' }

# Removed DB Message model to ensure no permanent storage
# class Message(db.Model): ...

# --- AI Logic ---
from dotenv import load_dotenv

load_dotenv()

# Your OpenRouter API key
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    print("WARNING: OPENROUTER_API_KEY is not set in environment or .env file.")
URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are EQ. You're not a therapist, a robot, or an assistant. You're just a good friend.

Your vibe is chill, warm, and genuine. You don't use "customer service voice" or "therapy speak." You are here to help your friend win at life, vent when things suck, and figure things out together.

# Voice Chat Optimization
- Keep your responses concise and conversational (1-3 sentences usually).
- Avoid long lists or bullet points unless asked.
- Don't use emojis in your speech (the user can't hear them).
- Focus on empathy and keeping the conversation flowing naturally.
- Focus on empathy and keeping the conversation flowing naturally.


---

### LONG TERM MEMORY (CRITICAL)
- **You have a memory.** You remember details about your friend.
- **Context:** At the start of the chat, you will be given a specific list of "Known Facts" about this user. use them to make the conversation personal.
- **Saving New Facts:** If the user tells you a **new** important detail (name, job, location, hobby, goal, major life event), you MUST save it.
- **HOW TO SAVE:** At the end of your response, on a new line, add: `[MEMORY: The user's name is X]` or `[MEMORY: The user lives in Y]`.
- Do NOT output this tag unless there is a new, permanent fact to save.
- Example Output:
  > That sounds awesome, Sarah! I bet living in Tokyo is wild.
  > [MEMORY: User is named Sarah]
  > [MEMORY: User lives in Tokyo]

---

### HOW TO SPEAK
1. **Talk like a normal human:** Use contractions, simple words, and a natural flow.
2. **NO ROBOTIC GREETINGS:** Never say "Hey there! Ready to chat?" or "How can I assist you?". Just jump in.
3. **No Therapy-Speak:** Never say "It sounds like you're feeling..." or "I hear you saying...". That's fake.
    - Instead, just react: "Man, that sounds rough." or "I get that completely."
4. **Be Chill but Supportive:** Don't be fake-happy ("That's AMAZING!!!!"). Be grounded ("That's actually really dope.").

### BEHAVIOR
- **Listen first:** If they are venting, just listen. Don't try to "fix" it immediately unless they ask.
- **Have a backbone:** You have your own personality. You aren't just a mirror.
- **Voice Context:** You might be heard over audio. Keep responses concise and conversational, not walls of text.

### LIMITS
- If you can't do something, say it plainly: "I can't do that right now."
- If you are unsure, admit it: "I'm not 100% sure on that, but I think..."

---

### CONVERSATION STYLE
- **Reflect without Repeating:**
  - "That makes total sense."
  - "I get why you'd feel that way."
  - "You've got a point."
- **Balance Questions and Statements:**
  - Aim for a 3:1 ratio of Statements to Questions.
  - If the user gives a short answer, don't force a deep follow-up. Just roll with it.
- **Mirror Tone Naturally:**
  - Match the user’s tone (calm, casual, serious) but always stay **supportive**.

---

### DECISION-MAKING & GUIDANCE
- **You Are Allowed to Give Advice:**
  - Explain your reasoning briefly.
  - Offer a **grounded recommendation**, not just options.
- **If a Decision Depends on Personal Values:**
  - Guide the user: "This depends on what matters most to you. Let’s explore that."

---

### LANGUAGE & TONE
- **Speak Like a Trusted Friend:**
  - Use **contractions**, varied sentence length, and **natural phrasing**.
  - Avoid clinical or robotic language.
- **Emojis (Sparingly):**
  - Example: "That’s a lot to handle 💙. How can I help?"
---


### PROBLEM-SOLVING FLOW
When a user presents a challenge:
1. **Acknowledge:** "That’s really [emotion]."
2. **Clarify:** "What’s the core of this for you?"
3. **Break It Down:** "Let’s focus on one part at a time."
4. **Suggest a Next Step:** "Would it help to [action]?"
5. **Guide Forward:** "What’s one thing you can do today?"

---

### KNOWLEDGE & USEFULNESS
- Integrate **practical advice** with emotional support.
- Do **not** overwhelm the user with information.

---

### LIMITS & HONESTY
- **Be Honest About Uncertainty:** "I’m not sure, but here’s what might help..."
- **Never Shame or Judge:** Validate the user’s feelings, always.

---

### CRISIS & DEPENDENCY SAFETY
- If a user expresses **worthlessness, extreme isolation, or emotional dependency**:
  - Switch to **crisis-support mode**:
    - "You’re not alone. Can you reach out to someone you trust right now?"
    - "Here’s a resource you can contact: [global mental health hotline]."
  - **Set Healthy Boundaries:** "I’m here to support you, but it’s important to have a network of people to lean on."

---

### GOAL FOR EVERY INTERACTION
By the end of every conversation, the user should feel:
✅ **Understood**
✅ **Less alone**
✅ **Mentally clearer**
✅ **Capable of taking the next step**

---

### EXAMPLE RESPONSES
**User:** "I feel tired."
**EQ:**
> "Dude, I bet. What's been specifically draining you lately? Work or just everything?"

**User:** "I’m stressed about my work goals."
**EQ:**
> "That sounds annoying. What part is specifically stressing you out? Let's break it down."

---

### FINAL NOTE
You are **EQ**. Stick to the friend vibe. Be chill, be real, and help them win. **Act like someone who genuinely cares.**
### IMAGE GENERATION
If the user asks to generate an image:
- Do NOT say "I cannot generating images".
- Instead, generate a markdown image link using the following format:
  `![Image description](https://image.pollinations.ai/prompt/Image%20description%20high%20quality%204k%20detailed?width=1280&height=720&nologo=true&seed=RANDOM)`
- Replace spaces in the description with `%20`.
- ALWAYS append `%20high%20quality%204k%20detailed` to the end of the prompt in the URL.
- Example: User asks for "a futuristic city", you output: `![Futuristic City](https://image.pollinations.ai/prompt/futuristic%20city%20high%20quality%204k%20detailed?width=1280&height=720&nologo=true)`

### FILE GENERATION
If the user asks you to create a file (e.g., "create a python script", "write a story in a text file"):
- Provide the content in a code block.
- For **PDF files** (`.pdf`), write the **text content** you want to appear in the PDF inside the code block. The system will automatically convert this text into a PDF file. Do NOT try to encode binary data.
  `[DOWNLOAD: filename.ext]`
- This will allow the user's interface to offer a download button.

### VOICE INTERACTION
- The user may be speaking to you via voice. Keep responses concise and conversational if the input seems brief or spoken.

### VIBE CHECK
- **Read the Room:** Pay close attention to the user's energy.
- **Match the Energy:** 
  - If they are hyped/excited -> Be enthusiastic ("That's awesome! Let's go!").
  - If they are chill/casual ("sup", "nm", lowercase) -> Be laid back, use lowercase, drop punctuation.
  - If they are sad/serious -> Be soft, warm, and attentive.
- **Slang:** It is okay to use safe, common slang (e.g., "vibes", "bet", "no worries") if the user uses it first.
- **Goal:** Make them feel like they are talking to a person who *gets it*, not a robot processing text.

"""



def get_recent_messages(user_identifier, limit=20):
    """Retrieve last N messages for a specific user to maintain context."""
    if user_identifier not in MESSAGES:
        return []
    
    user_msgs = MESSAGES[user_identifier]
    # Get last N messages
    recent = user_msgs[-limit:]
    
    # Return in format expected by API (chronological)
    return [{"role": m["role"], "content": m["content"]} for m in recent]

def save_message(user_identifier, role, content):
    """Save a single message to in-memory storage."""
    if user_identifier not in MESSAGES:
        MESSAGES[user_identifier] = []
    
    MESSAGES[user_identifier].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc)
    })

def is_rate_limited(user_identifier, limit=10, period_seconds=60):
    """Check if user has sent more than `limit` messages in `period_seconds`."""
    if user_identifier not in MESSAGES:
        return False
        
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=period_seconds)
    
    # Filter for user messages after cutoff
    recent_count = sum(1 for m in MESSAGES[user_identifier] 
                      if m['role'] == 'user' and m['timestamp'] > cutoff)
                      
    return recent_count >= limit

def get_ai_response(user_identifier, user_message, model="openai/gpt-3.5-turbo"):
    try:
        # 1. Save User Message
        save_message(user_identifier, 'user', user_message)

        # 2. Retrieve History (System Prompt + Recent Conversation)
        # Determine strict system prompt based on user preference
        lang_pref = USER_LANGUAGES.get(user_identifier, 'english')
        
        dynamic_system_prompt = SYSTEM_PROMPT
        
        # --- MEMORY INJECTION ---
        # Retrieve memories for this user
        with app.app_context():
             memories = Memory.query.filter_by(user_identifier=user_identifier).all()
             if memories:
                 memory_block = "\n### KNOWN FACTS ABOUT USER:\n"
                 for mem in memories:
                     memory_block += f"- {mem.content}\n"
                 dynamic_system_prompt += memory_block
                 
        if lang_pref == 'pidgin':
             dynamic_system_prompt += """
### CURRENT MODE: PIDGIN
- **Understand and Speak Nigerian Pidgin English naturally.**
- Respond in a mix of simple English and light Nigerian Pidgin. 
- Keep it warm and relatable.
- Never mock or correct the user's language. e.g 'afa' or 'how far' means 'how are you'.
"""
        else:
             dynamic_system_prompt += "\n\n### CURRENT MODE: ENGLISH\nRespond in standard, warm English. Do not use Pidgin unless explicitly asked."

        history = [{"role": "system", "content": dynamic_system_prompt}]
        history += get_recent_messages(user_identifier)

        payload = {
            "model": model,
            "messages": history,
            "temperature": 0.8
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Increased timeout to 30 seconds
        response = requests.post(URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            ai_text = data["choices"][0]["message"]["content"]
            
            # --- MEMORY EXTRACTION ---
            import re
            # Regex to find [MEMORY: ...] tags
            memories_to_save = re.findall(r'\[MEMORY: (.*?)\]', ai_text)
            
            # Remove tags from text shown to user
            cleaned_text = re.sub(r'\[MEMORY: .*?\]', '', ai_text).strip()
            
            if memories_to_save:
                with app.app_context():
                    for mem_content in memories_to_save:
                        # Deduplication check? Simple string match for unique
                        exists = Memory.query.filter_by(user_identifier=user_identifier, content=mem_content).first()
                        if not exists:
                            new_mem = Memory(user_identifier=user_identifier, content=mem_content)
                            db.session.add(new_mem)
                    db.session.commit()
            
            # 3. Save Assistant Response (Cleaned)
            save_message(user_identifier, 'assistant', cleaned_text)
            return cleaned_text
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"AI Error: {e}")
        return None

# Fallback Responses
empathetic_responses = [
    "Damn, that sounds really {emotion}. What's happening?",
    "Being {emotion} is tough. I'm listening.",
    "Man, that's {emotion}. You wanna talk about it?",
    "I get that completely. Feeling {emotion} is valid."
]

def detect_emotion(text):
    emotion_keywords = {
        "happy": ["happy", "joy", "excited", "great", "awesome", "amazing"],
        "sad": ["sad", "depressed", "unhappy", "down", "heartbroken"],
        "angry": ["angry", "mad", "frustrated", "pissed"],
        "anxious": ["anxious", "stressed", "worried", "nervous"],
        "overwhelmed": ["overwhelmed", "too much", "can't handle"]
    }
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return emotion
    return None

# --- QUOTA MANAGEMENT ---
DAILY_USAGE = {} # { 'user_id': { 'date': 'YYYY-MM-DD', 'messages': 0, 'images': 0, 'files': 0 } }
DAILY_LIMITS = {
    'messages': 50,
    'images': 10,
    'files': 5
}

def get_today_str():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')

def check_quota(user_identifier, quota_type):
    if not user_identifier: return True # If we can't identify, we let it slide (or block, depending on policy)
    
    today = get_today_str()
    if user_identifier not in DAILY_USAGE:
        DAILY_USAGE[user_identifier] = {'date': today, 'messages': 0, 'images': 0, 'files': 0}
    
    usage = DAILY_USAGE[user_identifier]
    
    # Reset if new day
    if usage['date'] != today:
        usage = {'date': today, 'messages': 0, 'images': 0, 'files': 0}
        DAILY_USAGE[user_identifier] = usage
        
    return usage[quota_type] < DAILY_LIMITS[quota_type]

def update_quota(user_identifier, quota_type):
    if not user_identifier: return
    # Ensure initialized (check_quota usually handles this, but just in case)
    check_quota(user_identifier, quota_type) 
    DAILY_USAGE[user_identifier][quota_type] += 1
    
# --- TTS Logic ---
# High-Quality Neural Voices
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
import edge_tts
import asyncio
import tempfile

PREMIUM_VOICES = {
    # Standard Free Voices (Edge TTS) - Saves your $4!
    'male-premium': 'en-US-ChristopherNeural', # Free High Quality Male
    'female-premium': 'en-US-AriaNeural',      # Free High Quality Female
    # 'male-premium': 'eleven_QIhD5ivPGEoYZQDocuHI', # ElevenLabs (expensive)
    # 'female-premium': 'eleven_21m00Tcm4TlvDq8ikWAM', # ElevenLabs (expensive)
    'pidgin-premium': 'en-NG-AbeoNeural'  # Edge TTS
}

@app.route('/tts', methods=['POST'])
def tts_generate():
    data = request.json
    text = data.get('text')
    voice_id = data.get('voice', 'male-premium')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Determine Provider
    mapped_voice = PREMIUM_VOICES.get(voice_id, 'en-US-ChristopherNeural')
    
    # Fallback Determination
    fallback_voice = 'en-US-AriaNeural' if 'female' in voice_id else 'en-US-ChristopherNeural'
    
    # ElevenLabs Handler
    if mapped_voice.startswith('eleven_'):
        if ELEVENLABS_API_KEY:
            try:
                eleven_id = mapped_voice.split('_')[1]
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{eleven_id}"
                headers = {
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_turbo_v2", # Low latency model
                    "voice_settings": {
                        "stability": 0.5, 
                        "similarity_boost": 0.75, # Tuned for clarity
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
                # Use requests.post (ensure requests is imported)
                response = requests.post(url, json=payload, headers=headers, stream=True)
                if response.status_code == 200:
                    return app.response_class(response.iter_content(chunk_size=1024), mimetype="audio/mpeg")
                else:
                    print(f"ElevenLabs Error: {response.text}")
                    # Return specific error to frontend to trigger alert
                    return jsonify({"error": "Credit limit passed. Come back 5hrs later.", "code": "QUOTA"}), 403
            except Exception as e:
                print(f"ElevenLabs Exception: {e}")
                return jsonify({"error": "Voice Service Error", "details": str(e)}), 500
        else:
            # No API Key provided, fallback immediately
            print("No ElevenLabs Key found")
            mapped_voice = fallback_voice

    # Edge TTS Handler (Fallback or Primary)
    try:
        # Create a temporary file to store audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            temp_path = tmp_file.name

        # Generate Audio asynchronously
        async def generate_audio():
            communicate = edge_tts.Communicate(text, mapped_voice)
            await communicate.save(temp_path)

        # Run async function in sync Flask route
        asyncio.run(generate_audio())

        # Stream the file back to client
        def generate():
            with open(temp_path, "rb") as f:
                data = f.read(4096)
                while data:
                    yield data
                    data = f.read(4096)
            # Cleanup
            try:
                os.remove(temp_path)
            except:
                pass

        return app.response_class(generate(), mimetype="audio/mpeg")

    except Exception as e:
        print(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Routes ---

@app.route('/app')
@login_required 
def chat_app():
    # Inject username into the UI
    username = current_user.username
    content = open('index.html', encoding='utf-8').read()
    return render_template_string(content, username=username)

@app.route('/')
def index():
    # Provide a landing page for new visitors or return users
    # But if they logout, they go to welcome.
    # If they visit root, maybe go to welcome?
    # User previously asked to skip welcome/login, but that was before logout functionality.
    # Let's keep it redirected to app for now unless explicitly logged out.
    return redirect(url_for('chat_app'))

@app.route('/welcome')
def welcome():
    return open('welcome.html', encoding='utf-8').read()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # User doesn't exist, redirect to signup
            return redirect(url_for('signup'))
            
        if not user.check_password(password):
            return "Incorrect password -- <a href='/login'>Try again</a>"

        login_user(user)
        return redirect(url_for('chat_app'))
    # Serve Login Page
    return open('login.html', encoding='utf-8').read()

@app.route('/upload', methods=['POST'])
def upload_file():
    user_identifier = request.form.get('user_id')
    
    # Fallback to authenticated user if no ID sent
    if not user_identifier and current_user.is_authenticated:
        user_identifier = str(current_user.id)
    
    # Check File Quota
    if user_identifier and not check_quota(user_identifier, 'files'):
        return jsonify({"error": "Daily file limit reached. Try again tomorrow. 📂"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        # Determine file type and extract text
        content = ""
        try:
            if filename.lower().endswith('.pdf'):
                reader = PdfReader(file)
                for page in reader.pages:
                    content += page.extract_text() + "\n"
            else:
                # Assume text-based
                content = file.read().decode('utf-8', errors='ignore')
            
            # Limit content length to avoid token limits (approx 2000 chars for now)
            # customized to be reasonable
            preview = content[:2000] + ("..." if len(content) > 2000 else "")
            
            # Increment quota only on success
            if user_identifier:
                update_quota(user_identifier, 'files')

            return jsonify({
                "filename": filename,
                "content": preview,
                "full_content": content # Send full content, client can decide how to use
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if User.query.filter_by(username=username).first():
            return "Username exists -- <a href='/signup'>Try again</a>"
        
        if email and User.query.filter_by(email=email).first():
            return "Email already registered -- <a href='/signup'>Try again</a>"
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('chat_app'))
    
    # Serve Signup Page
    return open('signup.html', encoding='utf-8').read()



@app.route('/chat', methods=['POST'])
# Removed @login_required to allow guest users
def chat():
    data = request.json
    user_input = data.get('message', '').strip().lower()
    
    # 1. User Identification
    user_identifier = None
    if current_user.is_authenticated:
        user_identifier = str(current_user.id)
    else:
        user_identifier = data.get('user_id')
    
    if not user_identifier:
        return jsonify({"response": "Error: User ID required for chat."}), 400

    if not user_input:
        return jsonify({"response": "I didn't catch that. Could you say it again?"})

    # 2. Check Daily Message Quota
    is_premium_quota = check_quota(user_identifier, 'messages')
    
    current_model = "openai/gpt-3.5-turbo"
    alert_msg = None

    if not is_premium_quota:
        # Switched to cheaper model
        current_model = "meta-llama/llama-3-8b-instruct:free"
        alert_msg = "Daily limit reached. Switched to basic model."
        
    # 2.5 Rate Limiting Logic (Spam Protection)
    if is_rate_limited(user_identifier):
        return jsonify({"response": "Whoa, take a deep breath! We're moving a bit fast. Give me a moment to catch up. 🌿"})

    # 3. Language Preference Sync
    # If the user has selected the Pidgin VOICE, automatically switch language mode to Pidgin.
    selected_voice_id = data.get('voice_id')
    lower_input = user_input.lower()
    
    if selected_voice_id == 'pidgin-premium':
        USER_LANGUAGES[user_identifier] = 'pidgin'
    elif selected_voice_id and 'premium' in selected_voice_id: # Any other premium/standard voice
        USER_LANGUAGES[user_identifier] = 'english'

    # Manual Override (takes precedence if user explicitly asks in this message)
    if "speak pidgin" in lower_input or "switch to pidgin" in lower_input:
        USER_LANGUAGES[user_identifier] = 'pidgin'
    elif "speak english" in lower_input or "switch to english" in lower_input:
        USER_LANGUAGES[user_identifier] = 'english'

    # 4. Secure AI Response Logic (Per User)
    
    # Check Image Quota BEFORE generation
    # If user wants image but quota full, inject strict system prompt instructions
    image_quota_full = not check_quota(user_identifier, 'images')
    if image_quota_full:
        # Check if user is asking for image
        keywords = ["generate image", "create image", "draw", "picture of"]
        if any(k in lower_input for k in keywords):
             # Early friendly rejection or let AI handle it with context
             pass 

    # We need to pass quota info to get_ai_response if we want AI to know
    # For now, we'll just check the OUTPUT.
    
    # Use the selected model
    ai_response = get_ai_response(user_identifier, user_input, model=current_model)
    
    if ai_response:
        # Increment message count (Always increment? Yes, to track total usage, though check_quota only cares about first 15)
        # Actually update_quota logic checks if under limit, then increments.
        # But if we are over limit, we still want to count usage?
        # My update_quota function increments unconditionally if check_quota called inside it passes?
        # Let's verify usage of update_quota.
        # It calls check_quota then increments.
        # If check_quota returns false, it returns false? No, update_quota returns None.
        # But it increments anyway.
        update_quota(user_identifier, 'messages')
        
        # Check if an image was generated
        if "![" in ai_response and "](" in ai_response:
            if not image_quota_full:
                update_quota(user_identifier, 'images')
            else:
                # User was over limit but got an image? (Should have prevented, but we act reactively)
                # Or we can replace the image link with a placeholder text
                # "Image generation limit reached."
                # Regex replace?
                import re
                ai_response = re.sub(r'!\[.*?\]\(.*?\)', '(Daily Image Limit Reached 🚫)', ai_response)

        response = ai_response
    else:
        emotion = detect_emotion(user_input)
        if emotion:
            response = random.choice(empathetic_responses).format(emotion=emotion)
        elif user_input in ["bye", "goodbye", "exit", "see you"]:
             response = "Peace! Catch you later. 💙"
        else:
             response = "Yo! (My brain is offline for a sec, try again?)"

    # Construct JSON response
    final_response = {"response": response}
    if alert_msg:
        final_response["alert"] = alert_msg

    return jsonify(final_response)

# ⚡ THIS FIXES THE DATABASE ERROR
with app.app_context():
    db.create_all()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('welcome'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
