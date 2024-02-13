import uuid
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops, ImageOps, ExifTags
from io import BytesIO
import requests
import re
import json
from django.conf import settings
import ast
from google.cloud import storage
from google.oauth2 import service_account
from urllib.parse import urlparse
from google.cloud.storage import Blob
from openai import OpenAI
import threading
import os
from django.templatetags.static import static 
from django.contrib.staticfiles.storage import staticfiles_storage
from .graphic_designer import generate_image_from_params, hex_to_rgb
import base64
from decouple import config
from firebase_admin import firestore, auth, credentials
from .functions import upload_png_to_google, create_call_to_action, create_ad_creative, add_logo, download_and_save_image_as_seek, generate_random_date, reupload_gcs_image
from .post_to_socials import post_to_facebook_page_feed, post_text_to_facebook_page_feed, post_to_instagram, post_to_linkedin, post_to_google_mybusiness, get_instagram_user_id, get_facebook_pages_and_groups, get_instagram_username, post_text_to_linkedin, get_linkedin_account_name, post_video_to_facebook_page_feed, post_video_to_instagram, exchange_short_lived_token_for_long_lived
import random
from django.http import JsonResponse

# FOR DEVELOPMENT
from decouple import config
pixabay_api_key = config('PIXABAY_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

def get_stock_image(query):
    num_results = 50
    random_page = random.randint(1, 10)
    endpoint = f"https://pixabay.com/api/?key={pixabay_api_key}&q={query}&per_page={num_results}&page={random_page}&image_type=photo"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            image_urls = [image_info.get("largeImageURL") for image_info in data.get("hits", [])]
            random_image_url = random.choice(image_urls)

            return random_image_url

    except Exception as e:
        pass

def post_to_feed(image_url, caption, platforms, post_type, user_settings, user_settings_ref, global_variables):

    facebook_checked = user_settings.get('isFacebook', False)
    instagram_checked = user_settings.get('isInstagram', False)
    linkedin_checked = user_settings.get('isLinkedin', False)

    num_sent = user_settings.get('num_sent', 0)
    max_sent = global_variables.get('max_sent', 5)

    if datetime.now() - user_settings.get('last_reset_time', datetime.now() - timedelta(days=1)) > timedelta(days=1):
        firestore_data = {'num_sent': 0, 'last_reset_time': datetime.now() }
        user_settings_ref.set(firestore_data, merge=True)
        
    if user_settings.get('num_sent', 0) < max_sent or user_settings.get('admin', False):  
        isAllPosted = False
        if post_type == 'text' or image_url == '':
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
                        firestore_data = {'isFacebook': False, 'facebook_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
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
                        firestore_data = {'isLinkedin': False, 'linkedin_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
                        print(f"Failed to post to Linkedin: {error_message}")

        elif post_type == 'video':
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
                        firestore_data = {'isFacebook': False, 'facebook_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
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
                        firestore_data = {'isInstagram': False, 'instagram_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
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
                        firestore_data = {'isFacebook': False, 'facebook_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
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
                        firestore_data = {'isInstagram': False, 'instagram_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
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
                        firestore_data = {'isLinkedin': False, 'linkedin_token': None}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
                        print(f"Failed to post to Linkedin: {error_message}")

        if isAllPosted:
            return 'success'

    return None

def schedule_post(url, caption, platforms, date_and_time, user_settings, user_settings_ref, firebase_id_token, post_type):
    timestamps = [
        "T19:00:00",
        "T20:00:00",
        "T21:00:00",
        "T21:15:00",
        "T21:30:00",
        "T22:00:00",
        "T22:15:00",
        "T22:30:00",
        "T23:00:00",
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

    if post_type == 'text':
        url = None
    else:
        url = reupload_gcs_image(url, "scheduled_image_library")

    event_id = uuid.uuid4()
    eid = str(event_id)
    eventDocRef = user_settings_ref.collection('events').document(eid)
    timestamp = new_date + random.choice(timestamps)
    start_time = datetime.fromisoformat(timestamp)

    facebook_checked = user_settings.get('isFacebook', False)
    instagram_checked = user_settings.get('isInstagram', False)
    linkedin_checked = user_settings.get('isLinkedin', False)

    socials = [platform for platform, checked in [
        ('facebook', facebook_checked),
        ('instagram', instagram_checked),
        ('linkedin', linkedin_checked)
    ] if checked]

    event_data = {
        'eid': eid,
        'start': start_time,
        'image_url': url,
        'caption': caption,
        'className': 'bg-warning',
        'socials': socials,
        'type' : post_type,
        'status': 'pending',
        'firebase_id_token': firebase_id_token
    }
    eventDocRef.set(event_data, merge=True)
    firestore_data = {'next_caption': caption}
    user_settings_ref.set(firestore_data, merge=True)
    return event_data

def add_graphics_from_bot(next_image_url, user_settings, user_settings_ref, global_variables, selected_option):
    if not next_image_url or next_image_url == 'None':
        return None
    
    # Extract user settings
    business_name = user_settings.get('business_name')
    business_description = user_settings.get('business_description')
    logo_path = user_settings.get('logo')
    is_logo = user_settings.get('isLogo', False)
    
    # Common variables for image creation
    image_folder_path = f'{selected_option}_image_library/'  # Default path based on option
    color = user_settings.get('brand_color')
    secondary_colors = ast.literal_eval(user_settings.get('secondary_colors', '[]'))
    
    # Process based on the selected option
    if selected_option == 'graphic':
        random_int = random.randint(global_variables['random_int_min'], global_variables['random_int_max'])
        img = create_call_to_action(business_description, business_name, color, secondary_colors, next_image_url, random_int, logo_path, is_logo)
    elif selected_option == 'ad':
        random_int = random.randint(global_variables['random_ad_int_min'], global_variables['random_ad_int_max'])
        img = create_ad_creative(business_description, business_name, color, secondary_colors, next_image_url, random_int, logo_path, is_logo)
    elif selected_option == 'photo':
        if is_logo and logo_path:
            img = add_logo(next_image_url, logo_path)
        else:
            img = download_and_save_image_as_seek(next_image_url)
    else:
        img = download_and_save_image_as_seek(next_image_url)
    url = upload_png_to_google(img, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)
    return url