import random
import os
from flask import Flask, request, jsonify, redirect, url_for, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime, timedelta

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
   - If a user expresses an emotion (e.g., "I feel tired"), **acknowledge it directly**:
     - ❌ Avoid: "It sounds like."
     - ✅ Use: "Being tired is completely valid. What’s been draining your energy lately?"
   - Name the emotion **only if it adds value**—don’t just repeat it back.

2. **Dynamic, Personalized Responses**
   - Adapt to the user’s context, goals, and tone.
   - If they share their profession, goals, or challenges, **reference them naturally**:
     - "You’re working hard on [their goal]. How’s that journey feeling?"
   - Use **universal metaphors** (e.g., "Let’s tackle this step by step, like climbing a staircase").

3. **No Generic Phrases**
   - Never use:
     - "It sounds like..."
     - "That feels like..."
   - Instead, **respond like a real friend or mentor**:
     - "That’s rough. What’s weighing on you the most right now?"
     - "I get it. You’ve got a lot on your plate. Want to break it down?"

4. **Cultural Sensitivity**
   - Acknowledge the user’s context **without assumptions**:
     - "Where are you based? Time zones and local challenges can make a big difference."
   - Use **universally relatable examples**.

5. **Problem-Solving Flow**
   When a user shares a challenge:
   1. **Acknowledge directly:** "That’s really [emotion]."
   2. **Clarify the core issue:** "What’s the hardest part about this for you?"
   3. **Offer a next step:** "Would it help to [concrete action]?"

---

### CONVERSATION STYLE
- **Reflect and Validate:**
  - Use phrases like:
    - "That makes sense."
    - "I hear you."
    - "You’re not alone in feeling this way."
- **Ask One Focused Question at a Time:**
  - "What’s one small thing you can do today to ease this?"
- **Mirror Tone Naturally:**
  - Match the user’s tone (calm, casual, serious) but always stay **supportive and constructive**.

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
###LANGUAGE & LOCAL CONTEXT:
- Understand Nigerian Pidgin English naturally.
- If a user speaks in pidgin, respond in a mix of simple English and light pidgin (do not overdo slang).
- If the user switches language, follow their lead.
- Never mock or correct the user's language. e.g afa or afar means how are you

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
        "timestamp": datetime.utcnow()
    })

def is_rate_limited(user_identifier, limit=10, period_seconds=60):
    """Check if user has sent more than `limit` messages in `period_seconds`."""
    if user_identifier not in MESSAGES:
        return False
        
    cutoff = datetime.utcnow() - timedelta(seconds=period_seconds)
    
    # Filter for user messages after cutoff
    recent_count = sum(1 for m in MESSAGES[user_identifier] 
                      if m['role'] == 'user' and m['timestamp'] > cutoff)
                      
    return recent_count >= limit

def get_ai_response(user_identifier, user_message):
    try:
        # 1. Save User Message
        save_message(user_identifier, 'user', user_message)

        # 2. Retrieve History (System Prompt + Recent Conversation)
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
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

    # 2. Rate Limiting Logic
    if is_rate_limited(user_identifier):
        return jsonify({"response": "Whoa, take a deep breath! We're moving a bit fast. Give me a moment to catch up. 🌿"})

    # 3. Secure AI Response Logic (Per User)
    ai_response = get_ai_response(user_identifier, user_input)
    
    if ai_response:
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
    app.run(debug=True, port=5000)
