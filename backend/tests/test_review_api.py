import requests
import json
import sys

def test_review_api():
    url = "http://localhost:8000/api/agent/review/analyze"
    payload = {
        "symbol": "AAPL",
        "user_id": "test_user_001"
    }
    
    print(f"Testing API: {url}")
    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: Status Code {response.status_code}")
                print(response.text)
                return

            print("Response Stream:")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(decoded_line)
                    try:
                        data = json.loads(decoded_line)
                        if data.get("type") == "agent_response":
                            # Just print a dot for progress to avoid spamming
                            sys.stdout.write(".") 
                            sys.stdout.flush()
                        elif data.get("type") == "error":
                            print(f"\nAPI Error: {data.get('content')}")
                    except:
                        pass
            print("\nStream finished.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_review_api()
