import requests

url = "http://127.0.0.1:8000/api/generate"
payload = {
    "prompt": "A story about Arthur, a knight in the medieval era whose armor is made of shattered glass. He seeks to protect the glass kingdom from the stone dragons.",
    "user_id": "test_multimodal_4",
    "world_bible": {},
    "interview_history": []
}

print("Sending request...")
response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")
try:
    print(response.json())
except:
    print(response.text)
