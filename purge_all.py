import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def purge():
    print(f"Purging all companies at {BACKEND_URL}...")
    try:
        r = httpx.delete(f"{BACKEND_URL}/api/empresas/purge")
        r.raise_for_status()
        print("Successfully purged all companies.")
    except Exception as e:
        print(f"Failed to purge: {e}")

if __name__ == "__main__":
    purge()
