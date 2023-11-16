from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from .forms import UserSettingsForm
from .models import UserSettings
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud.firestore_v1.base_query import FieldFilter
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport import requests
from urllib.parse import urlparse
import os
from .post_creator import create_stock_post, create_call_to_action, create_caption, create_dalle_post, create_stable_dif_post, create_ad_copy, create_ad_headline, create_placeholder, upload_jpg_to_google, add_watermark, create_upload, create_ad_creative, upload_png_to_google
from .post_to_media import post_to_facebook_page_feed, post_to_instagram, post_to_linkedin, post_to_google_mybusiness, get_instagram_user_id, get_facebook_page_id
from django.http import JsonResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
import time
from .functions import generate_random_date, create_tags, generate_secondary_colors, create_text_post, add_stock_tags, upload_and_crop_image, delete_from_google, reupload_gcs_image
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
import io
from io import BytesIO
import jwt
import re
import imghdr

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
        global_variables_ref = db.collection('variables').document('global_variables')
        try:
            user = auth.get_user(user_id)
            user_email = user.email
        except auth.AuthError as e:
            user_email = ''

        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            global_variables_doc = global_variables_ref.get()
            global_variables = global_variables_doc.to_dict()
            
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
                    colors = generate_secondary_colors(brand_color)
                    tags = create_tags(business_description)

                    # Prepare the data to be saved in Firestore
                    firestore_data = {
                        'ftue3': False,
                        'ftue4': True,
                        'tags': tags,
                        'business_description': business_description,
                        'business_name': business_name,
                        'brand_color': brand_color,
                        'secondary_colors' : colors
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
                if 'total_allowed_images' in global_variables and 'images_generated' in user_settings and 'cooldown_expiry' in user_settings:
                    total_allowed_images = user_settings['total_allowed_images']
                    images_generated = user_settings['images_generated']
                    cooldown_expiry = user_settings['cooldown_expiry']
                else:
                    total_allowed_images = global_variables['total_allowed_images']
                    images_generated = 0
                    cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
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
                    cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
                    cooldown_expiry = datetime.now() + cooldown_duration
                    user_settings_ref.update({
                        'images_generated': images_generated,
                        'cooldown_expiry': cooldown_expiry
                    })

                if images_generated < total_allowed_images:
                    images_generated = images_generated + 2
                    user_settings_ref.update({
                        'images_generated': images_generated,
                    })

                    if images_generated >= total_allowed_images:
                        cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
                        cooldown_expiry = datetime.now() + cooldown_duration

                    image_folder_path = f'ai_image_library/'
                    tags = user_settings['tags']
                    key = user_settings['business_description']
                    biz_name = user_settings['business_name']
                    color = user_settings['brand_color']
                    secondary_colors = user_settings['secondary_colors']
                    selected_option = 'cta'
                    isLogo = False
                    logo_path = ''
                    post_num1 = random.randint(1, global_variables['random_int_max'])
                    post_num2 = random.randint(1, global_variables['random_int_max'])
                    payload = {'user_id': user_id}
                    try:
                        enqueue_task(payload, settings.GS_IMAGE_QUEUE_NAME, settings.GS_GENERATE_AI_IMAGE_URL)
                        enqueue_task(payload, settings.GS_IMAGE_QUEUE_NAME, settings.GS_GENERATE_STOCK_URL)
                        enqueue_task(payload, settings.GS_IMAGE_QUEUE_NAME, settings.GS_GENERATE_CAPTIONS_URL)
                    except:
                        context = {
                            'user_settings_json': json.dumps(user_settings_strings),
                            'user_settings': user_settings,
                            'user_id' : user_id,
                            'error': 'Images failed to generate. Please retry later.'
                        }
                        return render(request, 'dashboard.html', context)
                    firestore_data = {
                        'status': '10',
                        'status2': '0',
                        'status3': '0',
                        'autoState': 2,
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
        elif form_name == 'formReset':
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
        elif form_name == 'formView':
            image_folder_path = f'ai_image_library/'
            tags = user_settings['tags']
            tags_list = ast.literal_eval(tags)
            key = random.choice(tags_list)
            business_description = user_settings['business_description']
            biz_name = user_settings['business_name']
            color = user_settings['brand_color']
            secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
            post_num1 = user_settings['post_num1']
            post_num2 = user_settings['post_num2']
            selected_option = 'cta'
            isLogo = False
            logo_path = ''
            random_int = random.randint(1, global_variables['random_int_max'])
            random_int2 = random.randint(1, global_variables['random_int_max'])
            try:
                image_list = [user_settings['schedule_image_1'], user_settings['schedule_image_2'], user_settings['schedule_image_3'], user_settings['schedule_image_4'], user_settings['schedule_image_5'], user_settings['schedule_image_6']]
                img_url = random.choice(image_list)
            except:
                img = create_stock_post(key)
                img_url = upload_jpg_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
            schedule_img_7 = create_call_to_action(business_description, biz_name, color, secondary_colors, img_url, random_int, logo_path)
            schedule_img_8 = create_call_to_action(business_description, biz_name, color, secondary_colors, img_url, random_int2, logo_path)

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
                "T21:00:00",
                "T21:30:00",
                "T22:00:00",
                "T22:30:00",
                "T23:00:00",
                "T23:30:00"
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
                    socials = []
                    social_options = {
                        'isFacebook': 'facebook',
                        'isInstagram': 'instagram',
                        'isLinkedin': 'linkedin',
                        'isGoogle': 'google_business'
                    }
                    for option, platform in social_options.items():
                        if option in user_settings and user_settings[option]:
                            try:
                                socials.append(platform)
                            except Exception as e:
                                return render(request, 'error.html', {'error': str(e)})
                        else:
                            pass
                    event_data = {
                        'eid': eid,
                        'start': start_time,
                        'image_url': user_settings[f'schedule_image_{str(check_num)}' ],
                        'caption': user_settings[f'schedule_cap_{str(check_num)}'],
                        'className': 'bg-elaine',
                        'socials': socials,
                        'type': 'image',
                        'status': 'pending',
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

def download(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return redirect('login')
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #
    url = user_settings['next_image_url']
    parsed_url = urlparse(url)
    if parsed_url.netloc == 'storage.googleapis.com':
        parts = parsed_url.path.strip('/').split('/')
        bucket_name = parts[0]
        object_name = '/'.join(parts[1:])
    else:
        raise ValueError('Invalid Google Cloud Storage URL')
    
    storage_client = storage.Client()
    bucket_name = bucket_name
    blob_name = object_name
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    file_content = blob.download_as_bytes()
    file_name = 'feadlio.jpg'
    response = FileResponse(
        io.BytesIO(file_content),
        as_attachment=True,
        filename=file_name
    )
    return response

def ad_manager(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return redirect('login')
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    ads_folder_path = f'ads/'
    biz = user_settings['business_description']
    try:
        logo_path = user_settings['logo']
        isLogo = True
    except (TypeError, KeyError):
        isLogo = False
        logo_path = None
    try:
        num_ad = int(user_settings['num_ad'])
    except (TypeError, KeyError):
        num_ad = 1
    try:
        ad_image_url = user_settings['ad_image_url']
    except (TypeError, KeyError):
        ad_image_url = None
    try:
        ad_copy = user_settings['ad_copy']
    except (TypeError, KeyError):
        ad_copy = None
    try:
        ad_headline = user_settings['ad_headline']
    except (TypeError, KeyError):
        ad_headline = None

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'formCopy':
            ad_copy = create_ad_copy(biz, user_settings['business_name'])
            ad_headline = create_ad_headline(biz, user_settings['business_name'])
        elif form_name == 'formCopySave':
            ad_copy = request.POST.get('ad_copy_content')
            ad_headline = request.POST.get('ad_headline_content')
        elif form_name == 'formAdRequest':
            user = auth.get_user(user_id)
            user_email = user.email
            subject = 'Feadl.io Ad Request'
            message = 'USER EMAIL: {}\nUSER ID: {}\nBUSINESS_NAME: {}\n\nAD COST: {}\n\nCAMPAIGN NAME: {}\nAD IMAGE: {}\nAD_COPY: {}'.format(
                user_email,
                request.POST.get('user_id'),
                request.POST.get('business_name'),
                request.POST.get('ad_cost'),
                request.POST.get('name'),
                request.POST.get('ad_image_url'),
                request.POST.get('ad_copy')
            )
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [settings.INTERNAL_RECIPIENTS]
            email = EmailMessage(subject, message, from_email, recipient_list)
            try:
                email.send()
                firestore_data = {'isAdRequested': True, 'isAdRun': False}
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                isLogo = request.session.get('isLogo', None)
                context = {
                    'user_settings': user_settings,
                    'user_id': user_id,
                    'isLogo': isLogo,
                    'success': "You're request was sent! We will get back to you with an email shortly.",
                }
            except Exception as e:
                isLogo = request.session.get('isLogo', None)
                context = {
                    'user_settings': user_settings,
                    'user_id': user_id,
                    'isLogo': isLogo,
                    'error': "There was an error with your request. Please wait a moment and try again.",
                }
            
            return render(request, 'ad_manager.html', context)

        elif form_name == 'formImg':
            isLogo = request.POST.get('isLogo', None)
            request.session['isLogo'] = isLogo
            ad_image_url = create_call_to_action(isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path, num_ad)
            if num_ad <= 5:
                num_ad += 1
        else:
            isLogo = request.POST.get('isLogo', None)
            request.session['isLogo'] = isLogo
            ad_image_url = create_call_to_action(isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path, num_ad)
            ad_copy = create_ad_copy(biz, user_settings['business_name'])
            if num_ad <= 5:
                num_ad += 1

        # Prepare the data to be saved in Firestore
        firestore_data = {
            'ad_image_url': ad_image_url,
            'ad_copy': ad_copy,
            'ad_headline': ad_headline,
            'num_ad': num_ad
        }

        # Save the data to Firestore
        user_settings_ref.set(firestore_data, merge=True)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        
    isLogo = request.session.get('isLogo', None)
    context = {
        'user_settings': user_settings,
        'user_id': user_id,
        'isLogo': isLogo,
    }
    return render(request, 'ad_manager.html', context)

def post_creator(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            global_variables_doc = global_variables_ref.get()
            global_variables = global_variables_doc.to_dict()
        except firestore.NotFound:
            return redirect('login') 
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    image_folder_path = f'ai_image_library/'

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
                selected_option = request.session.get('selected_radio')
                isLogo = request.session.get('isLogo', None)
                if selected_option == "text":
                    post = create_text_post('facebook', biz, biz_name)
                else:
                    post = create_caption(biz, biz_name)
                firestore_data = {'next_caption': post}
                url = user_settings['next_image_url']
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()

                return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings})
            if form_name == 'formDownload':
                selected_option = request.session.get('selected_radio')
                isLogo = request.session.get('isLogo', None)
                url = user_settings['next_image_url']
                parsed_url = urlparse(url)
                if parsed_url.netloc == 'storage.googleapis.com':
                    parts = parsed_url.path.strip('/').split('/')
                    bucket_name = parts[0]
                    object_name = '/'.join(parts[1:])
                else:
                    raise ValueError('Invalid Google Cloud Storage URL')
                
                storage_client = storage.Client()
                bucket_name = bucket_name
                blob_name = object_name
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename("downloaded_image.jpg")
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()

                return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings})
            elif form_name == 'formPostSchedule':
                timestamps = [
                    "T21:00:00",
                    "T21:30:00",
                    "T22:00:00",
                    "T22:30:00",
                    "T23:00:00",
                    "T23:30:00"
                ]
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

                new_date = generate_random_date(last_event_date, existing_event_times)

                post = request.POST.get('edited_caption', '')
                if user_settings['lastType'] == 'text':
                    url = "https://storage.googleapis.com/starter_web_app_bucket/user_folders/assets/textPost.png"
                    post_type = 'text'
                else:
                    post_type = "image"
                    url = reupload_gcs_image(request.POST.get('url'), "scheduled_image_library")
                selected_option = request.session.get('selected_radio', 'stable-dif')
                isLogo = request.session.get('isLogo', None)
                event_id = uuid.uuid4()
                eid = str(event_id)
                eventDocRef = user_settings_ref.collection('events').document(eid)
                timestamp = new_date + random.choice(timestamps)
                start_time = datetime.fromisoformat(timestamp)
                socials = []
                social_options = {
                    'isFacebook': 'facebook',
                    'isInstagram': 'instagram',
                    'isLinkedin': 'linkedin',
                    'isGoogle': 'google_business'
                }
                for option, platform in social_options.items():
                    if option in user_settings and user_settings[option]:
                        try:
                            socials.append(platform)
                        except Exception as e:
                            return render(request, 'error.html', {'error': str(e)})
                    else:
                        pass
                event_data = {
                    'eid': eid,
                    'start': start_time,
                    'image_url': url,
                    'caption': post,
                    'className': 'bg-warning',
                    'socials': socials,
                    'type' : post_type,
                    'status': 'pending',
                }
                eventDocRef.set(event_data, merge=True)
                firestore_data = {'next_caption': post}
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                context = { 'user_settings': user_settings, 'success': 'Post has been successfully uploaded to the schedule!'}
                return render(request, 'post_creator.html', context)
            elif form_name == 'formPostPost':
                caption = request.POST.get('edited_caption2', '')
                selected_option = request.session.get('selected_radio', 'stable-dif')
                isLogo = request.session.get('isLogo', None)
                image_url = request.POST.get('url2', '')
                if 'isFacebook' in user_settings and user_settings['isFacebook']:
                    page_id = user_settings['facebook_page_id']
                    access_token = user_settings['facebook_token']
                    post_to_facebook_page_feed(caption, image_url, page_id, access_token)
                elif 'isInstagram' in user_settings and user_settings['isInstagram']:
                    instagram_user_id = user_settings['instagram_user_id']
                    access_token = user_settings['instagram_token']
                    post_to_instagram(access_token, image_url, caption, instagram_user_id)
                elif 'isGoogle' in user_settings and user_settings['isGoogle']:
                    access_token = user_settings['google_token']
                    post_to_google_mybusiness(caption, image_url, access_token)
                elif 'isLinkedin' in user_settings and user_settings['isLinkedin']:
                    access_token = user_settings['linkedin_token']
                    post_to_linkedin(caption, image_url, access_token, page_id)
                context = { 'user_settings': user_settings, 'success': 'Post has been successfully uploaded to your feed!'}
                return render(request, 'post_creator.html', context)
            else:
        # ------------------- Get Selected Post Type --------------------------- #
                selected_option = request.POST.get('selected_post_type')
                request.session['selected_radio'] = selected_option
                isLogo = request.POST.get('isLogo', None)
                request.session['isLogo'] = isLogo
        # ---------------------------------------------------------------------- #

                if 'total_allowed_images' in global_variables and 'images_generated' in user_settings and 'cooldown_expiry' in user_settings:
                    total_allowed_images = global_variables['total_allowed_images']
                    images_generated = user_settings['images_generated']
                    cooldown_expiry = user_settings['cooldown_expiry']
                else:
                    total_allowed_images = 10
                    images_generated = 0
                    cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
                    cooldown_expiry = datetime.now() + cooldown_duration
                    user_settings_ref.update({
                        'cooldown_expiry': cooldown_expiry,
                        'images_generated': images_generated,
                        'total_allowed_images': total_allowed_images
                    })

                tz = pytz.UTC
                current_time = datetime.now(tz)

                if current_time.astimezone(tz) > cooldown_expiry.astimezone(tz):
                    images_generated = 0
                    cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
                    cooldown_expiry = datetime.now() + cooldown_duration
                    user_settings_ref.update({
                        'cooldown_expiry': cooldown_expiry,
                        'images_generated': images_generated
                    })

                if images_generated < total_allowed_images:
                    images_generated = images_generated + 0.6
                    user_settings_ref.update({
                        'images_generated': images_generated,
                    })

                    if images_generated >= total_allowed_images:
                        cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
                        cooldown_expiry = datetime.now() + cooldown_duration

                    if selected_option == 'up':
                        image = request.FILES.get('file')
                        isGraphic = request.POST.get('isGraphic')
                        isLogo = request.POST.get('isLogo')
                        name = request.POST.get('photo-attribution')
                        file_extension = image.name.split('.')[-1].lower()
                        if file_extension not in ['jpg', 'jpeg', 'png']:
                            context = {
                                'user_settings': user_settings,
                                'error': 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png'
                            }
                            return render(request, 'post_creator.html', context)
                        # try:
                        img = create_upload(image, logo_path, isLogo, isGraphic, color, name)
                        url = upload_png_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        # except requests.exceptions.HTTPError:
                        #     return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. Your input may be too specific. Please try again.'})
                        # except:
                        #     return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})
                    elif selected_option == 'text':
                        platform = request.POST.get('text-platfrom')
                        try:
                            post = create_text_post(platform, biz, biz_name)
                            url = "https://storage.googleapis.com/starter_web_app_bucket/user_folders/assets/textPost.png"
                        except requests.exceptions.HTTPError:
                            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. Your input may be too specific. Please try again.'})
                        except:
                            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})
                    
                    elif selected_option == 'stable-dif':
                        entered_tags = request.POST.get('tags')
                        tags = entered_tags.split(',')
                        request.session['tags'] = tags
                        key = tags
                        try:
                            img = create_stable_dif_post(key)
                            if isLogo == 'true':
                                if logo_path is not None:
                                        img = add_watermark(img, logo_path)
                            url = upload_jpg_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        except requests.exceptions.HTTPError:
                            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. Your input may be too specific. Please try again.'})
                        except:
                            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})
                    elif selected_option == 'graphic':
                        key = request.POST.get('graphic-description')
                        img_url = request.POST.get('selected_image_url', None)
                        print(img_url)
                        random_int = random.randint(global_variables['random_int_min'], global_variables['random_int_max'])
                        image_folder_path = f'graphic_image_library/'
                        color = user_settings['brand_color']
                        secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
                        if img_url == 'None':
                            img = create_stable_dif_post(key)
                            img_url = upload_jpg_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        # try:
                        img = create_call_to_action(biz, biz_name, color, secondary_colors, img_url, random_int, logo_path)
                        url = upload_png_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        # except requests.exceptions.HTTPError:
                        #     return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. Your input may be too specific. Please try again.'})
                        # except:
                        #     return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})
                    elif selected_option == 'ad':
                        key = request.POST.get('ad-creative-description')
                        img_url = request.POST.get('selected_ad_creative_image_url', None)
                        print(img_url)
                        platform = request.POST.get('text-platform')
                        random_int = random.randint(global_variables['random_ad_int_min'], global_variables['random_ad_int_max'])
                        image_folder_path = f'ad_image_library/'
                        color = user_settings['brand_color']
                        secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
                        if img_url == 'None':
                            img = create_stable_dif_post(key)
                            img_url = upload_jpg_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        # try:
                        img = create_ad_creative(biz, biz_name, color, secondary_colors, img_url, random_int, logo_path)
                        url = upload_png_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        # except requests.exceptions.HTTPError:
                        #     return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. Your input may be too specific. Please try again.'})
                        # except:
                        #     return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})
                    
                    elif selected_option == 'stock':
                        key = request.POST.get('stock-description')
                        try:
                            img = create_stock_post(key)
                            if isLogo == 'true':
                                if logo_path is not None:
                                        img = add_watermark(img, logo_path)
                            url = upload_jpg_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                        except requests.exceptions.HTTPError:
                            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. Your input may be too specific. Please try again.'})
                        except:
                            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})
                    else:
                        return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/'})

                    try:
                        last_image_url = user_settings['next_image_url']
                        last_caption = user_settings['next_caption']
                    except (TypeError, KeyError):
                        last_image_url = None
                        last_caption = None
                    if selected_option != "text":
                        if selected_option == "ad":
                            post = create_ad_copy(biz, biz_name, platform)
                        else:
                            post = create_caption(biz, biz_name)
                else:
                    return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings, 'error': 'Our generators need time to cooldown. You can check the progress in the brand settings tab.'})
                post_type = selected_option
                try:
                    delete_from_google(user_settings['next_image_url'], settings.GS_CREDENTIALS)
                except:
                    pass
                    
                firestore_data = {
                    'last_image_url': last_image_url,
                    'last_caption': last_caption,
                    'next_image_url': url,
                    'next_caption': post,
                    'lastType' : post_type,
                    'num_post': num_post,
                    'cooldown_expiry': cooldown_expiry,
                    'images_generated': images_generated
                }

            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()

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
        global_variables_ref = db.collection('variables').document('global_variables')
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            global_variables_doc = global_variables_ref.get()
            global_variables = global_variables_doc.to_dict()
        except firestore.NotFound:
            return redirect('login') 
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #s

    try:
        generated_images = user_settings['images_generated']
        total_allowed_images = global_variables['total_allowed_images']
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

    except (TypeError, KeyError):
        cooldown = None

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'brand-settings':
            logo = request.FILES.get('logo')
            if logo:
                try:
                    delete_from_google(user_settings['logo'], settings.GS_CREDENTIALS)
                except:
                    pass
                credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
                client = storage.Client(project=credentials.project_id, credentials=credentials)
                bucket = client.bucket(settings.GS_BUCKET_NAME)
                logo_folder_path = f'user_folders/{user_id}/logo/'
                filename = str(uuid.uuid4()) + ".png"
                blob = bucket.blob(logo_folder_path + filename)
                blob.upload_from_file(logo)
                blob.make_public()
                logo_url = blob.public_url
            else:
                try:
                    logo_url = user_settings['logo']
                except (TypeError, KeyError):
                    logo_url = None

