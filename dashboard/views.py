from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UserSettingsForm
from .models import UserSettings
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
import os
from .post_creator import create_image, create_stock_post, create_call_to_action, create_caption, create_dalle_post, create_stable_dif_post, create_ad_copy, create_ad
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
    ads_folder_path = f'user_folders/{user_id}/ads/'
    try:
        biz = user_settings['business_description']
    except (TypeError, KeyError):
        biz = 'mansion'
    try:
        logo_path = user_settings['logo']
    except (TypeError, KeyError):
        logo_path = None
    try:
        num_ad = int(user_settings['num_ad'])
    except (TypeError, KeyError):
        num_ad = 1
    try:
        current_ad_image_url = user_settings['current_ad_image']
    except (TypeError, KeyError):
        current_ad_image_url = None
    try:
        current_ad_copy = user_settings['current_ad_copy']
    except (TypeError, KeyError):
        current_ad_copy = None
    try:
        ad_image_url = user_settings['ad_image_url']
    except (TypeError, KeyError):
        ad_image_url = None
    try:
        ad_copy = user_settings['ad_copy']
    except (TypeError, KeyError):
        ad_copy = None

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if num_ad < 5 :
            if form_name == 'formCopy':
                ad_copy = create_ad_copy(biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path)
            elif form_name == 'formCopySave':
                ad_copy = request.POST.get('ad_copy_content')
            elif form_name == 'formRunAd':
                current_ad_image_url = ad_image_url
                current_ad_copy = ad_copy
            elif form_name == 'formImg':
                isLogo = request.POST.get('isLogo', 'false')
                request.session['isLogo'] = isLogo
                ad_image_url = create_ad(isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path, num_ad)
                if num_ad <= 5:
                    num_ad += 1
                    
            else:
                isLogo = request.POST.get('isLogo', False)
                request.session['isLogo'] = isLogo
                ad_copy = create_ad_copy(biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path)
                ad_image_url = create_ad(isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path, num_ad)
                if num_ad <= 5:
                    num_ad += 1
                # if num_ad >= 5:
                #     num_ad = 1
                # else:
                #     num_ad += 1

            # Prepare the data to be saved in Firestore
            firestore_data = {
                'ad_image_url': ad_image_url,
                'ad_copy': ad_copy,
                'num_ad': num_ad,
                'current_ad_copy': current_ad_copy,
                'current_ad_image_url': current_ad_image_url
            }

            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)

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

        else:
            user_settings['deny'] = True
        
    isLogo = request.session.get('isLogo', 'false')
    context = {
        'user_settings': user_settings,
        'isLogo': isLogo,
    }
    return render(request, 'ad_manager.html', context)

