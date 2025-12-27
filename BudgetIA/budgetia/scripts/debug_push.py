import sys
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from application.services.push_notification_service import PushNotificationService

load_dotenv()

def debug_push():
    base_dir = Path("data/users")
    users = [d for d in base_dir.iterdir() if d.is_dir()]
    
    print(f"Scanning {len(users)} user directories...")
    
    found_subs = 0
    
    for user_dir in users:
        service = PushNotificationService(user_dir)
        subs = service._load_subscriptions()
        
        if subs:
            print(f"\n[+] Found {len(subs)} subscriptions for user: {user_dir.name}")
            for sub in subs:
                print(f"    - Endpoint: {sub['endpoint'][:40]}...")
                print(f"    - Device: {sub.get('device_name')}")
            
            print(f"    > Sending Test Push to {user_dir.name}...")
            count = service.send_notification(
                user_id=user_dir.name, 
                message="Teste de Debug do Backend! 🐍", 
                title="Debug BudgetIA"
            )
            print(f"    > Result: {count} sent.")
            found_subs += 1
            
    if found_subs == 0:
        print("\n[-] No subscriptions found in any user folder.")
        print("    Did you save the Profile ID correctly?")

if __name__ == "__main__":
    debug_push()
