import os

welcome_path = "c:\\Users\\USER\\Documents\\eq1\\welcome.html"
image_path = "c:\\Users\\USER\\Documents\\eq1\\static\\RAE-removebg-preview.png"

def verify_image():
    # 1. Verify Image File Exists
    if os.path.exists(image_path):
        print(f"SUCCESS: Image found at {image_path}")
    else:
        print(f"FAILED: Image NOT found at {image_path}")

    # 2. Verify HTML Reference
    if os.path.exists(welcome_path):
        with open(welcome_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '<img src="/static/RAE-removebg-preview.png"' in content:
                print("SUCCESS: HTML image tag correct.")
            else:
                print("FAILED: HTML image tag incorrect or missing.")
            
            if ".logo-image" in content and "@keyframes float" in content:
                print("SUCCESS: CSS found.")
            else:
                print("FAILED: CSS missing.")
    else:
        print(f"FAILED: {welcome_path} not found.")

if __name__ == "__main__":
    verify_image()
