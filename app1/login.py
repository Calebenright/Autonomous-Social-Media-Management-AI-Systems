import requests
from decouple import config
from firebase_admin import firestore, auth, credentials
import secrets
import string

API_KEY = config('FIREBASE_API_KEY')

def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits  # Use letters and digits only
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

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


def create_or_login_user(email, uid):
    try:
        user = auth.get_user_by_email(email)
        db = firestore.client()
        doc_ref = db.collection('users').document(user.uid)
        doc = doc_ref.get()
        name = doc.to_dict().get('name', None)
    except auth.UserNotFoundError:
        name = generate_password()
        user = auth.create_user(email=email, password=name)
        db = firestore.client()
        doc_ref = db.collection('users').document(user.uid)
        doc_ref.set({'name': name}, merge=True)
        print('Created new user:', user.uid)
    except Exception as e:
        print('Error fetching user data:', e)
        return None
    
    try:
        id_token = user_login(email, name)
        return id_token, name, user.uid
    except Exception as e:
        print(e)
        return None
