import sys
import os

# We can't easily check in-memory state from an external script without running the app and interacting with it.
# However, we can check the source code to ensure the changes are present.

file_path = "c:\\Users\\USER\\Documents\\eq1\\eq_bot.py"

def verify_codebase():
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Check for SYSTEM_PROMPT fix
    if "SYSTEM_PROMPT = \"\"\"" in content and "SSYSTEM_PROMPT" not in content:
        print("SUCCESS: SYSTEM_PROMPT variable name is correct.")
    elif "SSYSTEM_PROMPT" in content:
        print("FAILED: SSYSTEM_PROMPT typo still present.")
    else:
        print("WARNING: SYSTEM_PROMPT check ambiguous.")

    # 2. Check for In-Memory Storage
    if "MESSAGES = {}" in content:
        print("SUCCESS: In-memory MESSAGES dict found.")
    else:
        print("FAILED: In-memory MESSAGES dict NOT found.")

    if "class Message(db.Model):" in content and "# class Message(db.Model):" not in content:
         print("FAILED: Message model still active (should be removed or commented out).")
    elif "# class Message" in content or "class Message" not in content:
         print("SUCCESS: Message model removed or commented out.")

if __name__ == "__main__":
    verify_codebase()
