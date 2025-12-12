import os
import shutil
from sec_edgar_downloader import Downloader

def test_download():
    # Setup temporary text dir
    dl_dir = "temp_sec_dl"
    if os.path.exists(dl_dir):
        shutil.rmtree(dl_dir)
    os.makedirs(dl_dir)

    try:
        # User requested this specific lib
        # Needs email/agent
        dl = Downloader("StockTradingPlatform", "agent@example.com", dl_dir)
        
        print("Downloading AAPL 10-K...")
        # Get latest 1
        num_downloaded = dl.get("10-K", "AAPL", limit=1)
        print(f"Downloaded: {num_downloaded}")
        
        # Check file size
        # path is usually: temp_sec_dl/sec-edgar-filings/AAPL/10-K/{accession_number}/full-submission.txt (or .htm?)
        # sec_edgar_downloader downloads the full text submission or html.
        # Let's verify structure
        for root, dirs, files in os.walk(dl_dir):
            for file in files:
                path = os.path.join(root, file)
                size = os.path.getsize(path)
                print(f"File: {path}, Size: {size} bytes")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(dl_dir):
            shutil.rmtree(dl_dir)

if __name__ == "__main__":
    test_download()
