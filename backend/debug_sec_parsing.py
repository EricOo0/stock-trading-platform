import os
import glob
import re

def inspect_file():
    # Find the file
    dl_path = os.path.join(os.getcwd(), "backend", "data", "temp_sec")
    search_path = os.path.join(dl_path, "sec-edgar-filings", "AAPL", "10-K", "*", "full-submission.txt")
    files = glob.glob(search_path)
    
    if not files:
        print("No file found!")
        return

    latest_file = max(files, key=os.path.getmtime)
    print(f"Inspecting: {latest_file}")
    print(f"File Size: {os.path.getsize(latest_file)} bytes")
    
    with open(latest_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Regex for documents
    # <DOCUMENT>
    # <TYPE>...
    # ...
    # <TEXT>...</TEXT>
    # </DOCUMENT>
    
    # Let's find all document types patterns
    # We look for <TYPE> value
    doc_matches = list(re.finditer(r'<TYPE>(.*?)\n', content, re.IGNORECASE))
    print(f"Found {len(doc_matches)} TYPE tags.")
    
    for i, m in enumerate(doc_matches):
        type_val = m.group(1).strip()
        start = m.start()
        # approximate length by looking ahead to next TYPE or end
        end = doc_matches[i+1].start() if i+1 < len(doc_matches) else len(content)
        length = end - start
        
        # Check for TEXT block size in this chunk?
        # A more robust way: Find <DOCUMENT> blocks
        print(f"Doc #{i}: TYPE='{type_val}', Approx Offset={start}")
        
    print("-" * 20)
    print("Testing extraction logic:")
    
    match = re.search(r'<TYPE>10-K.*?<TEXT>(.*?)</TEXT>', content, re.DOTALL | re.IGNORECASE)
    if match:
        extracted = match.group(1)
        print(f"Extracted Length: {len(extracted)} characters")
        print(f"Preview (Head): {extracted[:200]}")
        print(f"Preview (Tail): {extracted[-200:]}")
    else:
        print("Regex failed to match!")

if __name__ == "__main__":
    inspect_file()
