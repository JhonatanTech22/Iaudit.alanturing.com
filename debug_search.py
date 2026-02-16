import httpx
import json

def test_search(cnpj):
    url = f"http://localhost:8000/api/query/cnpj/{cnpj}"
    print(f"Searching CNPJ: {cnpj} via {url}")
    try:
        with httpx.Client(timeout=120) as client:
            resp = client.get(url)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("Success! Data received:")
                print(json.dumps(resp.json(), indent=2, ensure_ascii=False)[:1000] + "...")
            else:
                print("Error Details:")
                print(resp.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Using a known valid CNPJ from previous logs
    test_search("09157307000175")
