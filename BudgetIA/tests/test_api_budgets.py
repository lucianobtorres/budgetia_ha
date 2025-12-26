import requests
import json
import pandas as pd
from src.config import NomesAbas, ColunasOrcamentos

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-User-Id": "jsmith"}

def test_api():
    print("Testing /budgets ...")
    try:
        r = requests.get(f"{BASE_URL}/budgets", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            print("Success!")
            if data:
                print("Sample item keys:", data[0].keys())
                print("First item:", data[0])
            else:
                print("Empty list returned.")
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

    print("\nTesting /dashboard/budgets ...")
    try:
        r = requests.get(f"{BASE_URL}/dashboard/budgets", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            print("Success!")
            if data:
                print("Sample item keys:", data[0].keys())
                print("First item:", data[0])
            else:
                print("Empty list returned.")
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_api()
