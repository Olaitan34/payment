import requests

BASE_URL = "https://payment-production-6ded.up.railway.app"

# Endpoints you want to test
endpoints = [
    "/api/v1/payments/",
    "/api/v1/payments/1/",
    "/admin/login/",
]

for endpoint in endpoints:
    url = BASE_URL + endpoint
    try:
        print(f"Testing {url} ...")
        response = requests.get(url, timeout=10)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.text[:200], "...")  # print only first 200 chars
        else:
            print("Error:", response.text[:200], "...")
    except Exception as e:
        print(f"Failed to reach {url}: {e}")

print("✅ Test complete")