from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import EmailMessage
from dashboard.views import dashboard
from google.cloud import storage
from firebase_admin import firestore, auth, credentials
from .login import user_login
from decouple import config
from django.conf import settings

def index(request):
    return render(request, 'index.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms_of_service.html')

def graphic_builder(request):
    return render(request, 'graphic_builder.html')

def forgot_password(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            user = auth.get_user_by_email(email)
            link = auth.generate_password_reset_link(email)
            print(link)

            subject = 'Reset Your Feadl.io Password'
            message = (
                f"<p>Hello, {user}</p>"
                f"<p>Follow this link to reset your password for your {email} account.</p>"
                f"<p><a href='{link}'>{link}</a></p>"
                "<p>If you didn’t ask to reset your password, you can ignore this email.</p>"
                "<p>Thanks,</p>"
                "<p>Your Feadl.io team</p>"
            )
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [request.POST.get('email')] 

            email = EmailMessage(subject, message, from_email, recipient_list)
            email.content_subtype = "html"
            email.send() 
            return render(request, 'login.html', {'success': "Password reset email sent. Check your inbox."})
        except auth.UserNotFoundError:
            return render(request, 'forgot_password.html', {'error': "That email is not associated with an account."})

    return render(request, 'forgot_password.html')

def change_email(request):
    if request.method == 'POST':
        new_email = request.POST.get('new_email')
        confirm_new_email = request.POST.get('confirm_email')
        if new_email == confirm_new_email:
            try:
                new_email = request.POST.get('new_email')
                old_email = request.POST.get('old_email')
                user = auth.get_user_by_email(old_email)
                auth.update_user(user.uid, email=new_email)

                # ----- Get the Firestore document reference for the user settings ----- #
                db = firestore.client()
                user_settings_ref = db.collection('users').document(user.uid)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                # ---------------------------------------------------------------------- #
                firestore_data = {'email': new_email}
                user_settings_ref.set(firestore_data, merge=True)

                subject = 'Email Address Changed'
                message = (
                    f"<p>Hello,</p>"
                    f"<p>Your email address has been successfully changed to {new_email}.</p>"
                    "<p>If you didn’t request this change, please contact support.</p>"
                    "<p>Thanks,</p>"
                    "<p>Your Feadl.io team</p>"
                )

                from_email = settings.EMAIL_HOST_USER
                recipient_list = [new_email]

                email = EmailMessage(subject, message, from_email, recipient_list)
                email.content_subtype = "html"
                email.send() 
                return redirect('brand_settings')
            except auth.UserNotFoundError:
                return render(request, 'change_email.html', {'error': "User not found."})
        else:
            error = "New email and confirm email do not match."
            return render(request, 'change_email.html', {'error': error})
    return render(request, 'change_email.html')

def contact(request):
    if request.method == 'POST':
        subject = 'Feadl.io Contact Form Submission'
        message = 'Name: {}\nEmail: {}\nMessage: {}'.format(
            request.POST.get('name'),
            request.POST.get('email'),
            request.POST.get('message')
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [settings.INTERNAL_RECIPIENTS]

        email = EmailMessage(subject, message, from_email, recipient_list)

        try:
            email.send() 
            return render(request, 'contact.html', {'success': "You're email was sent! We will get back with you shortly."})
        except Exception as e:
            return render(request, 'contact.html', {'error': "There was an error sending your email. Please wait a moment and try again."})

    return render(request, 'contact.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        confirm_email = request.POST['confirm_email']
        password = request.POST['password']
        if confirm_email == email:
            try:
                user = auth.create_user(email=email, password=password)
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

                firestore_data = {
                    'ftue': True,
                    'autoState': 1,
                    'isSubscriber': False,
                    'isLogo': False,
                    'brand_color': '#000000',
                    'business_description': '',
                    'business_name': '',
                    'secondary_colors': "['#000000', '#000000', '#000000', '#000000']",
                    'images_generated': 0,
                    'progress': 100,
                    'admin': False,
                    'isBusiness': False,
                    'email': email
                }
                user_settings_ref.set(firestore_data, merge=True)
                messages.success(request, f'Account created. You can now log in.')
                return redirect('login')
            
            except Exception as e:
                error_message = 'An error occurred during registration. Please try again later.'
                if 'email' in str(e).lower():
                    error_message = 'The provided email is already in use. Please use a different email.'
                return render(request, 'signup.html', {'error': error_message})
        else:
            return render(request, 'signup.html', {'error': 'Emails must match. Please make sure the emails you entered are the same.'})
    else:
        return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            id_token = user_login(email, password)
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            request.session['firebase_id_token'] = id_token
            request.session['user_id'] = user_id
            db = firestore.client()
            master_ref = db.collection('variables').document('master')
            master_doc = master_ref.get()
            master_settings = master_doc.to_dict()
            if user_id == master_settings['id']:
                print('Master')
                request.session['master'] = True
            return redirect('dashboard') 
        except Exception as e:
            messages.error(request, 'Credentials Invalid.')
            return redirect('login')
    return render(request, 'login.html')






