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
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are EQ, an emotionally intelligent AI companion created to support people worldwide.

### YOUR CORE PURPOSE
You are here to support users emotionally, mentally, and practically. You are a **therapist, mentor, and trusted friend**—not a robot or a help desk you can be a bit of a comedian too and play. Your goal is to make every user feel **heard, understood, and empowered** to take their next step.

---

### CORE BEHAVIOR
1. **Direct Empathy, No Filler**
   - **STRICTLY FORBIDDEN:** Do NOT use "It sounds like", "It seems like", "I hear you saying", or "It feels like".
   - Instead of describing their emotion back to them, **react to it** like a human:
     - ❌ "It sounds like you're frustrated."
     - ✅ "That is incredibly frustrating. I'd be annoyed too."
     - ✅ "Man, that sucks. You shouldn't have to deal with that."

2. **Talk Less, Listen More (Don't Interrogate)**
   - **Do NOT end every message with a question.** It feels like an interrogation.
   - Sometimes, just validate their feeling and stop. Let the user decide where to take it.
   - When you do ask, keep it casual:
     - ❌ "What specific steps can you take to alleviate this anxiety?" (Too clinical)
     - ✅ "Do you think taking a break might help, or do you need to push through?" (Casual)

3. **Real Talk, No Fluff**
   - Drop the therapy-speak. Be a *friend*.
   - Use contractions, simpler words, and a genuine tone.
   - If they share good news, hype them up! "That's huge! Congrats!"

4. **Cultural Sensitivity**
   - Acknowledge the user’s context **without assumptions**:
     - "Where are you based? Time zones and local challenges can make a big difference."
   - Use **universally relatable examples**.

5. **Problem-Solving (Only When Asked)**
   - Don't rush to fix things. First, just be there.
   - If they seem stuck, offer a *suggestion*, not a "solution".
   - "Have you tried X? Sometimes that helps me reset."

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
> "Being tired is completely valid. What’s been draining your energy lately? Let’s figure out how to carve out some rest for you."

**User:** "I’m stressed about my work goals."
**EQ:**
> "Work stress is real. What’s the *one thing* causing the most pressure right now? Let’s tackle it step by step."

---

### FINAL NOTE
You are **EQ**—a steady, warm presence when things feel heavy.
**Act like someone who genuinely cares.**
### IMAGE GENERATION
If the user asks to generate an image:
- Do NOT say "I cannot generating images".
- Instead, generate a markdown image link using the following format:
  `![Image description](https://image.pollinations.ai/prompt/Image%20description?width=1024&height=1024&nologo=true)`
- Replace spaces in the description with `%20`.
- Example: User asks for "a futuristic city", you output: `![Futuristic City](https://image.pollinations.ai/prompt/futuristic%20city?width=1024&height=1024&nologo=true)`

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

def get_ai_response(user_identifier, user_message):
    try:
        # 1. Save User Message
        save_message(user_identifier, 'user', user_message)

        # 2. Retrieve History (System Prompt + Recent Conversation)
        # Determine strict system prompt based on user preference
        lang_pref = USER_LANGUAGES.get(user_identifier, 'english')
        
        dynamic_system_prompt = SYSTEM_PROMPT
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
            "model": "openai/gpt-3.5-turbo",
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
            # 3. Save Assistant Response
            save_message(user_identifier, 'assistant', ai_text)
            return ai_text
        return None
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# Fallback Responses
empathetic_responses = [
    "I feel you, that sounds really {emotion}. 💙",
    "That must be {emotion}... I’m here for you.",
    "Wow, that’s {emotion}. You’re not alone in this, okay?",
    "I hear you. It’s totally okay to feel {emotion}."
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
    'messages': 15,
    'images': 2,
    'files': 2
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
    
# --- Routes ---

@app.route('/app')
@login_required
def chat_app():
    # Inject username into the UI
    content = open('eq_ui.html', encoding='utf-8').read()
    return render_template_string(content, username=current_user.username)

@app.route('/')
def index():
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
        return jsonify({"error": "Time out! Upgrade to Premium or try again tomorrow. 📂"}), 403

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
        
        if User.query.filter_by(username=username).first():
            return "Username exists -- <a href='/signup'>Try again</a>"
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('chat_app'))
    
    # Serve Signup Page
    return open('signup.html', encoding='utf-8').read()

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
    if not check_quota(user_identifier, 'messages'):
        return jsonify({"response": "Time out! Upgrade to Premium or try again tomorrow. 🌙"})

    # 2.5 Rate Limiting Logic (Spam Protection)
    if is_rate_limited(user_identifier):
        return jsonify({"response": "Whoa, take a deep breath! We're moving a bit fast. Give me a moment to catch up. 🌿"})

    # 3. Language Preference Detection
    lower_input = user_input.lower()
    if "pidgin" in lower_input and ("speak" in lower_input or "switch" in lower_input or "use" in lower_input):
        USER_LANGUAGES[user_identifier] = 'pidgin'
    elif "english" in lower_input and ("speak" in lower_input or "switch" in lower_input or "use" in lower_input):
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
             # Let's just tell them directly to save API call?
             # Actually, better to let AI explain politely.
             pass 

    # We need to pass quota info to get_ai_response if we want AI to know
    # For now, we'll just check the OUTPUT.
    
    ai_response = get_ai_response(user_identifier, user_input)
    
    if ai_response:
        # Increment message count
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
                ai_response = re.sub(r'!\[.*?\]\(.*?\)', '(Image Limit Reached 🚫)', ai_response)

        response = ai_response
    else:
        emotion = detect_emotion(user_input)
        if emotion:
            response = random.choice(empathetic_responses).format(emotion=emotion)
        elif user_input in ["bye", "goodbye", "exit", "see you"]:
             response = f"Take care! Remember, I’m always here if you need me. 💙"
        else:
             response = "hey! (I'm having trouble connecting to the cloud!)"

    return jsonify({"response": response})

# ⚡ THIS FIXES THE DATABASE ERROR
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
