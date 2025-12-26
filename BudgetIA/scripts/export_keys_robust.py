import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def get_keys():
    # Load Private Key
    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )

    # Get Public Key
    public_key = private_key.public_key()

    # Serialize Public Key to Uncompressed Point format (65 bytes)
    # This is what 'applicationServerKey' expects (header 0x04 + X + Y)
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Serialize Private Key to Big Integer bytes (32 bytes)
    private_val = private_key.private_numbers().private_value
    private_bytes = private_val.to_bytes(32, byteorder='big')

    # Convert to URL-Safe Base64 (strip padding)
    pub_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    priv_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')

    # print("-" * 60)
    print("KEY_PART_1:" + pub_b64[:43])
    print("KEY_PART_2:" + pub_b64[43:])
    # print(f"VAPID_PRIVATE_KEY={priv_b64}")
    # print("-" * 60)

if __name__ == "__main__":
    get_keys()
