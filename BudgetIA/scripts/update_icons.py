from PIL import Image
import os

# Paths
SOURCE_IMAGE = r"C:/Users/lucia/.gemini/antigravity/brain/80b866fd-61b3-41b7-bff4-af1115bb2497/budget_ia_neon_icon_1766527748399.png"
DEST_DIR = r"C:/Users/lucia/Documents/Projetos/Python/BudgetIA/BudgetIA/pwa/public"

# PWA Sizes
PWA_SIZES = [
    (192, 192, "pwa-192x192.png"),
    (512, 512, "pwa-512x512.png")
]

# Favicon Sizes
FAVICON_PNG_SIZES = [
    (16, 16, "favicon-16x16.png"),
    (32, 32, "favicon-32x32.png")
]

def update_icons():
    if not os.path.exists(SOURCE_IMAGE):
        print(f"Error: Source image not found at {SOURCE_IMAGE}")
        return

    try:
        with Image.open(SOURCE_IMAGE) as img:
            print(f"Opened source image: {img.size}")
            
            # Convert to RGBA just in case
            img = img.convert("RGBA")

            # 1. Generate PWA Icons
            for width, height, filename in PWA_SIZES:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                dest_path = os.path.join(DEST_DIR, filename)
                resized.save(dest_path, "PNG")
                print(f"Saved {filename} to {dest_path}")

            # 2. Generate Favicon PNGs
            for width, height, filename in FAVICON_PNG_SIZES:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                dest_path = os.path.join(DEST_DIR, filename)
                resized.save(dest_path, "PNG")
                print(f"Saved {filename} to {dest_path}")
            
            # 3. Generate favicon.ico (Multi-size)
            ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            ico_images = []
            for w, h in ico_sizes:
                ico_images.append(img.resize((w, h), Image.Resampling.LANCZOS))
            
            ico_path = os.path.join(DEST_DIR, "favicon.ico")
            # Save as ICO with all sizes
            ico_images[0].save(ico_path, format="ICO", sizes=ico_sizes, append_images=ico_images[1:])
            print(f"Saved favicon.ico (multi-size) to {ico_path}")

            print("All icons updated successfully!")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_icons()