# ------------------ TAGS ---------------#
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

# ------------------ COLORS ---------------#
            colors = user_settings['secondary_colors']
            color_array = ast.literal_eval(colors)
            color2 = color_array[0]
            color3 = color_array[1]
            color4 = color_array[2]
            color5 = color_array[3]

            if request.POST.get('brand_color') != user_settings['brand_color']:
                colors = generate_secondary_colors(request.POST.get('brand_color'))
                color_array = ast.literal_eval(colors)
            
            if request.POST.get('color2') != color2:
                color_array[0] = request.POST.get('color2')
            if request.POST.get('color3') != color3:
                color_array[1] = request.POST.get('color3')
            if request.POST.get('color4') != color4:
                color_array[2] = request.POST.get('color4')
            if request.POST.get('color5') != color5:
                color_array[3] = request.POST.get('color5')
            
            colors = str(color_array)
# ------------------ ------------ ---------------#

            firestore_data = {
                'business_name': request.POST.get('business_name'),
                'business_description': request.POST.get('business_description'),
                'brand_color': request.POST.get('brand_color'),
                'website': request.POST.get('website'),
                'logo': logo_url,
                'tags': tags,
                'secondary_colors': colors
            }
        
# ------------------ IMAGE TAGS ---------------#

        elif form_name == 'image-tags':
            stock_image_folder_path = f'stock_image_library/'
            user_image_folder_path = f'user_image_library/'
            post_image_tags = request.POST.get('imageTags')
            if post_image_tags:
                image_tags = []
                output_list = [item.strip() for item in post_image_tags.split(',')]
                image_tags.extend(output_list)
            else:
                image_tags = []

            post_image_files = request.FILES.get('file')
            if post_image_files:
                uploaded_image_url = upload_and_crop_image(post_image_files, user_image_folder_path)
                image_tags.append(uploaded_image_url)

            is_generate_stock_images_clicked = request.POST.get('isGenerateStockImagesClicked', 'false') == 'true'
            if is_generate_stock_images_clicked:
                image_tags = add_stock_tags(user_settings['tags'], image_tags, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, stock_image_folder_path)
            image_tags_string = json.dumps(image_tags)
            image_tags_string = image_tags_string.replace("'", '"')
            firestore_data = {
                'image_tags': image_tags_string,
            }

        elif form_name == 'user-settings':
            pfp = request.FILES.get('pfp')
            if pfp:
                try:
                    delete_from_google(user_settings['pfp'], settings.GS_CREDENTIALS)
                except:
                    pass
                credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
                client = storage.Client(project=credentials.project_id, credentials=credentials)
                bucket = client.bucket(settings.GS_BUCKET_NAME)
                pfp_folder_path = f'user_folders/{user_id}/pfp/'
                pfp_content = pfp.read()
                image_type = imghdr.what(None, h=pfp_content)
                if image_type == 'jpeg':
                    extension = '.jpg'
                elif image_type == 'png':
                    extension = '.png'
                else:
                    raise ValueError("Unsupported image type")

                blob_name = pfp_folder_path + 'pfp' + extension
                blob = bucket.blob(blob_name)
                pfp.seek(0)
                blob.upload_from_file(pfp, content_type=f'image/{image_type}')
                blob.make_public()
                pfp_url = blob.public_url
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
        if user_settings is None:
            user_settings_strings = {}
        else:
            user_settings_strings = {
                key: value.isoformat() if isinstance(value, datetime) else value
                for key, value in user_settings.items()
            }
        context = {
        'user_settings_json': json.dumps(user_settings_strings),
        'user_settings': user_settings,
        'user_id' : user_id,
        'success': 'Settings Updated',
        'cooldown': cooldown
        }
        return render(request, 'brand_settings.html', context)
    if user_settings is None:
        user_settings_strings = {}
    else:
        user_settings_strings = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in user_settings.items()
        }
    context = {
        'user_settings_json': json.dumps(user_settings_strings),
        'user_settings': user_settings,
        'user_id' : user_id,
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
            auth_url = f'https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={settings.LINKEDIN_CLIENT_ID}&redirect_uri={redirect_uri}&scope=w_member_social openid profile email&state={state}'
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
            AUTHORIZATION_URL = 'https://www.facebook.com/v13.0/dialog/oauth'
            CLIENT_ID = settings.FACEBOOK_APP_ID
            REDIRECT_URI = redirect_uri
            STATE = state
            SCOPES = [
            'pages_show_list',
            'pages_read_engagement',
            'pages_manage_posts',
            'publish_to_groups'
            ]
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
        elif form_name == 'formInstagram':
            request.session['provider'] = 'instagram'
            AUTHORIZATION_URL = 'https://www.facebook.com/v13.0/dialog/oauth'
            CLIENT_ID = settings.FACEBOOK_APP_ID
            REDIRECT_URI = redirect_uri
            STATE = state
            SCOPES = [
            'pages_show_list',
            'instagram_basic',
            'instagram_content_publish'
            ]
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
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
            isCheck = 'Linkedin'
            code = request.GET.get('code')
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
            id_token = data.get('id_token')
            decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})
            user_id = decoded_id_token.get("sub")
            firestore_data = {
                f'{provider}_id': user_id,
                f'{provider}_token': access_token,
                f'is{isCheck}': True,
            }

            user_settings_ref.set(firestore_data, merge=True)
            pass
        elif provider == 'facebook':
            isCheck = 'Facebook'
            code = request.GET.get('code')
            access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
            params = {
                'client_id': settings.FACEBOOK_APP_ID,
                'client_secret': settings.FACEBOOK_APP_SECRET,
                'redirect_uri': settings.REDIRECT_URI,
                'code': code
            }
            response = requests.get(access_token_url, params=params, verify=False)
            data = response.json()
            access_token = data.get('access_token')
            facebook_page_id = get_facebook_page_id(access_token)
            firestore_data = {
                f'{provider}_token': access_token,
                f'{provider}_page_id': facebook_page_id,
                f'is{isCheck}': True,
            }

            user_settings_ref.set(firestore_data, merge=True)
            pass
        elif provider == 'instagram':
            isCheck = 'Instagram'
            code = request.GET.get('code')
            access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
            params = {
                'client_id': settings.FACEBOOK_APP_ID,
                'client_secret': settings.FACEBOOK_APP_SECRET,
                'redirect_uri': settings.REDIRECT_URI,
                'code': code
            }
            response = requests.get(access_token_url, params=params, verify=False)
            data = response.json()
            access_token = data.get('access_token')
            facebook_page_id = get_facebook_page_id(access_token)
            instagram_user_id = get_instagram_user_id(facebook_page_id, access_token)
            firestore_data = {
                f'{provider}_token': access_token,
                f'{provider}_user_id': instagram_user_id,
                f'is{isCheck}': True,
            }

            user_settings_ref.set(firestore_data, merge=True)
            pass
        elif provider == 'google_business':
            isCheck = 'Google'
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
            firestore_data = {
                f'{provider}_token': access_token,
                f'is{isCheck}': True,
            }

            user_settings_ref.set(firestore_data, merge=True)
            pass

        return redirect('brand_settings')
    except:
        return redirect('brand_settings')
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

