from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UserSettingsForm
from .models import UserSettings
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud.firestore_v1.base_query import FieldFilter
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport import requests
import os
from .post_creator import create_image, create_stock_post, create_call_to_action, create_caption, create_dalle_post, create_stable_dif_post, create_ad_copy, create_ad, create_placeholder, add_text
from .upload_post import send_post
from django.http import JsonResponse
import time
from .functions import generate_unique_filename, generate_random_date
from .brand_settings import create_tags
from firebase_admin import firestore, auth, credentials
import base64
import ast
import json
from .tasks import enqueue_task
from datetime import datetime, timedelta
import uuid
import random
import requests
from decouple import config
import stripe
import secrets
import pytz

# stripe.api_key = settings.STRIPE_SECRET_KEY
# endpoint_secret = 'whsec_ZS4zkRNL4aZ9Kumreb6D6ygrb3eHS8p9'
stripe.api_key = 'sk_test_51N3DeEAy1fGRWtyhPPQQR7NXm6N0kvTGbQ3XhxT4GB574akDF8ki3OPo9zhqSWYvZNMWhPvrGbbMeVkLPjQWi4Ga0027FmfJpA'
endpoint_secret = 'whsec_359fc53bbb46857ff7bbca0a01c1c56c36f795da8f7cf4717bb46e53a78f368a'

