import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

# Load environment
load_dotenv("backend/.env")

def run_purge():
    print("Purging database...")
    try:
        from app.database import clear_all_empresas
        clear_all_empresas()
        print("Success.")
    except Exception as e:
        print(f"Error during purge: {e}")

if __name__ == "__main__":
    run_purge()
