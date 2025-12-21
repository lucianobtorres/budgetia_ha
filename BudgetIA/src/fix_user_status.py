
import sys
import os

# Ensure src is in path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.user_config_service import UserConfigService

def fix():
    username = "jsmith"
    print(f"Fixing config for {username}...")
    try:
        svc = UserConfigService(username)
        cfg = svc.load_config()
        print("Current Config Keys:", list(cfg.keys()))
        print("Current Status:", cfg.get("onboarding_status"))
        
        cfg["onboarding_status"] = "COMPLETE"
        svc.save_config(cfg)
        print("SUCCESS: Updated onboarding_status to COMPLETE.")
        
        # Verify
        cfg_new = svc.load_config()
        print("Verified Status:", cfg_new.get("onboarding_status"))
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    fix()
