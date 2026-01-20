import os

login_path = "c:\\Users\\USER\\Documents\\eq1\\login.html"
welcome_path = "c:\\Users\\USER\\Documents\\eq1\\welcome.html"
bot_path = "c:\\Users\\USER\\Documents\\eq1\\eq_bot.py"

def verify_files():
    # 1. Verify Login Disclaimer
    if os.path.exists(login_path):
        with open(login_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "Conversations are temporary and not permanently stored" in content and ".disclaimer" in content:
                print("SUCCESS: Login disclaimer found.")
            else:
                print("FAILED: Login disclaimer missing.")
    else:
        print(f"FAILED: {login_path} not found.")

    # 2. Verify Welcome Page
    if os.path.exists(welcome_path):
        with open(welcome_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "RAE" in content and "EQ" in content and "Login" in content:
                print("SUCCESS: Welcome page created with key elements.")
            else:
                print("FAILED: Welcome page missing key elements.")
    else:
        print(f"FAILED: {welcome_path} not found.")

    # 3. Verify Bot Routes (Simple string check)
    if os.path.exists(bot_path):
        with open(bot_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "@app.route('/app')" in content and "def chat_app():" in content:
                print("SUCCESS: '/app' route found.")
            else:
                print("FAILED: '/app' route missing.")
            
            if "@app.route('/')" in content and "def index():" in content and "welcome.html" in content:
                print("SUCCESS: '/' index route found.")
            else:
                print("FAILED: '/' index route missing or incorrect.")
    else:
        print(f"FAILED: {bot_path} not found.")

if __name__ == "__main__":
    verify_files()
