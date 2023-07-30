from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UserSettingsForm
from .models import UserSettings
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
import os
from .post_creator import create_AI_post, create_stock_post
from .upload_post import send_post
from .generate_comment import generate_comment
from django.http import JsonResponse
import time
from .generate_unique_filename import generate_unique_filename
import firebase_admin
from firebase_admin import firestore, auth, credentials
import base64

def dashboard(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    try:
        # Get the user record from Firebase Authentication using the user_id
        user = auth.get_user(user_id)

        # Get the user's email address from the user record
        user_email = user.email
    except auth.AuthError as e:
        user_email = ''

    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except firestore.NotFound:
        user_settings = {}
    # ---------------------------------------------------------------------- #

    context = {
        'user_settings': user_settings,  # Pass the user_settings to the template
        'user_email': user_email
    }
    return render(request, 'dashboard.html', context)

def apps_calendar(request):
    return render(request, 'apps_calendar.html')

def comments(request):
    if request.method == 'POST':
        recent_comment = 'The colors are on point O.o that house build is awesome!'
        comment = generate_comment(recent_comment)
        return render(request, 'comments.html', {'comment': comment}) 
    return render(request, 'comments.html')


def post_creator(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except firestore.NotFound:
        user_settings = {}
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        user_folder_path = f'user_folders/{user_id}/images/'
        try:
            biz = user_settings['business_description']
        except (TypeError, KeyError):
            biz = 'mansion'
        post, url = create_AI_post(biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, user_folder_path)
        try:
            last_image_url = user_settings['next_image_url']
            last_caption = user_settings['next_caption']
        except (TypeError, KeyError):
            last_image_url = None
            last_caption = None
        next_image_url = url
        next_caption = post
    

        # Prepare the data to be saved in Firestore
        firestore_data = {
            'last_image_url': last_image_url,
            'last_caption': last_caption,
            'next_image_url': next_image_url,
            'next_caption': next_caption,
        }

        # Save the data to Firestore
        user_settings_ref.set(firestore_data, merge=True)
        return render(request, 'post_creator.html', {'post': post, 'image_url': url})
    
    context = {
        'user_settings': user_settings,
    }
    return render(request, 'post_creator.html', context)

def upload_post(request):
    if request.method == 'POST':
        user_settings = UserSettings.objects.get(user=request.user)
        image_url = user_settings.next_image_url
        caption = user_settings.next_caption

        # Call the function to post image to Instagram
        send_post(caption, image_url)
        return render(request, 'dashboard.html')

    return render(request, 'post_creator.html')


def brand_settings(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except firestore.NotFound:
        user_settings = {} 
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES)

        if form.is_valid():
            data = form.cleaned_data
            
            # Handle logo upload to GCP
            logo = request.FILES.get('logo')
            if logo:
                credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
                client = storage.Client(project=credentials.project_id, credentials=credentials)
                bucket = client.bucket(settings.GS_BUCKET_NAME)
                
                # Specify the user's folder path within the bucket
                user_folder_path = f'user_folders/{user_id}/logo/'  # Customize the folder structure as needed
                blob = bucket.blob(user_folder_path + 'logo.png')
                blob.upload_from_file(logo)
                blob.make_public()
                logo_url = blob.public_url
                # Assign the new user input value
            else:
                logo_url = user_settings.get('logo')

            # Prepare the data to be saved in Firestore
            firestore_data = {
                'business_description': data['business_description'],
                'brand_color': data['brand_color'],
                'temperature': data['temperature'],
                'logo': logo_url,
            }
            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)

            return redirect('brand_settings')  # Redirect to the brand settings page after saving settings

    context = {
        'user_settings': user_settings,  # Pass the user_settings to the template
    }
    return render(request, 'brand_settings.html', context)

def ad_manager(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except firestore.NotFound:
        user_settings = {}
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        user_folder_path = f'user_folders/{user_id}/images/'
        post, url = create_stock_post(user_settings.get('business_description'), settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, user_folder_path)
        ad_image_url = url
        ad_caption = post

        # Prepare the data to be saved in Firestore
        firestore_data = {
            'ad_image_url': ad_image_url,
            'ad_caption': ad_caption,
        }
        # Save the data to Firestore
        user_settings_ref.set(firestore_data, merge=True)
        # Update user_settings with the new values
        user_settings['ad_image_url'] = ad_image_url
        user_settings['ad_caption'] = ad_caption
    
    context = {
        'user_settings': user_settings,
    }
    return render(request, 'ad_manager.html', context)


