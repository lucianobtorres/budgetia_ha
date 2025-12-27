from PIL import Image
import os
import shutil

# Paths
SOURCE_IMAGE = r"C:/Users/lucia/.gemini/antigravity/brain/80b866fd-61b3-41b7-bff4-af1115bb2497/budgetia_icon_1766444166511.png"
DEST_DIR = r"C:\Users\lucia\Documents\Projetos\Python\BudgetIA\BudgetIA\pwa\public"

# Ensure destination exists
os.makedirs(DEST_DIR, exist_ok=True)

try:
    img = Image.open(SOURCE_IMAGE)
    
    # 1. pwa-192x192.png
    img_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    img_192.save(os.path.join(DEST_DIR, "pwa-192x192.png"))
    print("Saved pwa-192x192.png")

    # 2. pwa-512x512.png
    img_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    img_512.save(os.path.join(DEST_DIR, "pwa-512x512.png"))
    print("Saved pwa-512x512.png")

    # 3. apple-touch-icon.png (usually 180x180)
    img_180 = img.resize((180, 180), Image.Resampling.LANCZOS)
    img_180.save(os.path.join(DEST_DIR, "apple-touch-icon.png"))
    print("Saved apple-touch-icon.png")

    # 4. favicon.ico (multi-size)
    # create a list of resized images for the ico
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    img.save(os.path.join(DEST_DIR, "favicon.ico"), sizes=icon_sizes)
    print("Saved favicon.ico")
    
    print("All icons updated successfully.")

except Exception as e:
    print(f"Error processing images: {e}")
