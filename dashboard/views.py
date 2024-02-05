from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
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
from .post_to_socials import post_to_facebook_page_feed, post_text_to_facebook_page_feed, post_to_instagram, post_to_linkedin, post_to_google_mybusiness, get_instagram_user_id, get_facebook_pages_and_groups, get_instagram_username, post_text_to_linkedin, get_linkedin_account_name, post_video_to_facebook_page_feed, post_video_to_instagram, exchange_short_lived_token_for_long_lived
from django.http import JsonResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
import time
from .functions import generate_random_date, create_tags, generate_secondary_colors, create_text_post, add_stock_tags, upload_image_to_library, delete_from_google, reupload_gcs_image, download_and_save_image_as_seek, create_stock_image_description, create_background_image_description, create_call_to_action, create_caption, create_ad_copy, create_ad_headline, upload_jpg_to_google, add_logo, create_upload, create_ad_creative, upload_png_to_google, convert_color_to_hex, upload_video_to_google
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
from openai import OpenAI
import logging
import threading
from django.contrib import messages
from .login import user_login

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = OpenAI(api_key=config('OPENAI_API_KEY'))
assistant_ids = {'elaine': 'asst_KIHRjofgKB36hQkJt2IqXF51'}

def dashboard(request):
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')

        if not user_id:
            raise ValueError('User not logged in.')

        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')

        user_email = auth.get_user(user_id).email if user_id else ''
        user_settings = user_settings_ref.get().to_dict() or {}
        global_variables = global_variables_ref.get().to_dict() or {}

        ftue = user_settings.get('ftue', False)

        user_settings_strings = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in user_settings.items()
        }

        all_messages = request.session.get('all_messages', [{'role': 'bot', 'content': 'How can I assist you?'}])

        context = {
            'user_settings_json': json.dumps(user_settings_strings),
            'all_messages': all_messages,
            'user_settings': user_settings,
            'user_id' : user_id
        }

    except:
        message = 'An unexpected error occurred. Please try logging in again.'
        messages.error(request, message)
        return redirect('login')

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'formFtue':
            business_name = request.POST.get('business_name')
            business_description = request.POST.get('business_description')
            brand_color = request.POST.get('brand_color')
            colors = generate_secondary_colors(brand_color)
            tags = create_tags(business_description)

            # Prepare the data to be saved in Firestore
            firestore_data = {
                'tags': tags,
                'business_description': business_description,
                'business_name': business_name,
                'brand_color': brand_color,
                'secondary_colors' : colors,
                'ftue': True,
                'isSubscriber': False,
                'isLogo': False,
                'images_generated': 0,
                'progress': 100,
                'admin': False,
                'isBusiness': False,
                'email': user_email,
                'num_sent': 0,
                'last_reset_time': datetime.now()

            }

            user_settings_ref.set(firestore_data, merge=True)
            return redirect('dashboard')

    return render(request, 'dashboard.html', context)

# ---------------- chats ---------------- #

def start_chat(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    
    except:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    # ---------------------------------------------------------------------- #

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
        if user_settings['isSubscriber']:
            social_media_platforms = []

            if user_settings.get('isFacebook'):
                social_media_platforms.append('Facebook')

            if user_settings.get('isTwitter'):
                social_media_platforms.append('Twitter')

            if user_settings.get('isInstagram'):
                social_media_platforms.append('Instagram')

            if user_settings.get('isLinkedin'):
                social_media_platforms.append('Linkedin')

            assistant_id = assistant_ids.get('elaine')
            assistant = client.beta.assistants.retrieve(assistant_id)
            
            if 'thread_id' not in request.session:
                thread = client.beta.threads.create()
                request.session['thread_id'] = thread.id
                thread_id = thread.id
            else:
                thread_id = request.session['thread_id']
                
            user_input = request.POST.get('message')
            request.session['user_input'] = user_input

            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"[Ignore but remember this context for this user then answer the response: business name={user_settings['business_name']}, business description={user_settings['business_description']}, social_media_platforms={social_media_platforms}]" + user_input
            )
            run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
            request.session['run_id'] = run.id

            # ---------------------------------------------------------------------- #
            return JsonResponse({'status': 'pending', 'thread_id': thread_id, 'run_id': run.id})
        else:
            return JsonResponse({'error': 'Please Add A Payment Method To Continue.'}, status=400)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

