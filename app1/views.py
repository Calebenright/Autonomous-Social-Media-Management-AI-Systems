from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.mail import EmailMessage
from dashboard.views import dashboard
from google.cloud import storage
from firebase_admin import firestore, auth, credentials
from .login import user_login, create_or_login_user
from decouple import config
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import requests
import google.oauth2.id_token
import google.auth.transport.requests
from urllib.parse import urlencode, quote_plus
    
def index(request):
    return render(request, 'index.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def pricing(request):
    return render(request, 'pricing.html')

def terms_of_service(request):
    return render(request, 'terms_of_service.html')

def get_articles(request):
    cached_articles = cache.get('cached_articles_list')
    if cached_articles is None:
        try:
            db = firestore.client()
            articles_ref = db.collection('articles').order_by('publishedDate', direction=firestore.Query.DESCENDING).limit(36)
            docs = articles_ref.stream()
            cached_articles = [doc.to_dict() for doc in docs]
            cache.set('cached_articles_list', cached_articles, 600)
        except Exception as e:
            print(f"An error occurred: {e}")
            cached_articles = []
    return render(request, 'article_list.html', {'articles': cached_articles})

def article_detail(request, article_slug):
    cache_key = f'article_detail_{article_slug}'
    cached_article = cache.get(cache_key)
    if cached_article is None:
        try:
            db = firestore.client()
            # Assuming each article has a 'slug' field
            article_ref = db.collection('articles').where('slug', '==', article_slug).limit(1)
            docs = article_ref.stream()
            article = next(docs, None)
            if article:
                cached_article = article.to_dict()
                cache.set(cache_key, cached_article, 600)
            else:
                cached_article = {'error': 'Article not found'}
        except Exception as e:
            print(f"An error occurred fetching article {article_slug}: {e}")
            cached_article = {'error': 'Failed to fetch the article.'}
    return render(request, 'articles/article_details.html', {'article': cached_article})

def graphic_builder(request):
    return render(request, 'graphic_builder.html')

def forgot_password(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            user = auth.get_user_by_email(email)
            link = auth.generate_password_reset_link(email)
            subject = 'Reset Your Feadl.io Password'
            message = (
                f"<p>Hello, {user}</p>"
                f"<p>Follow this link to reset your password for your {email} account.</p>"
                f"<p><a href='{link}'>{link}</a></p>"
                "<p>If you didn’t ask to reset your password, you can ignore this email.</p>"
                "<p>Thanks,</p>"
                "<p>Your Feadl.io team</p>"
            )
            from_email = config("EMAIL_HOST_USER")
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

                from_email = config("EMAIL_HOST_USER")
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
        from_email = config("EMAIL_HOST_USER")
        recipient_list = [config("INTERNAL_RECIPIENTS")]

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

    user_id = request.session.get('user_id', None)
    email = request.session.get('user_email', None)
    user_pid = request.session.get('user_pid', None)
    isProvider = request.session.get('isProvider', False)

    if request.method == 'POST':
        email = request.POST.get('email')
        user_pid = request.POST.get('password')
        # try:
        id_token = user_login(email, user_pid)
        decoded_token = auth.verify_id_token(id_token)

        user_id = decoded_token['uid']
            
        request.session['firebase_id_token'] = id_token
        request.session['user_id'] = user_id
        request.session['user_email'] = email
        request.session['isProvider'] = False

        db = firestore.client()
        
        master_ref = db.collection('variables').document('master')
        master_doc = master_ref.get()

        master_settings = master_doc.to_dict()
        if user_id == master_settings['id']:
            request.session['master'] = True
            
        return redirect('dashboard') 
        # except Exception as e:
        #     messages.error(request, 'Credentials Invalid.')
        #     return redirect('login')
        
    return render(request, 'login.html', {'user_pid': user_pid, 'user_email': email, 'isProvider': isProvider})

def google_sign_in(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    redirect_uri = "https://feadl.io/google_auth_callback/"
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=825164430085-rtg5t1aus37nri37bo3ok3hf0hgjofdo.apps.googleusercontent.com&redirect_uri={redirect_uri}&scope={scope}"
    return HttpResponseRedirect(auth_url)

@csrf_exempt
def google_auth_callback(request):
    try:
        google_auth_code = request.GET.get('code')
        redirect_uri = "https://feadl.io/google_auth_callback/"
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': google_auth_code,
            'client_id': '825164430085-rtg5t1aus37nri37bo3ok3hf0hgjofdo.apps.googleusercontent.com',
            'client_secret': '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',
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        token_response = requests.post(token_url, data=token_data)
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        userinfo_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', params={'access_token': access_token})
        user_info = userinfo_response.json()
        email = user_info.get('email')
        gid = user_info.get('id')

        id_token, name, user_id = create_or_login_user(email, gid)

        request.session['user_id'] = user_id
        request.session['user_email'] = email
        request.session['user_pid'] = name
        request.session['isProvider'] = True

        return redirect('login')
 
    except Exception as e:
        messages.error(request, f'Credentials Invalid. {e}')
        return redirect('login')

def facebook_sign_in(request):
    
    facebook_auth_url = "https://www.facebook.com/v17.0/dialog/oauth?"
    client_id = "216745084667486"
    redirect_uri = "https://feadl.io/facebook_auth_callback/"
    scope = "email"
    state = "105"

    auth_url = f"{facebook_auth_url}client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&response_type=code"
    
    return HttpResponseRedirect(auth_url)

@csrf_exempt
def facebook_auth_callback(request):
    try:
        code = request.GET.get('code')
        redirect_uri = "https://feadl.io/facebook_auth_callback/"
        client_id = "216745084667486"
        client_secret = "d96b709e954bb40082e95bc9fef4281b"
        
        token_url = "https://graph.facebook.com/v17.0/oauth/access_token"
        token_params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'client_secret': client_secret,
            'code': code
        }
        
        token_response = requests.get(token_url, params=token_params)
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Use the access token to fetch the user's profile information
        userinfo_response = requests.get('https://graph.facebook.com/me', params={'fields': 'id,name,email', 'access_token': access_token})
        user_info = userinfo_response.json()
        email = user_info.get('email')
        fid = user_info.get('id')

        id_token, name, user_id = create_or_login_user(email, fid)

        request.session['user_id'] = user_id
        request.session['user_email'] = email
        request.session['user_pid'] = name
        request.session['isProvider'] = True
        
        return redirect('login')

    except Exception as e:
        messages.error(request, f'Credentials Invalid. {e}')
        return redirect('login')
    
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /login/",
        "Disallow: /signup/",
        "Disallow: /ad_manager/",
        "Disallow: /brand_settings/",
        "Disallow: /contact/",
        "Disallow: /graphic_builder/",
        "Disallow: /forgot_password/",
        "Disallow: /change_email/",
        "Disallow: /calendar/",
        "Disallow: /checkout/",
        "Disallow: /library/",
        "Disallow: /post_creator/",
        "Disallow: /dashboard/",
        "Disallow: /page_selection_popup/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

@csrf_exempt
def iframe_content(request):
    response = HttpResponse()
    response['Access-Control-Allow-Origin'] = 'https://feadl.io'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def update_is_provider(request):
    request.session['isProvider'] = False
    print(request.session['isProvider'])
    return JsonResponse({"success": True})