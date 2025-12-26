import base64
import re
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def update_constants():
    # 1. Get Key
    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    pub_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    print(f"Generated Key: {pub_b64} (Length: {len(pub_b64)})")

    # 2. Read constants.ts
    path = Path("pwa/src/utils/constants.ts")
    content = path.read_text(encoding="utf-8")

    # 3. Replace
    # Regex to find: export const VAPID_PUBLIC_KEY = ".*";
    new_line = f'export const VAPID_PUBLIC_KEY = "{pub_b64}";'
    
    content_new = re.sub(
        r'export const VAPID_PUBLIC_KEY = ".*";',
        new_line,
        content
    )
    
    # Validation
    if new_line not in content_new:
        print("Regex match failed. Appending instead.")
        content_new += f"\n{new_line}\n"

    # 4. Write
    path.write_text(content_new, encoding="utf-8")
    print("Updated constants.ts successfully!")

if __name__ == "__main__":
    update_constants()
