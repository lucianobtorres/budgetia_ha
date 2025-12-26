import base64
import re
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def update_env():
    # 1. Get Key
    if not Path("private_key.pem").exists():
        print("Error: private_key.pem not found. Cannot update .env")
        return

    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    
    # Private Key B64
    private_val = private_key.private_numbers().private_value
    private_bytes = private_val.to_bytes(32, byteorder='big')
    priv_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')

    # Public Key B64
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    pub_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    # 2. Read .env
    path = Path(".env")
    if not path.exists():
        content = ""
    else:
        content = path.read_text(encoding="utf-8")

    # 3. Append or Update
    keys_to_add = {
        "VAPID_PRIVATE_KEY": priv_b64,
        "VAPID_PUBLIC_KEY": pub_b64,
        "VAPID_CLAIM_EMAIL": "mailto:admin@budgetia.com"
    }

    updated_content = content
    for key, val in keys_to_add.items():
        if key in updated_content:
            # Replace
            updated_content = re.sub(f'{key}=.*', f'{key}={val}', updated_content)
        else:
            # Append
            if not updated_content.endswith("\n") and updated_content:
                updated_content += "\n"
            updated_content += f'{key}={val}\n'

    # 4. Write
    path.write_text(updated_content, encoding="utf-8")
    print("Updated .env successfully!")

if __name__ == "__main__":
    update_env()
