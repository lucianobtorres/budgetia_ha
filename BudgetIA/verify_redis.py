
import os
import redis
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("UPSTASH_REDIS_URL")

if not redis_url:
    print("❌ UPSTASH_REDIS_URL not found in environment.")
    exit(1)

print(f"Testing connection to: {redis_url[:15]}...")

# Force SSL if needed
real_url = redis_url
if redis_url.startswith("redis://") and not redis_url.startswith("rediss://"):
     print("Attempting to force SSL (rediss://)...")
     real_url = redis_url.replace("redis://", "rediss://")

try:
    # Remove unexpected arg. If SSL verification fails, we'll see SSL error.
    client = redis.from_url(real_url, decode_responses=True)
    client.ping()
    print("✅ Connection successful!")
    
    # Test Write/Read
    client.set("budgetia:test_key", "Hello Redis!")
    val = client.get("budgetia:test_key")
    print(f"✅ Write/Read Verification: {val}")
    
    # Clean up
    client.delete("budgetia:test_key")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
