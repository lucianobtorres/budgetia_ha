from py_vapid import Vapid

# Generate VAPID keys
v = Vapid()
v.generate_keys()

private_key = v.private_key.decode('utf-8')
public_key = v.public_key.decode('utf-8')

print("VAPID Keys Generated Successfully!")
print("-" * 50)
print(f"VAPID_PRIVATE_KEY={private_key}")
print(f"VAPID_PUBLIC_KEY={public_key}")
print(f"VAPID_CLAIM_EMAIL=mailto:admin@budgetia.com")
print("-" * 50)
print("Copy these lines to your .env file.")
