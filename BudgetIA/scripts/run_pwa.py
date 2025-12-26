import sys
import subprocess
from pathlib import Path

def main():
    """Runs the frontend development server using npm."""
    base_dir = Path(__file__).resolve().parent.parent
    pwa_dir = base_dir / "pwa"

    print(f"--- Starting BudgetIA Frontend (PWA) from {pwa_dir} ---")
    
    # Check if pwa dir exists
    if not pwa_dir.exists():
        print("Error: 'pwa' directory not found.")
        sys.exit(1)

    # Command to run
    # On Windows, npm is a batch file, so we need shell=True or fully qualified path.
    # shell=True is easiest.
    try:
        subprocess.run(["npm", "run", "dev"], cwd=str(pwa_dir), shell=True, check=True)
    except KeyboardInterrupt:
        print("\n--- Stopped Frontend ---")
    except subprocess.CalledProcessError as e:
        print(f"--- Frontend crashed with error code {e.returncode} ---")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