def dashboard(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user = auth.get_user(user_id)
            user_email = user.email
        except auth.AuthError as e:
            user_email = ''

        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            
        except firestore.NotFound:
            user_settings = {}
        # ---------------------------------------------------------------------- #
        pass
    
    except AttributeError as e:
        if "AuthError" in str(e):
            return redirect('login')
    
        return render(request, 'error.html', {'error_message': 'Please Try Logging in Again.'})
    
    
    try:
        ftue = user_settings['ftue']
    except (TypeError, KeyError):
        return render(request, 'error.html', {'error_message': 'Please Try Logging in Again.'})
    try:
        endFtue = user_settings['endFtue']
    except (TypeError, KeyError):
        endFtue = False
    try:
        website = user_settings['business_description']
    except (TypeError, KeyError):
        website = ''

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'formFtue':
            if ftue:
                # Prepare the data to be saved in Firestore
                firestore_data = {
                    'ftue': False,
                    'ftue2': True,
                    'ftue3': False,
                    'ftue4': False,
                    'endFtue': False
                }
            
            else:
                ftue2 = user_settings['ftue2']
                ftue3 = user_settings['ftue3']
                ftue4 = user_settings['ftue4']
                if ftue2:
                    # Prepare the data to be saved in Firestore
                    firestore_data = {
                        'ftue2': False,
                        'ftue3': True
                    }
                elif ftue3:
                    business_name = request.POST.get('business_name')
                    business_description = request.POST.get('business_description')
                    brand_color = request.POST.get('brand_color')
                    tags = create_tags(business_description)

                    # Prepare the data to be saved in Firestore
                    firestore_data = {
                        'ftue3': False,
                        'ftue4': True,
                        'tags': tags,
                        'business_description': business_description,
                        'business_name': business_name,
                        'brand_color': brand_color
                    }
                elif ftue4:
                    link = request.POST.get('link')

                    # Prepare the data to be saved in Firestore
                    firestore_data = {
                        'ftue4': False,
                        'endFtue': True,
                        'autoState': 1
                    }
                    user_settings_ref.set(firestore_data, merge=True)
                    return redirect(link)
                
        elif form_name == 'formAutomate':
            if user_settings['isSubscriber']:
                if 'total_allowed_images' in user_settings and 'images_generated' in user_settings and 'cooldown_expiry' in user_settings:
                    total_allowed_images = user_settings['total_allowed_images']
                    images_generated = user_settings['images_generated']
                    cooldown_expiry = user_settings['cooldown_expiry']
                else:
                    total_allowed_images = 10
                    images_generated = 0
                    cooldown_duration = timedelta(days=1)
                    cooldown_expiry = datetime.now() + cooldown_duration
                    user_settings_ref.update({
                        'cooldown_expiry': cooldown_expiry,
                        'images_generated': images_generated,
                        'total_allowed_images': total_allowed_images
                    })

                tz = pytz.UTC
                current_time = datetime.now(tz)

                if current_time > cooldown_expiry:
                    images_generated = 0
                    user_settings_ref.update({
                        'images_generated': images_generated
                    })
                    print('images generated reset')

                if images_generated < total_allowed_images:
                    images_generated = images_generated + 2
                    user_settings_ref.update({
                        'images_generated': images_generated,
                    })

                    if images_generated >= total_allowed_images:
                        cooldown_duration = timedelta(days=1)
                        cooldown_expiry = datetime.now() + cooldown_duration

                    image_folder_path = f'user_folders/{user_id}/images/'
                    tags = user_settings['tags']
                    key = user_settings['business_description']
                    biz_name = user_settings['business_name']
                    color = user_settings['brand_color']
                    selected_option = 'cta'
                    isLogo = False
                    logo_path = ''
                    post_num1 = random.randint(1, 4)
                    post_num2 = random.randint(1, 4)
                    payload = {
                        'user_id': user_id
                    }

                    enqueue_task(payload)

                    schedule_img_7 = create_image(website, color, selected_option, isLogo, logo_path, key, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, post_num1)
                    schedule_img_8 = create_image(website, color, selected_option, isLogo, logo_path, key, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, post_num2)

                    firestore_data = {
                        'status': '10',
                        'autoState': 2,
                        'schedule_image_7': schedule_img_7,
                        'schedule_image_8': schedule_img_8,
                        'post_num1': post_num1,
                        'post_num2': post_num2,
                        'cooldown_expiry': cooldown_expiry,
                        'images_generated': images_generated
                    }
                        
                    user_settings_ref.set(firestore_data, merge=True)
                    user_settings_doc = user_settings_ref.get()
                    user_settings = user_settings_doc.to_dict()
                else:
                    user_settings_strings = {
                        key: value.isoformat() if isinstance(value, datetime) else value
                        for key, value in user_settings.items()
                    }
                    context = {
                        'user_settings_json': json.dumps(user_settings_strings),
                        'user_settings': user_settings,
                        'user_id' : user_id,
                        'error': 'Our generators need to cooldown. You can check the status of them in the settings tab.'
                    }
                    return render(request, 'dashboard.html', context)

                user_settings_strings = {
                    key: value.isoformat() if isinstance(value, datetime) else value
                    for key, value in user_settings.items()
                }
                context = {
                    'user_settings_json': json.dumps(user_settings_strings),
                    'user_settings': user_settings,
                    'user_id' : user_id
                }
                return render(request, 'dashboard.html', context)
            else:
                user_settings_strings = {
                    key: value.isoformat() if isinstance(value, datetime) else value
                    for key, value in user_settings.items()
                }
                context = {
                    'user_settings_json': json.dumps(user_settings_strings),
                    'user_settings': user_settings,
                    'user_id': user_id,
                    'error': 'No Subscription'
                }
                return render(request, 'dashboard.html', context)
        
        elif form_name == 'formView':
            image_folder_path = f'user_folders/{user_id}/images/'
            tags = user_settings['tags']
            key = user_settings['business_description']
            biz_name = user_settings['business_name']
            color = user_settings['brand_color']
            post_num1 = user_settings['post_num1']
            post_num2 = user_settings['post_num2']
            selected_option = 'text'
            isLogo = False
            schedule_img_7 = create_image(website, color, selected_option, isLogo, user_settings['schedule_image_7'], key, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, post_num1)
            schedule_img_8 = create_image(website, color, selected_option, isLogo, user_settings['schedule_image_8'], key, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, post_num2)

            firestore_data = {
                'schedule_image_7': schedule_img_7,
                'schedule_image_8': schedule_img_8,
                'autoState': 3
            }
                
            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            user_settings_strings = {
                key: value.isoformat() if isinstance(value, datetime) else value
                for key, value in user_settings.items()
            }
            context = {
                'user_settings_json': json.dumps(user_settings_strings),
                'user_settings': user_settings,
                'user_id': user_id
            }
            return render(request, 'dashboard.html', context)
        
        elif form_name == 'formSchedule':
            checkboxes = [
                'ftueCheck',
                'ftueCheck2',
                'ftueCheck3',
                'ftueCheck4',
                'ftueCheck5',
                'ftueCheck6',
                'ftueCheck7',
                'ftueCheck8'
            ]
            timestamps = [
                "T12:00:00",
                "T12:15:00",
                "T12:30:00",
                "T12:45:00",
                "T13:00:00",
                "T13:15:00",
                "T13:30:00",
                "T13:45:00",
                "T14:00:00",
                "T14:15:00",
                "T14:30:00",
                "T14:45:00",
                "T15:00:00",
                "T15:15:00",
                "T15:30:00",
                "T15:45:00",
                "T16:00:00",
                "T16:15:00",
                "T16:30:00",
                "T16:45:00",
                "T17:00:00"
            ]

            total_events = sum(1 for checkbox in checkboxes if request.POST.get(checkbox) == 'on')
            existing_events = user_settings_ref.collection('events').order_by('start').stream()
            existing_event_times = []
            for event in existing_events:
                event_data = event.to_dict()
                if 'start' in event_data:
                    existing_event_times.append(event_data['start'])
            if existing_event_times:
                last_event_date = max(existing_event_times)
            else:
                last_event_date = datetime.now()
            generated_dates = []
            for _ in range(total_events):
                new_date = generate_random_date(last_event_date, existing_event_times)
                generated_dates.append(new_date)
                last_event_date = datetime.strptime(new_date, '%Y-%m-%d')

            check_num = 1
            time_num = 0
            for checkbox in checkboxes:
                checkbox_value = request.POST.get(checkbox, 'off')
                if checkbox_value == 'on':
                    event_id = uuid.uuid4()
                    eid = str(event_id)
                    eventDocRef = user_settings_ref.collection('events').document(eid)
                    timestamp = generated_dates[time_num] + random.choice(timestamps)
                    start_time = datetime.fromisoformat(timestamp)
                    event_data = {
                        'eid': eid,
                        'start': start_time,
                        'image_url': user_settings[f'schedule_image_{str(check_num)}' ],
                        'caption': user_settings[f'schedule_cap_{str(check_num)}'],
                        'className': 'bg-elaine'
                    }
                    eventDocRef.set(event_data, merge=True)
                    time_num += 1
                check_num += 1

            firestore_data = {
                'autoState': 1
            }
            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            user_settings_strings = {
                key: value.isoformat() if isinstance(value, datetime) else value
                for key, value in user_settings.items()
            }
            context = {
                'user_settings_json': json.dumps(user_settings_strings),
                'user_settings': user_settings,
                'user_id' : user_id
            }
            return render(request, 'dashboard.html', context)
        
        user_settings_ref.set(firestore_data, merge=True)

# ----- Get the Firestore document reference for the user settings ----- #
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return redirect('login') 
# ---------------------------------------------------------------------- #
    user_settings_strings = {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in user_settings.items()
    }
    context = {
        'user_settings_json': json.dumps(user_settings_strings),
        'user_settings': user_settings,
        'user_id' : user_id
    }
    return render(request, 'dashboard.html', context)

def post_creator(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return redirect('login') 
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    image_folder_path = f'user_folders/{user_id}/images/'

    try:
        biz = user_settings['business_description']
        biz_name = user_settings['business_name']
        color = user_settings['brand_color']
    except (TypeError, KeyError):
        return redirect('login') 
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
    if request.session.get('tags') != ['']:
        tags = request.session.get('tags')
    else:
        try:
            tags = ast.literal_eval(user_settings['tags'])
        except (TypeError, KeyError):
            tags = ''

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if user_settings['isSubscriber']:
            if form_name == 'formCaption1':
                selected_option = request.session.get('selected_radio', 'stable-dif')
                isLogo = request.session.get('isLogo', None)
                post = create_caption(biz, biz_name)
                firestore_data = {'next_caption': post}
                url = user_settings['next_image_url']
            
            elif form_name == 'formPostSchedule':
                timestamps = [
                    "T12:00:00",
                    "T12:15:00",
                    "T12:30:00",
                    "T12:45:00",
                    "T13:00:00",
                    "T13:15:00",
                    "T13:30:00",
                    "T13:45:00",
                    "T14:00:00",
                    "T14:15:00",
                    "T14:30:00",
                    "T14:45:00",
                    "T15:00:00",
                    "T15:15:00",
                    "T15:30:00",
                    "T15:45:00",
                    "T16:00:00",
                    "T16:15:00",
                    "T16:30:00",
                    "T16:45:00",
                    "T17:00:00"
                ]
                existing_events = user_settings_ref.collection('events').order_by('start').stream()
                existing_event_times = []
                for event in existing_events:
                    event_data = event.to_dict()
                    if 'start' in event_data:
                        existing_event_times.append(event_data['start'])
                if existing_event_times:
                    last_event_date = max(existing_event_times)
                    print('yes', last_event_date)
                else:
                    last_event_date = datetime.now()
                    print('no', last_event_date)

                new_date = generate_random_date(last_event_date, existing_event_times)

                post = request.POST.get('edited_caption', '')
                url = request.POST.get('url')
                selected_option = request.session.get('selected_radio', 'stable-dif')
                isLogo = request.session.get('isLogo', None)
                event_id = uuid.uuid4()
                eid = str(event_id)
                eventDocRef = user_settings_ref.collection('events').document(eid)
                timestamp = new_date + random.choice(timestamps)
                start_time = datetime.fromisoformat(timestamp)
                event_data = {
                    'eid': eid,
                    'start': start_time,
                    'image_url': url,
                    'caption': post,
                    'className': 'bg-warning'
                }
                eventDocRef.set(event_data, merge=True)
                firestore_data = {'next_caption': post}
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                context = { 'user_settings': user_settings, 'success': 'Post has been successfully uploaded to the schedule!'}
                return render(request, 'post_creator.html', context)
            else:
        # ------------------- Get Selected Post Type --------------------------- #
                selected_option = request.POST.get('flexRadioDefault')
                request.session['selected_radio'] = selected_option
                isLogo = request.POST.get('isLogo', None)
                request.session['isLogo'] = isLogo
        # ---------------------------------------------------------------------- #

                if 'total_allowed_images' in user_settings and 'images_generated' in user_settings and 'cooldown_expiry' in user_settings:
                    total_allowed_images = user_settings['total_allowed_images']
                    images_generated = user_settings['images_generated']
                    cooldown_expiry = user_settings['cooldown_expiry']
                else:
                    total_allowed_images = 10
                    images_generated = 0
                    cooldown_duration = timedelta(days=1)
                    cooldown_expiry = datetime.now() + cooldown_duration
                    user_settings_ref.update({
                        'cooldown_expiry': cooldown_expiry,
                        'images_generated': images_generated,
                        'total_allowed_images': total_allowed_images
                    })

                print('1: ', images_generated)
                tz = pytz.UTC
                current_time = datetime.now(tz)

                if current_time > cooldown_expiry:
                    images_generated = 0
                    user_settings_ref.update({
                        'images_generated': images_generated
                    })
                    print('images generated reset')

                if images_generated < total_allowed_images:
                    images_generated = images_generated + 0.6
                    print('2: ', images_generated)
                    user_settings_ref.update({
                        'images_generated': images_generated,
                    })
                    print('3: ', images_generated)

                    if images_generated >= total_allowed_images:
                        cooldown_duration = timedelta(days=1)
                        cooldown_expiry = datetime.now() + cooldown_duration

                    if selected_option == 'up':
                        key = request.FILES.get('file')
                        file_extension = key.name.split('.')[-1].lower()
                        if file_extension not in ['jpg', 'jpeg', 'png']:
                            context = {
                                'user_settings': user_settings,
                                'error': 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png'
                            }
                            return render(request, 'post_creator.html', context)
                        
                    elif selected_option == 'stable-dif':
                        entered_tags = request.POST.get('tags')
                        tags = entered_tags.split(',')
                        request.session['tags'] = tags
                        key = tags
                    elif selected_option == 'graphic':
                        key = biz
                    elif selected_option == 'stock':
                        key = biz
                    else:
                        key = biz
                    try:
                        last_image_url = user_settings['next_image_url']
                        last_caption = user_settings['next_caption']
                    except (TypeError, KeyError):
                        last_image_url = None
                        last_caption = None
                    
                    url = create_image(website, color, selected_option, isLogo, logo_path, key, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path, num_post)
                    post = create_caption(biz, biz_name)
                else:
                    return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Our generators need time to cooldown. You can check the progress in the brand settings tab.'})
                
                firestore_data = {
                    'last_image_url': last_image_url,
                    'last_caption': last_caption,
                    'next_image_url': url,
                    'next_caption': post,
                    'num_post': num_post,
                    'cooldown_expiry': cooldown_expiry,
                    'images_generated': images_generated
                }

            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            user_settings['tags'] = json.dumps(tags)

            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings})
        else:
            return render(request, 'post_creator.html', {'user_settings': user_settings, 'error': 'We are here to help your business. Our generators are in high demand and accrue a cost. Please subscribe to utilize our amazing app!'})

    context = {'user_settings': user_settings,}
    
    return render(request, 'post_creator.html', context)

