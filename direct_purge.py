from app.database import clear_all_empresas
import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

def run_purge():
    print("Executing hard purge via database logic...")
    try:
        clear_all_empresas()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_purge()
