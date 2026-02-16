import os

file_path = "frontend/pages/1_📊_Dashboard.py"

try:
    # Read as binary
    with open(file_path, "rb") as f:
        content_bytes = f.read()

    # Try to decode as UTF-8, replacing errors
    content_str = content_bytes.decode("utf-8", errors="replace")
    
    # If that looks weird (lots of replacement chars at the end), maybe try other common windows encodings for the appended part?
    # But for now, "replace" is safest to get a valid UTF-8 file back.
    
    # Write back as pure UTF-8
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content_str)
        
    print(f"Successfully fixed encoding for {file_path}")

except Exception as e:
    print(f"Error fixing encoding: {e}")