def post_creator(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    
    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except firestore.NotFound:
        return render(request, 'post_creator.html', {"Error": error})
    # ---------------------------------------------------------------------- #
    image_folder_path = f'user_folders/{user_id}/images/'
    try:
        biz = user_settings['business_description']
    except (TypeError, KeyError):
        biz = 'mansion'
    try:
        color = user_settings['brand_color']
    except (TypeError, KeyError):
        color = '#AAAAAA'
    try:
        website = user_settings['website']
    except (TypeError, KeyError):
        website = ''
    try:
        logo_path = user_settings['logo']
    except (TypeError, KeyError):
        logo_path = None
    try:
        num_post = int(user_settings['num_post'])
    except (TypeError, KeyError):
        num_post = 1
    try:
        num_schedule = int(user_settings['num_schedule'])
    except (TypeError, KeyError):
        num_schedule = 1

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if num_post < 10:
    # ------------------- Get Selected Post Type --------------------------- #
            selected_option = request.POST.get('flexRadioDefault')
            request.session['selected_radio'] = selected_option
            print(selected_option)
            isLogo = request.POST.get('isLogo', 'false')
            request.session['isLogo'] = isLogo
    # ---------------------------------------------------------------------- #
            if form_name == 'formImage1':
                selected_option = request.session.get('selected_radio', None)
                isLogo = request.session.get('isLogo', None)
                url = create_image(website, color, selected_option, isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, num_post)
                post = user_settings['next_caption']
                if num_post >= 10:
                    num_post = 1
                else:
                    num_post += 1
                firestore_data = {'next_image_url': url, 'num_post': num_post}
                
            elif form_name == 'formCaption1':
                selected_option = request.session.get('selected_radio', None)
                isLogo = request.session.get('isLogo', 'false')
                post = create_caption(biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                firestore_data = {'next_caption': post}
                url = user_settings['next_image_url']
            
            elif form_name == 'formPostSchedule':
                next_image_url = user_settings['next_image_url']
                post = user_settings['next_caption']
                url = user_settings['next_image_url']
                firestore_data = {
                    'schedule_img_' + str(num_schedule): next_image_url,
                    'schedule_cap_' + str(num_schedule): post,
                    'next_caption': post,
                    'num_schedule': num_schedule
                }

            else:
                try:
                    last_image_url = user_settings['next_image_url']
                    last_caption = user_settings['next_caption']
                except (TypeError, KeyError):
                    last_image_url = None
                    last_caption = None
                url = create_image(website, color, selected_option, isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, num_post)
                post = create_caption(biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)

                if num_post >= 10:
                    num_post = 1
                else:
                    num_post += 1
                    
                if num_schedule >= 8:
                    num_schedule = 1
                else:
                    num_schedule += 1

                firestore_data = {
                    'last_image_url': last_image_url,
                    'last_caption': last_caption,
                    'next_image_url': url,
                    'next_caption': post,
                    'num_post': num_post,
                    'num_schedule': num_schedule
                }

            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)
            return render(request, 'post_creator.html', {'post': post, 'image_url': url, 'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings})
        else:
            user_settings['deny'] = True
    context = {
        'user_settings': user_settings,
    }
    return render(request, 'post_creator.html', context)

def upload_post(request):
    return render(request, 'dashboard.html')

def schedule(request):
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
        form_name = request.POST.get('form')
        try:
            schedule_ad = int(user_settings['schedule_ad'])
        except (TypeError, KeyError):
            schedule_ad = 1

    context = {
        'user_settings': user_settings,
    }
    return render(request, 'schedule.html', context)

def comments(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except Exception as e:
        user_settings = {}
    
    # ---------------------------------------------------------------------- #
    if request.method == 'POST':
        recent_comment = 'The colors are on point O.o that house build is awesome!'
        comment = generate_comment(recent_comment)
        return render(request, 'comments.html', {'comment': comment, 'user_settings': user_settings}) 
    context = {
        'user_settings': user_settings,  
    }
    return render(request, 'comments.html', context)

def brand_settings(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    db = firestore.client()
    user_id = request.session.get('user_id')
    user_settings_ref = db.collection('users').document(user_id)
    try:
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    except Exception as e:
        user_settings = {}
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        logo = request.FILES.get('logo')
        if logo:
            try:
                num_logo = int(user_settings['num_logo'])
            except (TypeError, KeyError):
                num_logo = 1
            credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
            client = storage.Client(project=credentials.project_id, credentials=credentials)
            bucket = client.bucket(settings.GS_BUCKET_NAME)
            
            # Specify the user's folder path within the bucket
            logo_folder_path = f'user_folders/{user_id}/logo/'  
            blob = bucket.blob(logo_folder_path + 'logo' + str(num_logo) + '.png')
            blob.upload_from_file(logo)
            blob.make_public()
            logo_url = blob.public_url
            if num_logo >= 2:
                num_logo = 1
            else:
                num_logo += 1
        else:
            try:
                logo_url = user_settings['logo']
            except (TypeError, KeyError):
                logo_url = None

        pfp = request.FILES.get('pfp')
        if pfp:
            try:
                num_pfp = int(user_settings['num_pfp'])
            except (TypeError, KeyError):
                num_pfp = 1
            credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
            client = storage.Client(project=credentials.project_id, credentials=credentials)
            bucket = client.bucket(settings.GS_BUCKET_NAME)
            
            # Specify the user's folder path within the bucket
            pfp_folder_path = f'user_folders/{user_id}/pfp/' 
            blob = bucket.blob(pfp_folder_path + 'pfp' + str(num_pfp) + '.jpg')
            blob.upload_from_file(pfp)
            blob.make_public()
            pfp_url = blob.public_url
            if num_pfp >= 2:
                num_pfp = 1
            else:
                num_pfp += 1
        else:
            try:
                pfp_url = user_settings['pfp']
            except (TypeError, KeyError):
                pfp_url = ''

        # Prepare the data to be saved in Firestore
        firestore_data = {
            'business_name': request.POST.get('business_name'),
            'business_description': request.POST.get('business_description'),
            'brand_color': request.POST.get('brand_color'),
            'temperature': request.POST.get('temperature'),
            'website': request.POST.get('website'),
            'logo': logo_url,
            'pfp': pfp_url
        }
        # Save the data to Firestore
        user_settings_ref.set(firestore_data, merge=True)

        return redirect('brand_settings')  # Redirect to the brand settings page after saving settings

    context = {
        'user_settings': user_settings,  # Pass the user_settings to the template
    }
    return render(request, 'brand_settings.html', context)

def error(request):
    return render(request, 'error.html', status=500)

