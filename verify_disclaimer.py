import os

file_path = "c:\\Users\\USER\\Documents\\eq1\\signup.html"

def verify_disclaimer():
    if not os.path.exists(file_path):
        print(f"FAILED: {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    disclaimer_text = "Conversations are temporary and not permanently stored."
    disclaimer_class = ".disclaimer"

    if disclaimer_text in content:
        print("SUCCESS: Disclaimer text found.")
    else:
        print("FAILED: Disclaimer text NOT found.")

    if disclaimer_class in content:
        print("SUCCESS: Disclaimer CSS class found.")
    else:
        print("FAILED: Disclaimer CSS class NOT found.")

if __name__ == "__main__":
    verify_disclaimer()
