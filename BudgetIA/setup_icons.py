from PIL import Image
import os
import shutil

SOURCE_PATH = r"C:\Users\lucia\.gemini\antigravity\brain\28951d61-049a-49dd-b6d6-c13366f10980\budgetia_app_icon_1766112562474.png"
DEST_DIR = r"c:\Users\lucia\Documents\Projetos\Python\BudgetIA\BudgetIA\pwa\public"

def main():
    if not os.path.exists(SOURCE_PATH):
        print(f"Error: Source image not found at {SOURCE_PATH}")
        return

    img = Image.open(SOURCE_PATH)
    
    # Save 192x192
    img.resize((192, 192)).save(os.path.join(DEST_DIR, "pwa-192x192.png"))
    print("Saved pwa-192x192.png")

    # Save 512x512
    img.resize((512, 512)).save(os.path.join(DEST_DIR, "pwa-512x512.png"))
    print("Saved pwa-512x512.png")

    # Save favicon (64x64 or 32x32)
    img.resize((64, 64)).save(os.path.join(DEST_DIR, "favicon.ico"), format='ICO')
    print("Saved favicon.ico")

if __name__ == "__main__":
    main()