def get_chat(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        except firestore.NotFound:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        pass
    
    except:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    # ---------------------------------------------------------------------- #
    
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if user_settings['isSubscriber']:
            assistant_id = assistant_ids.get('elaine')
            assistant = client.beta.assistants.retrieve(assistant_id)

            user_input = request.session.get('user_input')
            all_messages = request.session.get('all_messages', [{'role': 'bot', 'content': 'How can I help you?'}])
            thread_id = request.session.get('thread_id')
            run_id = request.session.get('run_id')
        
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == 'completed':
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                all_messages.append({'role': 'user', 'content': user_input})
                if messages:
                    messages_list = messages.data
                    if messages_list:
                        last_message_content = messages_list[0].content[0].text.value
                        # formatted_message = format_message(last_message_content)
                        formatted_message = last_message_content
                        all_messages.append({'role': 'bot', 'content': formatted_message})
                        request.session['last_message'] = formatted_message

                request.session['all_messages'] = all_messages

                firestore_data = {'images_generated': user_settings['images_generated'] + 0.1}
                user_settings_ref.set(firestore_data, merge=True)

                return JsonResponse({
                    'all_messages': all_messages,
                    'botMessage': formatted_message,
                    'status': 'completed'
                })
            else:
                return JsonResponse({'status': 'pending'})
        else:
            return JsonResponse({'error': 'Please Add A Payment Method To Continue.'}, status=400)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

def clear_chat(request):
    keys_to_clear = [
        'thread_id', 'run_id', 'user_input', 'all_messages'
    ]

    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    return JsonResponse({'success': 'cleared'})

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
    file_name = 'feadlio.png'
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
                isLogo = request.session.get('isLogo', False)
                context = {
                    'user_settings': user_settings,
                    'user_id': user_id,
                    'isLogo': isLogo,
                    'success': "You're request was sent! We will get back to you with an email shortly.",
                }
            except Exception as e:
                isLogo = request.session.get('isLogo', False)
                context = {
                    'user_settings': user_settings,
                    'user_id': user_id,
                    'isLogo': isLogo,
                    'error': "There was an error with your request. Please wait a moment and try again.",
                }
            
            return render(request, 'ad_manager.html', context)

        elif form_name == 'formImg':
            isLogo = request.POST.get('isLogo', False)
            request.session['isLogo'] = isLogo
            ad_image_url = create_call_to_action(isLogo, logo_path, biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, ads_folder_path, num_ad)
            if num_ad <= 5:
                num_ad += 1
        else:
            isLogo = request.POST.get('isLogo', False)
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
        
    isLogo = request.session.get('isLogo', False)
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
    video_folder_path = f'video_library/'

    try:
        biz = user_settings['business_description']
        biz_name = user_settings['business_name']
        color = user_settings['brand_color']
    except (TypeError, KeyError):
        return redirect('login')
    try:
        logo_path = user_settings['logo']
    except (TypeError, KeyError):
        logo_path = None
    try:
        num_post = int(user_settings['num_post'])
    except (TypeError, KeyError):
        num_post = 1
    if request.session.get('tags') != ['']:
        tags = request.session.get('tags')
    else:
        try:
            tags = ast.literal_eval(user_settings['tags'])
        except (TypeError, KeyError):
            tags = ''

    selected_option = request.session.get('selected_option', 'up')
    isLogo = request.session.get('isLogo', False)

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if user_settings['isSubscriber']:
            # -------------- CAPTIONS --------------- #
            if form_name == 'formCaption1':
                if selected_option == "text":
                    post = create_text_post('facebook', biz, biz_name)
                elif selected_option == "ad":
                    post = create_ad_copy(biz, biz_name)
                else:
                    post = create_caption(biz, biz_name)
                firestore_data = {'next_caption': post}
                url = user_settings['next_image_url']
                user_settings_ref.set(firestore_data, merge=True)
                return redirect('post_creator')
            # -------------- DOWNLOAD --------------- #
            if form_name == 'formDownload':
                url = user_settings['next_image_url']
                parsed_url = urlparse(url)
                if parsed_url.netloc == 'storage.googleapis.com':
                    parts = parsed_url.path.strip('/').split('/')
                    bucket_name = parts[0]
                    object_name = '/'.join(parts[1:])
                else:
                    messages.error(request, 'Invalid Google Cloud Storage URL')
                    return redirect('post_creator')
                
                storage_client = storage.Client()
                bucket_name = bucket_name
                blob_name = object_name
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename("downloaded_image.jpg")
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()

                return redirect('post_creator')
            # -------------- SCHEDULE --------------- #
            elif form_name == 'formPostSchedule':
                timestamps = [
                    "T21:00:00",
                    "T21:15:00",
                    "T21:30:00",
                    "T22:00:00",
                    "T22:15:00",
                    "T22:30:00",
                    "T23:00:00",
                    "T23:15:00",
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
                    url = None
                    post_type = 'text'
                else:
                    post_type = "image"
                    url = reupload_gcs_image(request.POST.get('url'), "scheduled_image_library")
                event_id = uuid.uuid4()
                eid = str(event_id)
                eventDocRef = user_settings_ref.collection('events').document(eid)
                timestamp = new_date + random.choice(timestamps)
                start_time = datetime.fromisoformat(timestamp)

                facebook_checked = request.POST.get('facebook_visible', 'false') == 'true'
                instagram_checked = request.POST.get('instagram_visible', 'false') == 'true'
                linkedin_checked = request.POST.get('linkedin_visible', 'false') == 'true'

                socials = [platform for platform, checked in [
                    ('facebook', facebook_checked),
                    ('instagram', instagram_checked),
                    ('linkedin', linkedin_checked)
                ] if checked]

                event_data = {
                    'eid': eid,
                    'start': start_time,
                    'image_url': url,
                    'caption': post,
                    'className': 'bg-warning',
                    'socials': socials,
                    'type' : post_type,
                    'status': 'pending',
                    'firebase_id_token': request.session.get('firebase_id_token')
                }
                eventDocRef.set(event_data, merge=True)
                firestore_data = {'next_caption': post}
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                messages.success(request, 'Post has been successfully uploaded to the schedule!')
                return redirect('post_creator')
            # -------------- POST --------------- #
            elif form_name == 'formPostLibrary':
                user_image_folder_path = f'user_image_library/'
                image_url = request.POST.get('url', None)
                if image_url:
                    image_url = image_url.replace("'", '"')
                    url = reupload_gcs_image(image_url, user_image_folder_path)
                    image_tags = json.loads(user_settings.get('image_tags', '[]'))
                    image_tags.append(url)
                    image_tags_string = json.dumps(image_tags)
                    firestore_data = {
                        'image_tags': image_tags_string,
                    }
                    user_settings_ref.set(firestore_data, merge=True)
                    messages.success(request, 'Image has been added to your library!')
                    return redirect('post_creator')
            # -------------- POST --------------- #
            elif form_name == 'formPostFeed':
                caption = request.POST.get('edited_caption', '')
                image_url = request.POST.get('url', '')
                lastType = user_settings['lastType']

                facebook_checked = request.POST.get('facebook_visible', 'false') == 'true'
                instagram_checked = request.POST.get('instagram_visible', 'false') == 'true'
                linkedin_checked = request.POST.get('linkedin_visible', 'false') == 'true'

                num_sent = user_settings.get('num_sent', 0)
                max_sent = global_variables.get('max_sent', 5)

                if datetime.now() - user_settings.get('last_reset_time', datetime.now() - timedelta(days=1)) > timedelta(days=1):
                    firestore_data = {'num_sent': 0, 'last_reset_time': datetime.now() }
                    user_settings_ref.set(firestore_data, merge=True)
                    
                if user_settings.get('num_sent', 0) < max_sent or user_settings.get('admin', False):                 
                    try:
                        isAllPosted = False
                        if lastType == 'text' or image_url == '':
                            if facebook_checked:
                                try:
                                    page_id = user_settings['facebook_page_id']
                                    facebook_page_token = user_settings['facebook_page_token']
                                    post_text_to_facebook_page_feed(caption, page_id, facebook_page_token)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Facebook access token has expired. Please re-link your account.')
                                        firestore_data = {'isFacebook': False, 'facebook_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Facebook: {error_message}")

                            if linkedin_checked:
                                try:
                                    page_id = user_settings['linkedin_id']
                                    access_token = user_settings['linkedin_token']
                                    post_text_to_linkedin(access_token, page_id, caption)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Linkedin access token has expired. Please re-link your account.')
                                        firestore_data = {'isLinkedin': False, 'linkedin_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Linkedin: {error_message}")

                        elif lastType == 'video':
                            if facebook_checked:
                                try:
                                    page_id = user_settings['facebook_page_id']
                                    facebook_page_token = user_settings['facebook_page_token']
                                    post_video_to_facebook_page_feed(caption, image_url, page_id, facebook_page_token)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Facebook access token has expired. Please re-link your account.')
                                        firestore_data = {'isFacebook': False, 'facebook_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Facebook: {error_message}")

                            if instagram_checked:
                                try:
                                    instagram_user_id = user_settings['instagram_user_id']
                                    access_token = user_settings['instagram_token']
                                    post_video_to_instagram(access_token, image_url, caption, instagram_user_id)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Instagram access token has expired. Please re-link your account.')
                                        firestore_data = {'isInstagram': False, 'instagram_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Instagram: {error_message}")
                        else:
                            if facebook_checked:
                                try:
                                    page_id = user_settings['facebook_page_id']
                                    facebook_page_token = user_settings['facebook_page_token']
                                    post_to_facebook_page_feed(caption, image_url, page_id, facebook_page_token)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Facebook access token has expired. Please re-link your account.')
                                        firestore_data = {'isFacebook': False, 'facebook_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Facebook: {error_message}")

                            if instagram_checked:
                                try:
                                    instagram_user_id = user_settings['instagram_user_id']
                                    access_token = user_settings['instagram_token']
                                    post_to_instagram(access_token, image_url, caption, instagram_user_id)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Instagram access token has expired. Please re-link your account.')
                                        firestore_data = {'isInstagram': False, 'instagram_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Instagram: {error_message}")

                            if linkedin_checked:
                                try:
                                    access_token = user_settings['linkedin_token']
                                    page_id = user_settings['linkedin_id']
                                    post_to_linkedin(caption, image_url, access_token, page_id)
                                    num_sent += 1
                                    firestore_data = {'num_sent': num_sent}
                                    user_settings_ref.set(firestore_data, merge=True)
                                    isAllPosted = True
                                except Exception as e:
                                    isAllPosted = False
                                    error_message = str(e)
                                    if 'Access token error' in error_message:
                                        print(f"Failed due to access token expiry: {error_message}")
                                        messages.warning(request, 'Your Linkedin access token has expired. Please re-link your account.')
                                        firestore_data = {'isLinkedin': False, 'linkedin_token': None}
                                        user_settings_ref.set(firestore_data, merge=True)
                                    else:
                                        messages.error(request, 'There was an error with your post. Please try again.')
                                        print(f"Failed to post to Linkedin: {error_message}")

                        if isAllPosted:
                            messages.success(request, 'Your post has been successfully uploaded to your Social Media!')
                        

                    except Exception as e:
                        messages.error(request, "An unexpected error occurred. Please try again.")
                
                else:
                    messages.error(request, 'You have reached the maximum number of posts for your subscription. Please upgrade to continue.')  

                return redirect('post_creator')
            # -------------- GENERATE --------------- #

            else:
        # ------------------- Get Selected Post Type --------------------------- #
                selected_option = request.POST.get('selected_post_type')
                request.session['selected_option'] = selected_option
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

                if images_generated < total_allowed_images or user_settings.get('admin', False):
                    images_generated = images_generated + 0.6
                    user_settings_ref.update({
                        'images_generated': images_generated,
                    })

                    if images_generated >= total_allowed_images:
                        cooldown_duration = timedelta(days=global_variables['cooldown_duration'])
                        cooldown_expiry = datetime.now() + cooldown_duration
                        
                    if selected_option == 'up':
                        progress = 100
                        image = request.FILES.get('file')
                        file_extension = image.name.split('.')[-1].lower()
                        isLogo = request.POST.get('isLogo', False)
                        try:
                            if file_extension not in ['jpg', 'jpeg', 'png', 'mp4', 'mov']:
                                messages.error(request, 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png, .mp4, .mov')
                                return redirect('post_creator')

                            try: 
                                if file_extension in ['mp4', 'avi', 'mov']:
                                    url = upload_video_to_google(image, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, video_folder_path, file_extension)
                                    selected_option = 'video'
                                else:
                                    img = create_upload(image, logo_path, isLogo)
                                    url = upload_jpg_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('post_creator')
                        except:
                            messages.error(request, 'No image was uploaded or there was an error. Please try again.')
                            return redirect('post_creator')
                        
                    elif selected_option == 'text':
                        progress = 100
                        select = request.POST.get('text-platform')
                        try:
                            post = create_text_post(select, biz, biz_name)
                            url = None
                        except:
                            messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                            return redirect('post_creator')

                    elif selected_option == 'photo':
                        progress = 0
                        img_url = request.POST.get('selected_img_url', 'None')
                        if img_url != 'None':
                            progress = 95
                            url = img_url
                        else:
                            entered_tags = request.POST.get('tags')
                            tags = entered_tags.split(',')
                            request.session['tags'] = tags
                            key = tags
                            prompt_string = create_stock_image_description(key)
                            url = ''
                            try:
                                payload = {
                                    "prompt": prompt_string, 
                                    "uid": user_id, 
                                    "dimensions": "1024x1024", 
                                    "number": 1
                                }
                                enqueue_task(payload, settings.GS_IMAGE_QUEUE_NAME, settings.GS_DALLE3)
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('post_creator')
                        
                    elif selected_option == 'graphic':
                        key = request.POST.get('ai-description')
                        request.session['key'] = key
                        img_url = request.POST.get('selected_img_url', 'None')
                        if img_url == 'None':
                            prompt_string = create_background_image_description(key)
                            payload = {
                                "prompt": prompt_string, 
                                "uid": user_id, 
                                "dimensions": "1024x1024", 
                                "number": 1
                            }
                            enqueue_task(payload, settings.GS_IMAGE_QUEUE_NAME, settings.GS_DALLE3)
                            url = ''
                            progress = 0
                        else:
                            try:
                                progress = 95
                                url = img_url
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('post_creator')

                    elif selected_option == 'ad':
                        key = request.POST.get('ad-description')
                        request.session['key'] = key
                        img_url = request.POST.get('selected_img_url', 'None')
                        if img_url == 'None':
                            try:
                                prompt_string = create_background_image_description(key)
                                payload = {
                                    "prompt": prompt_string, 
                                    "uid": user_id, 
                                    "dimensions": "1024x1024", 
                                    "number": 1
                                }
                                enqueue_task(payload, settings.GS_IMAGE_QUEUE_NAME, settings.GS_DALLE3)
                                progress = 0
                                url = ''
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('post_creator')
                        else:
                            try:
                                progress = 95
                                url = img_url
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('post_creator')
            
                    try:
                        last_image_url = user_settings['next_image_url']
                        last_caption = user_settings['next_caption']
                    except (TypeError, KeyError):
                        last_image_url = None
                        last_caption = None

                    if selected_option != "text":
                        if selected_option == "ad":
                            post = create_ad_copy(key, biz_name)
                        else:
                            post = create_caption(biz, biz_name)
                else:
                    messages.error(request, 'Our generators need time to cooldown. You can check the progress in the Account Settings Tab.')
                    return redirect('post_creator')

                try:
                    if "user_image_library" not in user_settings['last_image_url']:
                        delete_from_google(user_settings['last_image_url'], settings.GS_CREDENTIALS)
                except:
                    pass
                    
                firestore_data = {
                    'last_image_url': last_image_url,
                    'last_caption': last_caption,
                    'next_image_url': url,
                    'next_caption': post,
                    'lastType' : selected_option,
                    'num_post': num_post,
                    'cooldown_expiry': cooldown_expiry,
                    'images_generated': images_generated,
                    'progress': progress
                }
            print(progress)
            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            return redirect('post_creator')
        else:
            messages.error(request, 'We are here to help your business. Our generators are in high demand and accrue a cost. Please subscribe to utilize our amazing app!')
            return redirect('post_creator')
        
    context = {'user_id': user_id, 'user_settings': user_settings, 'selected_option': selected_option, 'isLogo': isLogo, 'tags': json.dumps(user_settings.get('image_tags'))}
    return render(request, 'post_creator.html', context)

def add_graphics(request):
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
            return JsonResponse({'error': 'firestore.NotFound'}, status=400)
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return JsonResponse({'error': 'Invalid login'}, status=400)
    # ---------------------------------------------------------------------- #

    try:
        biz = user_settings['business_description']
        biz_name = user_settings['business_name']
        color = user_settings['brand_color']
    except (TypeError, KeyError):
        return JsonResponse({'error': 'Error fetching user info.'})
    
    if request.session.get('tags') != ['']:
        tags = request.session.get('tags')
    else:
        try:
            tags = ast.literal_eval(user_settings['tags'])
        except (TypeError, KeyError):
            tags = ''

    logo_path = user_settings.get('logo', None)
    isLogo = user_settings.get('isLogo', False)
    selected_option = user_settings.get('lastType', False)
    progress = user_settings.get('progress', 100)
    key = request.session.get('key', biz)
    if request.method == 'POST':
        if progress < 100:
            print('ran')
            next_image_url = user_settings.get('next_image_url')
            if next_image_url == 'None':
                return JsonResponse({'error': 'Image response empty.'}, status=400)
            if selected_option == 'graphic':
                random_int = random.randint(global_variables['random_int_min'], global_variables['random_int_max'])
                image_folder_path = f'graphic_image_library/'
                color = user_settings['brand_color']
                secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
                img = create_call_to_action(biz, biz_name, color, secondary_colors, next_image_url, random_int, logo_path, isLogo)
                url = upload_png_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
            elif selected_option == 'ad':
                random_int = random.randint(global_variables['random_ad_int_min'], global_variables['random_ad_int_max'])
                image_folder_path = f'ad_image_library/'
                color = user_settings['brand_color']
                secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
                img = create_ad_creative(key, biz_name, color, secondary_colors, next_image_url, random_int, logo_path, isLogo)
                url = upload_png_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
            elif selected_option == 'photo':
                image_folder_path = f'stock_image_library/'
                if isLogo and logo_path is not None:
                    image_data = add_logo(next_image_url, logo_path)
                else:
                    image_data = download_and_save_image_as_seek(next_image_url)
                url = upload_png_to_google(image_data, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
            else:
                url = next_image_url
            firestore_data = {'next_image_url': url, 'progress': 100}
            user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'url': url})
    return JsonResponse({'status': 'nothing'})

def master_switch(request):
    if request.method == 'POST':
        new_id = request.POST.get('newId')
        if request.session.get('master', False):
            request.session['user_id'] = new_id
            messages.success(request, 'ID has been updated.')
            return redirect('post_creator')
        else:
            messages.error(request, 'It seems like you are not authorized to access this page. Please contact us at https://feadl.io/contact/')
            return redirect('post_creator')
    else:
        messages.error(request, 'Oops! Something went wrong. I am not sure how you got here.')
        return redirect('post_creator')
        
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
            messages.error(request, 'Please try logging in again.')
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

def library(request):
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        logging.info(f"Fetching settings for user {user_id}")
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        
        try:
            user_settings_doc = user_settings_ref.get()
            if user_settings_doc.exists:
                user_settings = user_settings_doc.to_dict()
            else:
                raise firestore.NotFound('User settings document not found.')
            
            global_variables_doc = global_variables_ref.get()
            if global_variables_doc.exists:
                global_variables = global_variables_doc.to_dict()
            else:
                raise firestore.NotFound('Global variables document not found.')
        except firestore.NotFound as e:
            logging.error(str(e))
            messages.error(request, str(e))
            return redirect('login')

    except Exception as e:
        logging.exception("An unexpected error occurred")
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        try:
            form_name = request.POST.get('form')
            logging.info(f"Processing POST request for form {form_name}")
            if form_name == 'image-tags':
                stock_image_folder_path = 'stock_image_library/'
                user_image_folder_path = 'user_image_library/'
                post_image_tags = request.POST.get('imageTags', '')
                image_tags = [item.strip() for item in post_image_tags.split(',')] if post_image_tags else []

                post_image_files = request.FILES.get('file')
                if post_image_files:
                    uploaded_image_url = upload_image_to_library(post_image_files, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, user_image_folder_path)
                    image_tags.append(uploaded_image_url)

                is_generate_stock_images_clicked = request.POST.get('isGenerateStockImagesClicked', 'false') == 'true'
                if is_generate_stock_images_clicked:
                    image_tags = add_stock_tags(user_settings['tags'], image_tags, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, stock_image_folder_path)

                image_tags_string = json.dumps(image_tags).replace("'", '"')
                user_settings_ref.set({'image_tags': image_tags_string}, merge=True)
                messages.success(request, 'Settings Updated.')
                return redirect('library')
        except Exception as e:
            logging.error(f"Failed to update settings: {str(e)}")
            messages.error(request, f"Failed to update settings: {str(e)}")

    # Prepare user settings for rendering
    user_settings_strings = {key: value.isoformat() if isinstance(value, datetime) else value
                             for key, value in (user_settings or {}).items()}
    
    context = {
        'user_settings_json': json.dumps(user_settings_strings),
        'user_settings': user_settings,
        'user_id': user_id
    }
    logging.info("Rendering library page")
    return render(request, 'library.html', context)

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
            messages.error(request, 'Please try logging in again.')
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

            # ------------------ TAGS ---------------#
            if request.POST.get('tags'):
                if request.POST.get('business_description') == user_settings.get('business_description'):
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
                'website': request.POST.get('website'),
                'tags': tags
            }

        elif form_name == 'branding':
            # ------------------ LOGO ---------------#
            try:
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

                firestore_data = {
                    'logo': logo_url
                }
                user_settings_ref.set(firestore_data, merge=True)
            except:
                pass
            # ------------------ COLORS ---------------#

            try:
                def get_color(array, index):
                    try:
                        return array[index]
                    except IndexError:
                        return '#000000'
                
                colors = user_settings.get("secondary_colors", "['#000000', '#000000', '#000000', '#000000']")
                color_array = ast.literal_eval(colors)
                color2 = get_color(color_array, 0)
                color3 = get_color(color_array, 1)
                color4 = get_color(color_array, 2)
                color5 = get_color(color_array, 3)

                if request.POST.get('brand_color') != user_settings['brand_color']:
                    colors = generate_secondary_colors(request.POST.get('brand_color'))
                    color_array = ast.literal_eval(colors)
                
                if request.POST.get('color2') != color2:
                    color_array[0] = convert_color_to_hex(request.POST.get('color2', '#000000'))
                if request.POST.get('color3') != color3:
                    color_array[1] = convert_color_to_hex(request.POST.get('color3', '#000000'))
                if request.POST.get('color4') != color4:
                    color_array[2] = convert_color_to_hex(request.POST.get('color4', '#000000'))
                if request.POST.get('color5') != color5:
                    color_array[3] = convert_color_to_hex(request.POST.get('color5', '#000000'))
                
                colors = str(color_array)
                # ------------------ ------------ ---------------#
                
                firestore_data = {
                    'brand_color': request.POST.get('brand_color'),
                    'secondary_colors': colors
                }
                user_settings_ref.set(firestore_data, merge=True)

            except:
                pass

            try:
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

                user_settings_ref.set(firestore_data, merge=True)
            except:
                pass

        # Save the data to Firestore
        user_settings_ref.set(firestore_data, merge=True)

        messages.success(request, 'Settings Have Been Updated.')
        return redirect('brand_settings')
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

def error500(request):
    return render(request, 'error.html', status=500)

def error404(request, exception):
    return render(request, 'error.html', {}, status=404)

## ------------------ LINKING SOCIALS ------------------------- ##

def all_auth(request):
    if request.method == 'POST':
        form_name = request.POST.get('form')
        state = secrets.token_urlsafe(16)
        redirect_uri = settings.REDIRECT_URI
        # if form_name == 'formLinkedin':
        #     request.session['provider'] = 'linkedin'
        #     auth_url = f'https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={settings.LINKEDIN_CLIENT_ID}&redirect_uri={redirect_uri}&scope=w_member_social openid profile email&state={state}'
        # elif form_name == 'formGoogle':
        #     request.session['provider'] = 'google_business'
        #     AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
        #     CLIENT_ID = settings.GOOGLE_APP_ID
        #     REDIRECT_URI = redirect_uri
        #     SCOPES = ['https://www.googleapis.com/auth/business.manage']
        #     STATE = state
        #     auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
        if form_name == 'formFacebook':
            request.session['provider'] = 'facebook'
            AUTHORIZATION_URL = 'https://www.facebook.com/v13.0/dialog/oauth'
            CLIENT_ID = settings.FACEBOOK_APP_ID
            REDIRECT_URI = redirect_uri
            STATE = state
            SCOPES = [
            'pages_show_list',
            'pages_read_engagement',
            'pages_manage_posts'
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
                messages.error(request, 'Please try logging in again.')
                return redirect('login')
        except AttributeError as e:
            messages.error(request, 'Please try logging in again.')
            return redirect('login')
        
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
            # username = get_linkedin_account_name(access_token)
            firestore_data = {
                f'{provider}_id': user_id,
                f'{provider}_token': access_token,
                f'is{isCheck}': True
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
            short_lived_access_token = data.get('access_token')
            access_token = exchange_short_lived_token_for_long_lived(short_lived_access_token, settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
            facebook_pages_and_groups, has_multiple = get_facebook_pages_and_groups(access_token)
            if has_multiple:
                firestore_data = {
                    f'{provider}_token': access_token,
                    f'is{isCheck}': True,
                }
                user_settings_ref.set(firestore_data, merge=True)
                return render(request, 'page_selection_popup.html', {'pages': facebook_pages_and_groups, 'provider': provider,})
            else:
                facebook_page_id = facebook_pages_and_groups[0]['id'] if facebook_pages_and_groups else None
                facebook_page_token = facebook_pages_and_groups[0]['access_token'] if facebook_pages_and_groups else None
                facebook_page_type = facebook_pages_and_groups[0]['type'] if facebook_pages_and_groups else None
                facebook_page_name = facebook_pages_and_groups[0]['name'] if facebook_pages_and_groups else None
                firestore_data = {
                    f'{provider}_token': access_token,
                    f'{provider}_page_id': facebook_page_id,
                    f'{provider}_page_name': facebook_page_name,
                    f'{provider}_page_token': facebook_page_token,
                    f'{provider}_page_type': facebook_page_type,
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
            # access_token = exchange_short_lived_token_for_long_lived(short_lived_access_token, settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
            facebook_page_ids, has_multiple = get_facebook_pages_and_groups(access_token)
            try:
                for facebook_page_id in facebook_page_ids:
                    instagram_id = get_instagram_user_id(facebook_page_id['id'], access_token)
                    if instagram_id:
                        got_instagram_id = instagram_id
                        got_facebook_page_id = facebook_page_id['id']
            except:
                pass

            if got_instagram_id:
                username = get_instagram_username(got_instagram_id, access_token)
                firestore_data = {
                    f'{provider}_token': access_token,
                    f'{provider}_user_id': got_instagram_id,
                    f'{provider}_facebook_page_id': got_facebook_page_id,
                    f'{provider}_name': username,
                    f'is{isCheck}': True
                }
                user_settings_ref.set(firestore_data, merge=True)
            else:
                messages.error(request, 'Please make sure the instagram account is linked to the selected facebook account.')
                return redirect('brand_settings')
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
    
def process_page_selection(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            
        except firestore.NotFound:
            messages.error(request, 'Please try logging in again.')
            return redirect('login')
    except AttributeError as e:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
    # ---------------------------------------------------------------------- #
    selected_page_id = request.POST.get('pageId')
    provider = request.POST.get('provider')
    page_name = request.POST.get('pageName')
    page_token = request.POST.get('pageToken')
    page_type = request.POST.get('pageType')

    if not selected_page_id:
        messages.error(request, 'Please make sure the instagram account is linkeed to the selected facebook account.')
        return redirect('brand_settings')
    else:
        if provider == 'facebook':
            firestore_data = {
                f'{provider}_page_id': selected_page_id,
                f'{provider}_page_name': page_name,
                f'{provider}_page_token': page_token,
                f'{provider}_page_type': page_type,
            }       
            user_settings_ref.set(firestore_data, merge=True)
            messages.success(request, f"You've successfully logged connected your {provider} account!")
            return redirect('brand_settings')
        else: 
            messages.error(request, 'There was an error connecting your account. Please try again.')
            return redirect('brand_settings')

    
def unlink(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        db = firestore.client()
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            
        except firestore.NotFound:
            messages.error(request, 'There was an error connecting your account. Please try again.')
            return redirect('brand_settings')
    except AttributeError as e:
        messages.error(request, 'There was an error connecting your account. Please try again.')
        return redirect('brand_settings')
    provider = request.POST.get('provider')
    isCheck = request.POST.get('isCheck')
    if provider == 'facebook':
        firestore_data = {
            f'{provider}_token': None,
            f'{provider}_page_id': None,
            f'{provider}_page_name': None,
            f'{provider}_page_token': None,
            f'{provider}_page_type': None,
            f'is{isCheck}': False,
        }    
        user_settings_ref.set(firestore_data, merge=True)
    if provider == 'instagram':
        firestore_data = {
            f'{provider}_token': None,
            f'{provider}_facebook_page_id': None,
            f'{provider}_user_id': None,
            f'{provider}_name': None,
            f'is{isCheck}': False,
        }    
        user_settings_ref.set(firestore_data, merge=True)
    if provider == 'linkedin':
        firestore_data = {
            f'{provider}_token': None,
            f'{provider}_id': None,
            f'{provider}_name': None,
            f'is{isCheck}': False,
        }    
        user_settings_ref.set(firestore_data, merge=True)
    return redirect('brand_settings')
    
def logout_view(request):
    request.session.flush()
    return redirect('index')

## ------------------ STRIPE ------------------------- ##

@csrf_exempt  
def checkout(request):
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
            user_settings = {}
        # ---------------------------------------------------------------------- #
        pass
    except:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
        
    context = {
        'user_settings': user_settings,
        'user_id': user_id,
        'isStripeDev': global_variables['isStripeDev']
    }
    return render(request, 'checkout.html', context)

@csrf_exempt
def success(request):
    messages.success(request, 'Thank you for subscribing to Feadl.io! You have been redirected to the dashboard.')
    # ---------------------------------------------------------------------- #
    return redirect('dashboard')

@csrf_exempt
def cancel(request):
    messages.error(request, 'We were unable to complete your subscription. Please try again.')
    return redirect('dashboard')

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT
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
        uid = session.get("client_reference_id", None)
        id_token = user_login(settings.MASTER_EMAIL, settings.MASTER_PASSWORD)
        decoded_token = auth.verify_id_token(id_token)
        master_id = decoded_token['uid']
        db = firestore.client()

        if event['type'] == 'checkout.session.completed':
            customer_id = event['data']['object']['customer']
            subscription_id = event['data']['object']['subscription']
            if subscription_id:
                user_settings_ref = db.collection('users').document(uid)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                firestore_data = {'customer_id': customer_id, 'subscription_id': subscription_id, 'isSubscriber': True, 'subscription_status': 'Subscribed'}
                user_settings_ref.set(firestore_data, merge=True)
                if user_settings.get('isBusiness', False):
                    new_doc_ref = db.collection('accounts').document(uid)
                    new_doc_ref.set({'name': user_settings['business_name']})
            return JsonResponse({'status': 'Checkout Complete'})
        
        if event['type'] == 'invoice.payment_succeeded':
            customer_id = event['data']['object']['customer']
            docs = (
                db.collection('users')
                .where(filter=FieldFilter("customer_id", "==", customer_id))
                .stream()
            )
            for doc in docs:
                user_id = doc.id
                user_settings_ref = db.collection('users').document(user_id)
                firestore_data = {'subscription_status': 'Invoice Paid'}
                user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'status': 'Invoice Paid'})

        if event['type'] == 'invoice.marked_uncollectible' or event['type'] == 'invoice.payment_action_required' or event['type'] == 'invoice.payment_failed':
            customer_id = event['data']['object']['customer']
            docs = (
                db.collection('users')
                .where(filter=FieldFilter("customer_id", "==", customer_id))
                .stream()
            )
            for doc in docs:
                user_id = doc.id
                user_settings_ref = db.collection('users').document(user_id)
                firestore_data = {'isSubscriber': False, 'subscription_status': 'Payment Failed'}
                user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'status': 'Payment Failed'})
        
        if event['type'] == 'subscription_schedule.canceled' or event['type'] == 'plan.deleted' or event['type'] == 'customer.subscription.deleted':
            customer_id = event['data']['object']['customer']
            docs = (
                db.collection('users')
                .where(filter=FieldFilter("customer_id", "==", customer_id))
                .stream()
            )
            for doc in docs:
                user_id = doc.id
                user_settings_ref = db.collection('users').document(user_id)
                firestore_data = {'isSubscriber': False, 'subscription_status': 'Subscription Canceled'}
                user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'status': 'Subscription Canceled'})
        return JsonResponse({'status': 'nothing'})
        
    except Exception as e:
        return JsonResponse({'error': e})
    # ---------------------------------------------------------------------- #

