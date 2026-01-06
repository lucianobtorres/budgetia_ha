import requests
import time
import statistics

BASE_URL = "http://127.0.0.1:8001"
USERNAME = "bench_user"
PASSWORD = "password123"

def benchmark(name, func, iterations=5):
    times = []
    print(f"\n--- Benchmarking {name} ---")
    for i in range(iterations):
        start = time.time()
        func()
        end = time.time()
        duration = end - start
        times.append(duration)
        print(f"Run {i+1}: {duration:.4f}s")
    
    avg = statistics.mean(times)
    print(f"Average: {avg:.4f}s")
    return avg

def login():
    payload = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]

def main():
    try:
        print("Authenticating...")
        token = login()
        headers = {"Authorization": f"Bearer {token}"}

        def get_summary():
            resp = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=headers)
            assert resp.status_code == 200, f"Dashboard Error: {resp.status_code} - {resp.text}"

        def get_transactions():
            resp = requests.get(f"{BASE_URL}/api/transactions?limit=50", headers=headers)
            assert resp.status_code == 200, f"Transactions Error: {resp.status_code} - {resp.text}"
        
        def get_budgets():
            resp = requests.get(f"{BASE_URL}/api/budgets/", headers=headers)
            assert resp.status_code == 200, f"Budgets Error: {resp.status_code} - {resp.text}"

        # Run Benchmarks
        benchmark("Dashboard Summary", get_summary, iterations=10)
        benchmark("Transactions List (50)", get_transactions, iterations=10)
        benchmark("Budgets List", get_budgets, iterations=10)

    except Exception as e:
        print(f"Benchmark failed: {e}")

if __name__ == "__main__":
    main()
