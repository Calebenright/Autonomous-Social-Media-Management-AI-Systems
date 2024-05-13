import requests
from decouple import config
from firebase_admin import firestore, auth, credentials
import secrets
import string

API_KEY = config('FIREBASE_API_KEY')

def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
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
    db = firestore.client()
    user = None
    pid = None

    try:
        user = auth.get_user_by_email(email)
        doc_ref = db.collection('users').document(user.uid)
        doc = doc_ref.get()
        pid = doc.to_dict().get('admin_id', None)
        if pid is None or pid == "":
            raise ValueError("Account with this email already exists.")

    except auth.UserNotFoundError:
        pid = generate_password()
        user = auth.create_user(email=email, password=pid)
        doc_ref = db.collection('users').document(user.uid)
        doc_ref.set({'admin_id': pid}, merge=True)
        print('Created new user:', user.uid)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None, None

    try:
        id_token = user_login(email, pid)
        return id_token, pid, user.uid

    except Exception as e:
        print(f"Login error: {str(e)}")
        return None, pid, user.uid
    
def create_or_login_funnel(email):
    db = firestore.client()
    user = None
    pid = None

    try:
        user = auth.get_user_by_email(email)
        doc_ref = db.collection('users').document(user.uid)
        doc = doc_ref.get()
        pid = doc.to_dict().get('admin_id', None)
        isUser = True

    except auth.UserNotFoundError:
        pid = generate_password()
        user = auth.create_user(email=email, password=pid)
        doc_ref = db.collection('users').document(user.uid)
        doc_ref.set({'admin_id': pid}, merge=True)
        isUser = False

    except Exception as e:
        return None, None, None, None

    try:
        id_token = user_login(email, pid)
        return id_token, pid, user.uid, isUser

    except Exception as e:
        return None, None, None, None
    
def login_funnel(email):
    db = firestore.client()
    user = None
    pid = None

    try:
        user = auth.get_user_by_email(email)
        doc_ref = db.collection('users').document(user.uid)
        doc = doc_ref.get()
        pid = doc.to_dict().get('admin_id', None)

    except Exception as e:
        return None, None, None

    try:
        id_token = user_login(email, pid)
        return id_token, pid, user.uid

    except Exception as e:
        return None, None, None