def schedule(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return redirect('login') 
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #
    
    if request.method == 'POST':
        form_name = request.POST.get('form')

    context = {
        'user_settings': user_settings,
        'user_id': user_id
    }
    return render(request, 'calendar.html', context)

def brand_settings(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return redirect('login') 
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #s

    try:
        generated_images = user_settings['images_generated']
        total_allowed_images = user_settings['total_allowed_images']
        cooldown_expiry = user_settings['cooldown_expiry']
        progress_ratio = generated_images / total_allowed_images
        tz = pytz.UTC
        current_time = datetime.now(tz)
        remaining_time = (cooldown_expiry - current_time).total_seconds()
        total_seconds_in_day = 30 * 60 * 60
        cooldown_ratio = remaining_time / total_seconds_in_day
        combined_ratio = (progress_ratio + cooldown_ratio) / 2
        progress_percentage = int(combined_ratio * 100)
        cooldown = min(100, max(1, progress_percentage))
        print(cooldown)

    except (TypeError, KeyError):
        cooldown = None

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'brand-settings':
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
            
            if request.POST.get('tags'):
                if request.POST.get('business_description') == user_settings['business_description']:
                    input_string = request.POST.get('tags')
                    output_list = [item.strip() for item in input_string.split(',')]
                    output_string = json.dumps(output_list)
                    tags = output_string
                else:
                    tags = create_tags(request.POST.get('business_description'))
            else:
                if request.POST.get('business_description'):
                    tags = create_tags(request.POST.get('business_description'))
                else:
                    tags = ''

            firestore_data = {
                'business_name': request.POST.get('business_name'),
                'business_description': request.POST.get('business_description'),
                'brand_color': request.POST.get('brand_color'),
                'website': request.POST.get('website'),
                'logo': logo_url,
                'tags': tags
            }

        elif form_name == 'user-settings':
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
            
            firestore_data = {
                'user_name': request.POST.get('user_name'),
                'pfp': pfp_url,
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
            return redirect('login') 
        # ---------------------------------------------------------------------- #
        context = {
        'user_settings': user_settings,
        'success': 'Settings Updated',
        'cooldown': cooldown
        }
        return render(request, 'brand_settings.html', context)

    context = {
        'user_settings': user_settings,
        'cooldown': cooldown
    }
    return render(request, 'brand_settings.html', context)

def error(request):
    return render(request, 'error.html', status=500)

## ------------------ LINKING SOCIALS ------------------------- ##

def all_auth(request):
    if request.method == 'POST':
        form_name = request.POST.get('form')
        state = secrets.token_urlsafe(16)
        redirect_uri = settings.REDIRECT_URI
        if form_name == 'formLinkedin':
            request.session['provider'] = 'linkedin'
            auth_url = f'https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={settings.LINKEDIN_CLIENT_ID}&redirect_uri={redirect_uri}&scope=w_member_social profile email&state={state}'
        elif form_name == 'formGoogle':
            request.session['provider'] = 'google_business'
            AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
            CLIENT_ID = settings.GOOGLE_APP_ID
            REDIRECT_URI = redirect_uri
            SCOPES = ['https://www.googleapis.com/auth/business.manage']
            STATE = state
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
        elif form_name == 'formFacebook':
            request.session['provider'] = 'facebook'
            # AUTHORIZATION_URL = 'https://www.facebook.com/v13.0/dialog/oauth'
            # CLIENT_ID = settings.FACEBOOK_APP_ID
            # REDIRECT_URI = redirect_uri
            # STATE = state
            # SCOPES = [
            # 'manage_pages',
            # 'publish_pages',
            # 'pages_read_engagement',
            # 'pages_manage_posts',
            # 'publish_video',
            # 'publish_to_groups',
            # 'user_managed_groups']
            # auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
            auth_url = 'http://127.0.0.1:8000/callback/'
        elif form_name == 'formInstagram':
            # instagram_content_publish
            request.session['provider'] = 'instagram'
            # AUTHORIZATION_URL = 'https://www.facebook.com/v13.0/dialog/oauth'
            # CLIENT_ID = settings.FACEBOOK_APP_ID
            # REDIRECT_URI = redirect_uri
            # STATE = state
            # SCOPES = [
            # 'instagram_content_publish',
            # 'instagram_basic',
            # 'instagram_manage_comments',
            # 'instagram_manage_insights',
            # 'instagram_content_publish',
            # 'instagram_manage_messages'
            # ]
            # auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
            auth_url = 'http://127.0.0.1:8000/callback/'
        else:
            return redirect('brand_settings')
    else:
        return redirect('dashboard')
    return redirect(auth_url)

def callback(request):
    try:
        state = request.GET.get('state')
        provider = request.session.get('provider')
            # ----- Get the Firestore document reference for the user settings ----- #
        try:
            db = firestore.client()
            user_id = request.session.get('user_id')
            user_settings_ref = db.collection('users').document(user_id)
            try:
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                
            except firestore.NotFound:
                return render(request, 'error.html', {'error_message': 'Please Try Logging in Again.'})
        except AttributeError as e:
            return render(request, 'error.html', {'error_message': 'Please Try Logging in Again.'})
        
            # ---------------------------------------------------------------------- #

        if provider == 'linkedin':
            code = request.GET.get('code')
            print(code)
            access_token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
            params = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': settings.REDIRECT_URI,
                'client_id': settings.LINKEDIN_CLIENT_ID,
                'client_secret': settings.LINKEDIN_CLIENT_SECRET,
            }
            response = requests.post(access_token_url, data=params)
            data = response.json()
            access_token = data.get('access_token')
            print('AC: ', access_token)
            pass
        elif provider == 'facebook':
            # code = request.GET.get('code')
            # access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
            # params = {
            #     'client_id': settings.FACEBOOK_APP_ID,
            #     'client_secret': settings.FACEBOOK_APP_SECRET,
            #     'redirect_uri': settings.REDIRECT_URI,
            #     'code': code
            # }
            # response = requests.get(access_token_url, params=params, verify=False)
            # data = response.json()
            # access_token = data.get('access_token')
            access_token = 'EAADFIOXHRl4BO1PRnYWBXPgjZCmxZAH7hyMac4vL1Q97yqjLmIWkDLtOUFZAR8Cfz5GziMT9MASay51NuNMlpsBnyQqcgsoOfAYSGDibdxRdflX41t6Awx4Mw55yn6ZBgKJe7smF8aoErPiibEopx2nY8kTjd04Dkyh9bi1ZBBnjogxExnfSZBHD5xPLigzoHI8Q8jjirFZBmx5gCezwnt28q6CCRZBZCLoJbeSFL076dPLrGgzeO8QZDZD'
            pass
        elif provider == 'instagram':
            # code = request.GET.get('code')
            # access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
            # params = {
            #     'client_id': settings.FACEBOOK_APP_ID,
            #     'client_secret': settings.FACEBOOK_APP_SECRET,
            #     'redirect_uri': settings.REDIRECT_URI,
            #     'code': code
            # }
            # response = requests.get(access_token_url, params=params, verify=False)
            # data = response.json()
            # access_token = data.get('access_token')
            access_token = 'EAADFIOXHRl4BO1PRnYWBXPgjZCmxZAH7hyMac4vL1Q97yqjLmIWkDLtOUFZAR8Cfz5GziMT9MASay51NuNMlpsBnyQqcgsoOfAYSGDibdxRdflX41t6Awx4Mw55yn6ZBgKJe7smF8aoErPiibEopx2nY8kTjd04Dkyh9bi1ZBBnjogxExnfSZBHD5xPLigzoHI8Q8jjirFZBmx5gCezwnt28q6CCRZBZCLoJbeSFL076dPLrGgzeO8QZDZD'
            pass
        elif provider == 'google_business':
            code = request.GET.get('code')
            access_token_url = 'https://oauth2.googleapis.com/token'
            params = {
                'client_id': settings.GOOGLE_APP_ID,
                'client_secret': settings.GOOGLE_APP_SECRET,
                'redirect_uri': settings.REDIRECT_URI,
                'code': code,
                'grant_type': 'authorization_code'
            }
            response = requests.post(access_token_url, data=params)
            data = response.json()
            access_token = data['access_token']
            print('AC: ', access_token)
            pass
        firestore_data = {
            f'{provider}_token': access_token,
        }

        user_settings_ref.set(firestore_data, merge=True)
        return redirect('brand_settings')
    except:
        return redirect('brand_settings')
## ------------------ FIREBASE SAFETY ------------------------- ##

def get_firebase_config(request):
    config = {
        'apiKey': os.environ.get("FIREBASE_API_KEY"),
        'authDomain': os.environ.get("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.environ.get("FIREBASE_PROJECT_ID"),
        'storageBucket': os.environ.get("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.environ.get("FIREBASE_APP_ID"),
        'measurementId': os.environ.get("FIREBASE_MEASUREMENT_ID"),
    }
    return JsonResponse(config)

## ------------------ STRIPE ------------------------- ##

@csrf_exempt  
def checkout(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id')
        # ----- Get the Firestore document reference for the user settings ----- #
        try:
            db = firestore.client()
            user_settings_ref = db.collection('users').document(user_id)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            try:
                customer_id = user_settings['customer_id']
            except (TypeError, KeyError):
                customer_id = None
            
        except AttributeError as e:
            return render(request, 'error.html', {'error': str(e)})
            # ---------------------------------------------------------------------- #
        try:
            if customer_id is None:
                try:
                    user = auth.get_user(user_id)
                    user_email = user.email
                    stripe_customer = stripe.Customer.create(email=user_email)
                    customer_id = stripe_customer.id
                    firestore_data = {'customer_id': customer_id,}
                    user_settings_ref.set(firestore_data, merge=True)
                except Exception as e:
                    return render(request, 'error.html', {'error': str(e)})

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Feadl.io Standard Plan',
                        },
                        'unit_amount': 2699,
                        'recurring': {
                            'interval': 'month',  
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.STRIPE_SUCCESS_URL + f'?customer_id={customer_id}',
                cancel_url=settings.STRIPE_CANCEL_URL,
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return render(request, 'error.html', {'error': str(e)})

    return render(request, 'error.html', {'error': str(e)})

@csrf_exempt
def success(request):
    customer_id = request.GET.get('customer_id')
    print('customer_id:', customer_id)
    try:
        db = firestore.client()
        docs = (
            db.collection('users')
            .where(filter=FieldFilter("customer_id", "==", customer_id))
            .stream()
        )
        print('Headed into for loop', docs)
        for doc in docs:
            user_id = doc.id
            print('User ID:', user_id)
            user_settings_ref = db.collection('users').document(user_id)
            firestore_data = {'isSubscriber': True}
            user_settings_ref.set(firestore_data, merge=True)
            print('Success!')
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})
    # ---------------------------------------------------------------------- #
    return redirect('dashboard')

@csrf_exempt
def cancel(request):
    print('Cancelled')
    return redirect('dashboard')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        session = event['data']['object']
        customer_id = session.get('customer')
        db = firestore.client()
        docs = (
            db.collection('users')
            .where(filter=FieldFilter("customer_id", "==", customer_id))
            .stream()
        )
        for doc in docs:
            user_id = doc.id
            print('User ID:', user_id)
            user_settings_ref = db.collection('users').document(user_id)
            print('Got Ref!')
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})
    # ---------------------------------------------------------------------- #
    
    if event['type'] == 'checkout.session.completed':
        firestore_data = {'isSubscriber': True}
        user_settings_ref.set(firestore_data, merge=True)
        print('Checkout Session Complete!')
        return JsonResponse({'status': 'Checkout Complete'})

    if event['type'] == 'subscription_schedule.canceled':
        firestore_data = {'isSubscriber': False}
        user_settings_ref.set(firestore_data, merge=True)
        print('Subscription Canceled!')
        return JsonResponse({'status': 'Subscription Checked and Canceled'})

    return JsonResponse({'status': 'nothing'})