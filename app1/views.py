from django.shortcuts import render, redirect
from django.http import HttpResponse
from dashboard.views import dashboard
from google.cloud import storage
from firebase_admin import firestore, auth, credentials
from firebase_admin import auth
from .login import user_login

def index(request):
    return render(request, 'index.html')

def pricing(request):
    return render(request, 'pricing.html')

def forgot_password(request):
    return render(request, 'forgot_password.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        if not email or not password:
            return render(request, 'signup.html', {'error': 'Please fill in all fields.'})
        try:
            user = auth.create_user(email=email, password=password)
            # Get the user ID
            user_id = user.uid
            # ----- Get the Firestore document reference for the user settings ----- #
            db = firestore.client()
            user_settings_ref = db.collection('users').document(user_id)
            try:
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
            except firestore.NotFound:
                user_settings = {}
            # ---------------------------------------------------------------------- #

            # Prepare the data to be saved in Firestore
            firestore_data = {
                'ftue': True
            }

            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)

            # Your logic after successful user registration
            return redirect('login')  # Redirect to a success page
        
        except Exception as e:
            # Handle registration error with a user-friendly message
            error_message = 'An error occurred during registration. Please try again later.'
            if 'email' in str(e).lower():
                error_message = 'The provided email is already in use. Please use a different email.'
            return render(request, 'signup.html', {'error': error_message})
    else:
        return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = auth.get_user_by_email(email)
            # Sign in the user with the provided email and password
            id_token = user_login(email, password)
            # User login successful

            # Get the user ID
            user_id = user.uid

            request.session['user_id'] = user_id
            print(user_id)
            return redirect('dashboard')  # Redirect to the 'dashboard' view
        except Exception as e:
            # Handle other exceptions (if any)
            error_message = f'Error: Credentials Invalid.'
            print(error_message)
            return render(request, 'login.html', {'error': error_message})
    return render(request, 'login.html')






