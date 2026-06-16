import requests

url = "https://infinite-weaver-api-1.onrender.com/api/generate"
payload = {"prompt": "A heroic test prompt for testing the database insert."}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
