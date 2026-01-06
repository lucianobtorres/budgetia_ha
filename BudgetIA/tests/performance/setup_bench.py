import sys
import os
import shutil

# Add src to path
sys.path.append(os.path.abspath("src"))

from interfaces.api.utils.security import create_user
from core.user_config_service import UserConfigService
from tests.criar_planilha_teste import main as generate_sheet

def setup():
    username = "bench_user"
    password = "password123"
    email = "bench@test.com"
    name = "Benchmarker"

    print(f"--- Setting up {username} ---")

    # 1. Create User
    try:
        create_user(username, name, email, password)
        print("User created/exists.")
    except Exception as e:
        print(f"User creation warning (might exist): {e}")

    # 2. Generate Excel
    sheet_filename = "bench_sheet.xlsx"
    # Run generator logic (reusing imported main, but hijacking filename if possible, or just rename)
    # The imported main uses global OUTPUT_FILE. Let's just run it and rename.
    generate_sheet()
    if os.path.exists("planilha_mestra.xlsx"):
        abs_path = os.path.abspath(sheet_filename)
        shutil.move("planilha_mestra.xlsx", abs_path)
        print(f"Spreadsheet generated at {abs_path}")
    else:
        raise Exception("Failed to generate spreadsheet")

    # 3. Configure User
    try:
        service = UserConfigService(username)
        service.save_planilha_path(abs_path)
        # Verify
        if service.is_configured():
            print("User configured successfully via UserConfigService.")
        else:
            print("Failed to configure user.")
    except Exception as e:
        print(f"Configuration failed: {e}")

if __name__ == "__main__":
    setup()
