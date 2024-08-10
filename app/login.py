import requests
from decouple import config

API_KEY = config('FIREBASE_API_KEY')

def user_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    if "idToken" in response_data:
        return response_data["idToken"]
    else:
        error_message = response_data["error"]["message"]
        raise Exception(f"Sign-in failed: {error_message}")
