from py_vapid import Vapid
import base64

v = Vapid.from_file("private_key.pem")
raw_private = v.private_key
# Encode to base64url for .env usage usually, or just keep it as is if library supports it.
# pywebpush accepts PEM file path or DER bytes.
# For .env, let's just print the Public Key again and tell user to point to the file or we extract the string.

# Actually, let's just use the library to get the b64
import json

# Try to get the raw numbers
private_val = v.private_key.private_numbers().private_value
# convert to bytes
private_bytes = private_val.to_bytes(32, byteorder='big')
private_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').strip('=')

public_raw = v.public_key.public_bytes(
    encoding=v.public_key._serialization.Encoding.X962,
    format=v.public_key._serialization.PublicFormat.UncompressedPoint
)
public_b64 = base64.urlsafe_b64encode(public_raw).decode('utf-8').strip('=')

print("-" * 50)
print(f"VAPID_PRIVATE_KEY={private_b64}")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print(f"VAPID_CLAIM_EMAIL=mailto:admin@budgetia.com")
print("-" * 50)
