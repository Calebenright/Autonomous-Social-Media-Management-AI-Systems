from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
import io
from firebase_admin.auth import EmailAlreadyExistsError
from decouple import config
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import requests
import secrets
from app.post_to_socials import *
from website.login import *
from google.cloud import storage, firestore
import random
from django.core.mail import EmailMessage
from app.functions import *
from app.get_images import *
import json
import imghdr
from django.utils import timezone
from google.oauth2 import service_account
from google.auth.transport import requests
from urllib.parse import urlparse
from app.post_to_socials import *
from django.http import JsonResponse
from app.functions import *
from firebase_admin import firestore, auth
import ast
from app.tasks import enqueue_task, create_queue
from app.upload_article import *
import uuid
import pytz
from django.contrib import messages
import threading
from datetime import datetime, timedelta, timezone

db = firestore.Client(project=config('FIRESTORE_ID'))
bucket_credentials = config('GS_CREDENTIALS')
bucket_name = config('GS_BUCKET_NAME')
credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
client = storage.Client(project=credentials.project_id, credentials=credentials)

def social_media(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            global_variables_doc = global_variables_ref.get()
            global_variables = global_variables_doc.to_dict()
            elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
            elaine_settings = (elaine_doc_ref.get().to_dict() or []) if elaine_doc_ref.get().exists else []

        except:
            messages.error(request, 'Please try logging in again.')
            return redirect('login')
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'postToSocials':
            if user_settings.get('isSubscriber'):
                post_to_social_feed(request, user_settings, user_settings_ref, 'social_media')
                return redirect('service:social_media')
            else:
                messages.error(request, 'Please upgrade to the Unlimited plan to post directly to your social medias.')
                return redirect('service:social_media')
        elif form_name == 'formCheckout':
            firestore_data = {
                'isPlan': True,
            }
            user_settings_ref.set(firestore_data, merge=True)

            if user_settings.get('isSubscriber'):
                return redirect('service:checkout')
            return redirect('service:checkout')
        elif form_name == 'formLibrary':
            firestore_data = {
                'isLibrary': True,
            }
            user_settings_ref.set(firestore_data, merge=True)
            return redirect('service:library')
        elif form_name == 'elaine-settings':
            isElaineEmail = request.POST.get('isElaineEmail') == "on"
            
            elaine_data = {
                'isElaineEmail': isElaineEmail,
                'ElaineEmail': request.POST.get('ElaineEmail'),
                'posts_per_week': int(request.POST.get('posts_per_week', 0)),
            }

            elaine_doc_ref.set(elaine_data, merge=True)

            messages.success(request, 'Settings have been successfully updated!')
            return redirect('service:social_media')
        
    try:
        if user_settings.get('service_ftue', '0') == '1':
            return redirect('service:ftue')
        
        if user_settings.get('service_ftue', '0') == '3':
            return redirect('service:choose_images')
        
        if not user_settings.get('isSubscriber', False):
            return redirect('service:checkout')
    except:
        return redirect('service:getting_started')
    
    image_tags_num = len(json.loads(user_settings.get('image_tags', '[]')))
    
    context = {
        'image_tags_num': image_tags_num,
        'user_settings': user_settings,
        'elaine_settings': elaine_settings,
        'user_id' : user_id,
    }
    return render(request, "social_media.html", context)

def ftue(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
        elaine_settings = (elaine_doc_ref.get().to_dict() or []) if elaine_doc_ref.get().exists else []
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'formFtue2':
            email = user_settings.get('email')
            business_name = user_settings.get('business_name')
            business_description = user_settings.get('business_description')
            lead_ref = db.collection('service').document(email)
            lead_ref.set({'leadPriority': 3, 'user_id': user_id}, merge=True)
            user_settings_ref.set({'service_ftue': '2', 'ftue': True}, merge=True)
            email_template("New user has submitted FTUE", f"User {email} has submitted their FTUE form.\nBusiness Name: {business_name}\nBusiness Description: {business_description}")
            messages.success(request, 'We are creating your posts now! Please select a plan to continue.')
            return redirect('service:ftue')
        
    if user_settings.get('service_ftue', '0') == '1':
        render_template = "ftue_2.html"
    elif user_settings.get('service_ftue', '0') == '2':
        return redirect('service:checkout')
    elif user_settings.get('service_ftue', '0') == '3':
        return redirect('service:choose_images')
    else:
        return redirect('service:social_media')

    user_settings_strings = {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in user_settings.items()
    }

    context = {
        'user_settings': user_settings,
        'user_settings_json': json.dumps(user_settings_strings),
        'elaine_settings': elaine_settings,
        'user_id' : user_id,
    }
    return render(request, render_template, context)

def choose_images(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user_settings_ref = db.collection('users').document(user_id)
        elaine_ref = db.collection('users').document(user_id).collection('agents').document('elaine')
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        selected_images = json.loads(request.POST.get('selectedImages', '[]'))
        payload = {
            "uid": user_id,
            "selected_images": selected_images
        }
        create_queue(user_id)
        enqueue_task(payload, user_id,  config("GS_CHOOSE_IMAGES"))
        user_settings_data = {'service_ftue': '0', 'isFtue': False, 'isAgency': True, 'agency_id': config("AGENCY_MASTER_ID"), }
        user_settings_ref.set(user_settings_data, merge=True)
        elaine_data = {'isElaineEmail': True, 'isElaineOn': True}
        elaine_ref.set(elaine_data, merge=True)
        return redirect('service:social_media')
    
    context = {
        'user_settings': user_settings,
        'user_id' : user_id
    }

    return render(request, 'choose_images.html', context)


def needs_images(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user_settings_ref = db.collection('users').document(user_id)
        elaine_ref = db.collection('users').document(user_id).collection('agents').document('elaine')
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    if request.method == 'POST':
        try:
            get_library_content(user_id)
        except Exception as e:
            print(f"Failed to update settings: {str(e)}")
        user_settings_ref.set({'service_ftue': '3', 'needs_images': False}, merge=True)
    
    return redirect('service:social_media')
    
def settings(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        elaine_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()
        elaine_doc = elaine_ref.get()
        elaine_settings = elaine_doc.to_dict()
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login')
    # ---------------------------------------------------------------------- #

    try:
        generated_images = user_settings['images_generated']
        total_allowed_images = global_variables['total_allowed_images']
        progress_ratio = generated_images / total_allowed_images
        progress_percentage = int(progress_ratio * 100)
        cooldown = min(100, max(0, progress_percentage))

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
                'business_name': request.POST.get('business_name', '').strip(),
                'business_description': request.POST.get('business_description', '').strip(),
                'website': request.POST.get('website', '').strip(),
                'tags': tags
            }

        elif form_name == 'user-settings':
            firstName = request.POST.get('firstName')
            lastName = request.POST.get('lastName')
            phone = request.POST.get('phone')
            website = request.POST.get('website')
            address1 = request.POST.get('address1')

            ElaineTimezone = request.POST.get('ElaineTimezone')
            elaine_data = {'ElaineTimezone': ElaineTimezone}
            elaine_ref.set(elaine_data, merge=True)

            firestore_data = {
                'firstName': firstName,
                'lastName': lastName,
                'phone': phone,
                'website': website,
                'address1': address1
            }
        elif form_name == 'branding':
            # ------------------ LOGO ---------------#
            try:
                logo = request.FILES.get('logo')
                if logo:
                    try:
                        delete_from_google(user_settings['logo'],  config("GS_CREDENTIALS"))
                    except:
                        pass
                    credentials = service_account.Credentials.from_service_account_file( config("GS_CREDENTIALS"))
                    storage_client = storage.Client(project=credentials.project_id, credentials=credentials)
                    bucket = storage_client.bucket( config("GS_BUCKET_NAME"))
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
                    'brand_color': all_color_to_hex(request.POST.get('brand_color')),
                    'secondary_colors': colors
                }
                user_settings_ref.set(firestore_data, merge=True)

            except:
                pass

            try:
                pfp = request.FILES.get('pfp')
                if pfp:
                    try:
                        delete_from_google(user_settings['pfp'],  config("GS_CREDENTIALS"))
                    except:
                        pass
                    credentials = service_account.Credentials.from_service_account_file( config("GS_CREDENTIALS"))
                    storage_client = storage.Client(project=credentials.project_id, credentials=credentials)
                    bucket = storage_client.bucket( config("GS_BUCKET_NAME"))
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

        user_settings_ref.set(firestore_data, merge=True)

        messages.success(request, 'Settings Have Been Updated.')
        return redirect('service:settings')
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
        'elaine_settings': elaine_settings,
        'global_variables': global_variables,
        'user_id' : user_id,
        'cooldown': cooldown
    }
    return render(request, 'settings.html', context)

def content_creator(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
        try:
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            global_variables_doc = global_variables_ref.get()
            global_variables = global_variables_doc.to_dict()
            elaine_doc = elaine_doc_ref.get()
            elaine_settings = elaine_doc.to_dict()
        except firestore.NotFound:
            return redirect('login')
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #

    image_folder_path = f'user_folders/{user_id}/image_posts'
    video_folder_path = f'user_folders/{user_id}/video_library/'

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
    if request.session.get('tags') != ['']:
        tags = request.session.get('tags')
    else:
        try:
            tags = ast.literal_eval(user_settings['tags'])
        except (TypeError, KeyError):
            tags = ''

    selected_option = request.session.get('selected_option', 'up')
    isLogo = request.session.get('isLogo', False)
    isSubscriber = user_settings.get('isSubscriber')
    isAdmin = user_settings.get('admin', False)
    isUnlimited = user_settings.get('isUnlimited', False)

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if user_id:
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
                return redirect('service:content_creator')
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
                    return redirect('service:content_creator')
                
                storage_client = storage.Client()
                bucket_name = bucket_name
                blob_name = object_name
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename("downloaded_image.jpg")
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()

                return redirect('service:content_creator')
            # -------------- SERVICE DOWNLOAD --------------- #
            if form_name == 'formServiceDownload':
                url = user_settings['next_image_url']
                parsed_url = urlparse(url)
                if parsed_url.netloc == 'storage.googleapis.com':
                    parts = parsed_url.path.strip('/').split('/')
                    bucket_name = parts[0]
                    object_name = '/'.join(parts[1:])
                else:
                    messages.error(request, 'Invalid Google Cloud Storage URL')
                    return redirect('service:social_media')
                
                storage_client = storage.Client()
                bucket_name = bucket_name
                blob_name = object_name
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename("downloaded_image.jpg")

                return redirect('service:social_media')
            # -------------- SCHEDULE --------------- #
            elif form_name == 'formPostSchedule':
                elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
                elaine_doc = elaine_doc_ref.get()
                elaine_settings = elaine_doc.to_dict()
                
                existing_events = user_settings_ref.collection('events').order_by('start').stream()
                existing_event_times = []
                for event in existing_events:
                    event_data = event.to_dict()
                    if 'start' in event_data:
                        existing_event_times.append(event_data['start'])
                        
                post = request.POST.get('edited_caption', '')

                if user_settings['lastType'] == 'text':
                    url = None
                    post_type = 'text'
                else:
                    post_type = "image"
                    url = reupload_gcs_image(request.POST.get('url'), f"user_folders/{user_id}/scheduled_image_library/")

                event_id = uuid.uuid4()
                eid = str(event_id)
                eventDocRef = user_settings_ref.collection('events').document(eid)

                facebook_checked = request.POST.get('facebook_visible', 'false') == 'true'
                instagram_checked = request.POST.get('instagram_visible', 'false') == 'true'

                socials = [platform for platform, checked in [
                    ('facebook', facebook_checked),
                    ('instagram', instagram_checked)
                ] if checked]

                if not socials:
                    messages.error(request, 'Please select at least one social media platform.')
                    return redirect('service:content_creator')

                next_optimal_day = find_next_optimal_day_for_new_post(existing_event_times)
                next_optimal_day_name = next_optimal_day.strftime('%A').lower()
                analog_time = get_best_posting_times(next_optimal_day_name, random.choice(socials))
                optimal_analog_time = convert_optimal_posting_time(analog_time, elaine_settings.get('ElaineTimezone'))
                optimal_timestamp = convert_analog_to_timestamp(optimal_analog_time)
                parsed_time = datetime.strptime(optimal_timestamp[1:], "%H:%M:%S").time()
                start_time = datetime.combine(next_optimal_day, parsed_time)

                event_data = {
                    'eid': eid,
                    'start': start_time,
                    'image_url': url,
                    'caption': post,
                    'className': 'bg-warning',
                    'socials': socials,
                    'type' : post_type,
                    'status': 'pending'
                }
                eventDocRef.set(event_data, merge=True)
                firestore_data = {'next_caption': post}
                user_settings_ref.set(firestore_data, merge=True)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                messages.success(request, 'Post has been successfully uploaded to the schedule!')
                return redirect('service:content_creator')
            # -------------- POST --------------- #
            elif form_name == 'formPostLibrary':
                library_folder_path = f'user_folders/{user_id}/image_posts/'
                image_url = request.POST.get('url', None)
                if image_url:
                    image_url = image_url.replace("'", '"')
                    url = reupload_gcs_image(image_url, library_folder_path)
                    image_tags = json.loads(user_settings.get('image_tags', '[]'))
                    image_tags.append(url)
                    image_tags_string = json.dumps(image_tags)
                    firestore_data = {
                        'image_tags': image_tags_string,
                    }
                    user_settings_ref.set(firestore_data, merge=True)
                    messages.success(request, 'Image has been added to your library!')
                    return redirect('service:content_creator')
            # -------------- POST --------------- #
            elif form_name == 'formPostFeed':
                caption = request.POST.get('edited_caption', '')
                image_url = request.POST.get('url', '')
                lastType = user_settings['lastType']

                facebook_checked = request.POST.get('facebook_visible', 'false') == 'true'
                instagram_checked = request.POST.get('instagram_visible', 'false') == 'true'

                socials = [platform for platform, checked in [
                    ('facebook', facebook_checked),
                    ('instagram', instagram_checked)
                ] if checked]

                if not socials:
                    messages.error(request, 'Please select at least one social media platform.')
                    return redirect('service:content_creator')

                linkedin_checked = False

                num_sent = user_settings.get('num_sent', 0)
                max_sent = global_variables.get('max_sent', 5)

                tz = pytz.UTC
                current_time = datetime.now(tz)
                default_reset_time = current_time - timedelta(days=1)

                last_reset_time = user_settings.get('last_reset_time', default_reset_time)

                if current_time - last_reset_time > timedelta(days=1):
                    firestore_data = {'num_sent': 0, 'last_reset_time': current_time}
                    user_settings_ref.set(firestore_data, merge=True)
                    
                if num_sent < max_sent or isAdmin:                 
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
                                    page_type = user_settings['linkedin_type']
                                    post_text_to_linkedin(access_token, page_id, caption, page_type)
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
                                    page_type = user_settings['linkedin_type']
                                    personal_id = user_settings.get('linkedin_personal_id', None)
                                    post_to_linkedin(caption, image_url, access_token, page_id, page_type)
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

                return redirect('service:content_creator')
            # -------------- GENERATE --------------- #

            else:
        # ------------------- Get Selected Post Type --------------------------- #
                selected_option = request.POST.get('selected_post_type')
                request.session['selected_option'] = selected_option
        # ---------------------------------------------------------------------- #

                monthly_allowed_images = global_variables.get('monthly_allowed_images', 100)
                monthly_images_generated = user_settings.get('monthly_images_generated', 0)
                total_allowed_images = global_variables.get('total_allowed_images', 20)
                images_generated = user_settings.get('images_generated', 0)
                cooldown_expiry = user_settings.get('cooldown_expiry', datetime.now() + timedelta(days=global_variables.get('cooldown_duration', 1)))
                add_credits = 0

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

                if monthly_images_generated < monthly_allowed_images or isAdmin or isUnlimited:

                    if images_generated >= total_allowed_images and not isAdmin and not isUnlimited:
                        messages.error(request, 'You have reached the maximum number of daily images for your subscription. Please upgrade to continue or come back tomorrow.')
                        return redirect('service:content_creator')
                    
                    if selected_option == 'up':
                        progress = 100
                        image = request.FILES.get('file')
                        file_extension = image.name.split('.')[-1].lower()
                        isLogo = request.POST.get('isLogo', False)

                        if file_extension not in ['jpg', 'jpeg', 'png']:
                            messages.error(request, 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png')
                            return redirect('service:content_creator')

                        try: 
                            if file_extension in ['mp4', 'avi', 'mov']:
                                messages.error(request, 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png')
                                return redirect('service:content_creator')
                                # url = upload_video_to_google(image, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), video_folder_path, file_extension)
                                # selected_option = 'video'
                            else:
                                img = create_upload(image, logo_path, isLogo)
                                url = upload_jpg_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path)
                        except:
                            messages.error(request, 'No image was uploaded or there was an error. Please try again.')
                            return redirect('service:content_creator')
                        
                    elif selected_option == 'text':
                        progress = 100
                        select = request.POST.get('text-platform')
                        add_credits += 0.5

                        try:
                            post = create_text_post(select, biz, biz_name)
                            url = None
                        except:
                            messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                            return redirect('service:content_creator')

                    elif selected_option == 'photo':
                        progress = 0
                        img_url = request.POST.get('selected_img_url', 'None')
                        if img_url == 'None':
                            if isSubscriber:
                                add_credits += 1
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
                                    create_queue(user_id)
                                    enqueue_task(payload, user_id,  config("GS_DALLE3"))
                                except:
                                    messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                    return redirect('service:content_creator')
                            else:
                                messages.error(request, 'Please upgrade to utilize our AI Stock Image Library.')
                                return redirect('service:content_creator')
                            
                        else:
                            add_credits += 0.5
                            progress = 95
                            url = img_url
                        
                    elif selected_option == 'graphic':
                        key = request.POST.get('ai-description')
                        request.session['key'] = key
                        img_url = request.POST.get('selected_img_url', 'None')
                        if img_url == 'None':
                            if isSubscriber:
                                add_credits += 1
                                prompt_string = create_background_image_description(key)
                                payload = {
                                    "prompt": prompt_string, 
                                    "uid": user_id, 
                                    "dimensions": "1024x1024", 
                                    "number": 1
                                }
                                create_queue(user_id)
                                enqueue_task(payload, user_id,  config("GS_DALLE3"))
                                url = ''
                                progress = 0
                            else:
                                messages.error(request, 'Please upgrade to utilize our AI Stock Image Library.')
                                return redirect('service:content_creator')
                        else:
                            add_credits += 0.8
                            try:
                                progress = 95
                                url = img_url
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('service:content_creator')

                    elif selected_option == 'ad':
                        if isSubscriber:
                            key = request.POST.get('ad-description')
                            request.session['key'] = key
                            img_url = request.POST.get('selected_img_url', 'None')
                            if img_url == 'None':
                                add_credits += 1.2
                                prompt_string = create_background_image_description(key)
                                payload = {
                                    "prompt": prompt_string, 
                                    "uid": user_id, 
                                    "dimensions": "1024x1024", 
                                    "number": 1
                                }
                                create_queue(user_id)
                                enqueue_task(payload, user_id,  config("GS_DALLE3"))
                                progress = 0
                                url = ''
                            else:
                                add_credits += 0.9
                                try:
                                    progress = 95
                                    url = img_url
                                except:
                                    messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                    return redirect('service:content_creator')
                        else:
                            messages.error(request, 'Please upgrade to utilize this feature.')
                            return redirect('service:content_creator')
            
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
                    messages.error(request, 'You have reached the maximum number of monthly images for your subscription. Please upgrade to continue or wait until the beginning of the next month.')
                    return redirect('service:content_creator')

                try:
                    if "image_library" not in user_settings['last_image_url']:
                        delete_from_google(user_settings['last_image_url'],  config("GS_CREDENTIALS"))
                except:
                    pass

                images_generated += add_credits
                monthly_images_generated += add_credits
                
                firestore_data = {
                    'last_image_url': last_image_url,
                    'last_caption': last_caption,
                    'next_image_url': url,
                    'next_caption': post,
                    'lastType' : selected_option,
                    'cooldown_expiry': cooldown_expiry,
                    'images_generated': images_generated,
                    'progress': progress
                }

            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            messages.success(request, 'Your graphic is being created!')
            return redirect('service:content_creator')
        else:
            messages.error(request, 'We are here to help your business. Our generators are in high demand and accrue a cost. Please upgrade to utilize our amazing app!')
            return redirect('service:content_creator')
        
    context = {'user_id': user_id, 'user_settings': user_settings, 'elaine_settings': elaine_settings, 'global_variables': global_variables, 'selected_option': selected_option, 'isLogo': isLogo, 'tags': json.dumps(user_settings.get('image_tags'))}
    return render(request, 'content_creator.html', context)

def calendar(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
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

    context = {
        'user_settings': user_settings,
        'user_id': user_id
    }
    return render(request, "calendar.html", context)

def checkout(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
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

    context = {
        'user_settings': user_settings,
        'user_id': user_id
    }

    return render(request, "checkout.html", context)


def advertising_checkout(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
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

    context = {
        'user_settings': user_settings,
        'user_id': user_id
    }

    return render(request, "advertising_checkout.html", context)

def email_template(subject, message):
    from_email = config("EMAIL_HOST_USER")
    recipient_list = [config("INTERNAL_RECIPIENTS")]
    to_admin_email_message = EmailMessage(subject, message, from_email, recipient_list)
    to_admin_email_message.send()

def process_email(request, redirect_success, redirect_fail, template, bname, bdesc, color, selectedImage, selectedPlan, email):
    subject = "FTUE Response!"
    if request.method == 'POST':
        details = {
            'email': email,
            'bname': bname,
            'bdesc': bdesc,
            'color': color,
            'selectedImage': selectedImage,
            'selectedPlan': selectedPlan
        }
        message = 'Email: {email}\nBusiness Name: {bname}\nBusiness Description: {bdesc}\nselectedPlan: {selectedPlan}\nselectedImage: {selectedImage}'.format(**details)
        
        from_email = config("EMAIL_HOST_USER")
        recipient_list = [config("INTERNAL_RECIPIENTS")]
        to_admin_email_message = EmailMessage(subject, message, from_email, recipient_list)
        
        try:
            to_admin_email_message.send()
        except Exception:
            messages.error(request, "There was an error sending your email. Please wait a moment and try again.")
            return redirect(redirect_fail)
        
        suggested_subject = request.POST.get('subject', "Feadl.io - Let's Get Started!")
        suggested_message = f"Your response has been received and one of our social media agents will get back to you soon.\n\nSincerely,\nElaine\n\nElaine | Marketing Agent @ Feadl.io\n407.516.6380\nExperience our platform: https://feadl.io/beta_signup/"

        to_user_email_message = EmailMessage(suggested_subject, suggested_message, from_email, [email])
        
        try:
            to_user_email_message.send()
            db.collection('service').document(email).update({'emailSent': True})

        except Exception as e:
            print(f"An error occurred: {e}")

def download(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
        elaine_settings = (elaine_doc_ref.get().to_dict() or []) if elaine_doc_ref.get().exists else []
        george_settings_ref = db.collection('users').document(user_id).collection('agents').document('george')
        george_settings_doc = george_settings_ref.get()
        george_settings = george_settings_doc.to_dict() if george_settings_doc.exists else {}
        
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #
    if request.method == 'POST':
        form_name = request.POST.get('form')
        print(form_name)
        if form_name == 'smm-download':
            image_number = request.POST.get('imageNum')
            url = elaine_settings.get(f'scheduled_image_{image_number}', '')
            parsed_url = urlparse(url)
            if parsed_url.netloc == 'storage.googleapis.com':
                parts = parsed_url.path.strip('/').split('/')
                bucket_name = parts[0]
                object_name = '/'.join(parts[1:])
            else:
                messages.error(request, 'There was an error downloading the image. Please try again.')
                return redirect('service:social_media')
            print(image_number)
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
        elif form_name == 'graphic-download':
            url = george_settings.get(f'graphic')
            parsed_url = urlparse(url)
            if parsed_url.netloc == 'storage.googleapis.com':
                parts = parsed_url.path.strip('/').split('/')
                bucket_name = parts[0]
                object_name = '/'.join(parts[1:])
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
        else:
            url = user_settings['next_image_url']
            parsed_url = urlparse(url)
            print(parsed_url.netloc)
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
    raise ValueError('Not selected')

def getting_started(request):
    email = request.session.get('email', None)

    if not email:
        return redirect('signup')

    if request.method == 'POST':
        selected_image = request.POST.get('selectedImage', 'Simple')
        if selected_image == 'image1':
            selected_image = 'Graphics'
        else:
            selected_image = 'Simple'
        business_name = request.POST.get('business-name', 'Muscle Up')
        business_description = request.POST.get('business-description', "Muscle Up is a premier body building nutrition course designed to sculpt your physique and elevate your fitness journey. Our program combines cutting-edge training techniques with personalized coaching to help you achieve peak muscle growth, strength, and endurance. We focus on supplements, workout equipment, and excersises.")
        color = request.POST.get('brand-color', '#fcba03')
        if business_description == "":
            business_description = "Muscle Up is a premier body building nutrition course designed to sculpt your physique and elevate your fitness journey. Our program combines cutting-edge training techniques with personalized coaching to help you achieve peak muscle growth, strength, and endurance. We focus on supplements, workout equipment, and excersises."
        if business_name == "":
            business_name = 'Muscle Up'
        try:
            
            lead_ref = db.collection('service').document(email)
            lead_ref.set({
                'selected_image': selected_image,
                'business_name': business_name,
                'business_description': business_description,
                'color': color,
                'leadPriority': 2
            })

        except Exception as e:
            messages.error(request, ("An error occurred: {}".format(e)))
            return redirect('service:getting_started')
        
        return redirect('service:getting_started_success')
    
    context = {'email': email}
    return render(request, "getting_started.html", context)

def getting_started_success(request):
    email = request.session.get('email')
    if request.method == 'POST':
        new_email = request.POST.get('email')
        confirm_email = request.POST.get('confirm_email')
        password = request.POST.get('password')
        if new_email != confirm_email:
            messages.error(request, "Please make sure your emails match.")
            return redirect('service:getting_started_success')
        try:
            user = auth.create_user(email=new_email, password=password)
        except EmailAlreadyExistsError:
            messages.error(request, "User already exists. Please login.")
            return redirect('login')
        
        request.session['user_id'] = user.uid
        
        lead_ref = db.collection('service').document(email)
        lead = lead_ref.get().to_dict()
        business_description = lead.get('business_description')
        business_name = lead.get('business_name')
        brand_color = all_color_to_hex(lead.get('color'))
        colors = generate_secondary_colors(brand_color)
        tags = create_tags(business_description)

        user_ref = db.collection('users').document(user.uid)

        firestore_data = {
            'tags': tags,
            'business_description': business_description,
            'business_name': business_name,
            'brand_color': brand_color,
            'secondary_colors' : colors,
            'agency_id': 'ef6a81bf-6388-4cef-b522-e8fd9c667b0c',
            'isAds': False,
            'isAgency': True,
            'isFtue': True,
            'isSubscriber': False,
            'isAutomated': False,
            'isUnlimited': False,
            'isLogo': False,
            'images_generated': 0,
            'isBusiness': False,
            'monthly_images_generated': 0,
            'progress': 100,
            'admin': False,
            'email': new_email,
            'num_sent': 0,
            'last_reset_time': datetime.now(),
            'trial': 0,
            'service_ftue': '1',
            'leadPriority': 3,
            'signup_date': datetime.now(),
        }
        
        user_ref.set(firestore_data, merge=True)

        lead_ref.update({
            'user_id': user.uid
        })

        elaine_doc_ref = db.collection('users').document(user.uid).collection('agents').document('elaine')

        elaine_data = {
            'isElaineEmail': True,
            'isElaineOn' : False,
            'posts_per_week': 1,
            'text_weight': 35,
            'stock_weight': 50,
            'graphic_weight': 15,
            'combined_weight': 85,
            'ElaineSocialMedias': [],
            'ElainePostType': ["Text Post","Stock Photo Post"],
            'ElaineImageLog': [],
            'ElaineTimezone': 'America/Chicago',
        }

        elaine_doc_ref.set(elaine_data, merge=True)
        
        try:
            get_library_content(user.uid)
        except Exception as e:
            print(f"Failed to update settings: {str(e)}")

        return redirect('service:ftue')

    context = {'email': email}
    return render(request, "getting_started_success.html", context)

def graphic_designer(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user_settings = db.collection('users').document(user_id).get().to_dict()
        george_settings_ref = db.collection('users').document(user_id).collection('agents').document('george')
        george_settings_doc = george_settings_ref.get()
        george_settings = george_settings_doc.to_dict() if george_settings_doc.exists else {}

    except firestore.NotFound:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
    except Exception:
        return redirect('login')
    
    if request.method == 'POST':
        form = request.POST.get('form')
        if form == 'graphic-proposal':
            submit_brief(request)
            brief = request.POST.get('brief')
            george_data = {
                'isLoading': True,
                'brief': brief,
                'progress': 5,
                'message': '',
                'date': datetime.now()
            }
            messages.success(request, 'Brief has been successfully sent.')
        elif form == 'graphic-clear':
            delete_gcs_folder(user_id, 'graphic_proposal')
            george_data = {
                'isLoading': False,
                'brief': '',
            }
            messages.success(request, 'Graphic request has been cleared.')
        
        george_settings_ref.set(george_data, merge=True)
        return redirect('service:graphic_designer')
    
    date = george_settings.get('date', None)
    current_progress = george_settings.get('progress', 5)

    if date:
        now = datetime.now(timezone.utc)

        time_difference = now - date
        elapsed_seconds = time_difference.total_seconds()
        
        five_days_seconds = 5 * 24 * 60 * 60
        
        progress = min(95, (elapsed_seconds / five_days_seconds) * 95) + current_progress
    else:
        progress = 0

    progress = min(progress + current_progress, 95)

    bucket = client.bucket(config("GS_BUCKET_NAME"))
    prefix = f'user_folders/{user_id}/graphic_proposal/'
    thumbnails = list(bucket.list_blobs(prefix=prefix))
    thumbnail_urls = []
    for thumbnail in thumbnails:
        thumbnail_url = f'https://storage.googleapis.com/{bucket.name}/{thumbnail.name}'
        thumbnail_urls.append(thumbnail_url)
        print(thumbnail_url)

    context = {
        'george_settings': george_settings,
        'user_settings': user_settings,
        'user_id': user_id,
        'progress': progress,
        'thumbnails': thumbnail_urls,
    }

    return render(request, "graphic_designer.html", context)

def video_editor(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user_settings = db.collection('users').document(user_id).get().to_dict()
        susan_settings_ref = db.collection('users').document(user_id).collection('agents').document('susan')
        susan_settings_doc = susan_settings_ref.get()
        susan_settings = susan_settings_doc.to_dict() if susan_settings_doc.exists else {}

    except firestore.NotFound:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
    except Exception:
        return redirect('login')
    
    if request.method == 'POST':
        form = request.POST.get('form')
        if form == 'video-proposal':
            submit_brief(request)
            brief = request.POST.get('brief')
            susan_data = {
                'isLoading': True,
                'brief': brief,
                'progress': 5,
                'message': '',
                'date': datetime.now()
            }
            messages.success(request, 'Brief has been successfully sent.')
        elif form == 'video-clear':
            delete_gcs_folder(user_id, 'video_proposal')
            susan_data = {
                'isLoading': False,
                'brief': '',
            }
            messages.success(request, 'Video request has been cleared.')
        
        susan_settings_ref.set(susan_data, merge=True)
        return redirect('service:video_editor')
    
    date = susan_settings.get('date', None)
    current_progress = susan_settings.get('progress', 5)

    if date:
        now = datetime.now(timezone.utc)

        time_difference = now - date
        elapsed_seconds = time_difference.total_seconds()
        
        fourteen_days_seconds = 14 * 24 * 60 * 60
        
        progress = min(95, (elapsed_seconds / fourteen_days_seconds) * 95) + current_progress
    else:
        progress = 0

    progress = min(progress + current_progress, 95)

    bucket = client.bucket(config("GS_BUCKET_NAME"))
    prefix = f'user_folders/{user_id}/video_proposal/'
    thumbnails = list(bucket.list_blobs(prefix=prefix))
    thumbnail_urls = []
    for thumbnail in thumbnails:
        thumbnail_url = f'https://storage.googleapis.com/{bucket.name}/{thumbnail.name}'
        thumbnail_urls.append(thumbnail_url)

    context = {
        'susan_settings': susan_settings,
        'user_settings': user_settings,
        'user_id': user_id,
        'progress': progress,
        'thumbnails': thumbnail_urls,
    }

    return render(request, "video_editor.html", context)


def clips_creator(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        clips_ref = db.collection('users').document(user_id).collection('clips')
        clips_query = clips_ref.stream()

        clips_data = []
        for doc in clips_query:
            clip_dict = doc.to_dict()
            clips_data.append({
                'id': doc.id,
                'created_at': clip_dict.get('created_at'),
                'urls': clip_dict.get('clips', [])
            })
        clips_data = [clip for clip in clips_data if clip['created_at'] is not None]
        clips_data.sort(key=lambda x: x['created_at'], reverse=True)

        print(clips_data)

    except firestore.NotFound:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
    except Exception:
        return redirect('login')
    
    if request.method == 'POST':
        form = request.POST.get('form')
        if form == 'clips':
            if user_settings.get('clip_minutes', 0) > 200:
                messages.error(request, 'You have reached the maximum amount of minutes for the month.')
                return redirect('service:clips_creator')

            file_name = request.POST.get('file_name')
            file_name_without_extension, _ = os.path.splitext(file_name)
            print("Filename: ", file_name_without_extension)
            if not file_name_without_extension:
                messages.error(request, 'Please re-upload the file.')
                return redirect('service:clips_creator')
            get_clips(request)
            url = 'https://feadlio-api-611051344563.us-central1.run.app/url-to-clips'
            payload = {
                "url": f"https://storage.googleapis.com/starter_web_app_bucket/user_folders/{user_id}/clips/uploaded/{file_name_without_extension}.mp4",
                "uid": user_id,
                "name": file_name_without_extension
            }
            user_settings_ref.set({'clip_percent': 1, 'last_clip': datetime.now(timezone.utc)}, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            threading.Thread(target=send_post_request, args=(url, payload)).start()
            messages.success(request, 'Clips are being created!')
        
        elif form == 'clear':
            user_settings_ref.set({'clip_percent': 100}, merge=True)
            messages.success(request, 'Process Cancelled')
        elif form == 'formPostSchedule':
            video_url = request.POST.get('clipUrl')
            access_token = user_settings.get("instagram_token")
            instagram_user_id = user_settings.get("instagram_user_id")
            caption = create_caption(user_settings.get("business_description"), user_settings.get("business_name"))
            
            print("CLIP URL: ", video_url)
            elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
            elaine_doc = elaine_doc_ref.get()
            elaine_settings = elaine_doc.to_dict()
            
            existing_events = user_settings_ref.collection('events').order_by('start').stream()
            existing_event_times = []
            for event in existing_events:
                event_data = event.to_dict()
                if 'start' in event_data:
                    existing_event_times.append(event_data['start'])
                    
            event_id = uuid.uuid4()
            eid = str(event_id)
            eventDocRef = user_settings_ref.collection('events').document(eid)

            socials = ['instagram'] if user_settings.get("isInstagram") else None

            if not socials:
                messages.error(request, 'Please link your instagram account to post.')
                return redirect('service:clips_creator')

            times_array = ["08:00:00", "12:00:00", "15:00:00", "18:00:00"]
            tzone = "America/Chicago"  # Example timezone
            days_to_add = random.randint(1, 7)
            random_date = datetime.now() + timedelta(days=days_to_add)
            
            # Pick a random time from the array
            random_time_str = random.choice(times_array)
            
            # Convert the time string to a datetime object in the specified timezone
            local_tz = pytz.timezone(tzone)
            time_obj = datetime.strptime(random_time_str, "%H:%M:%S").time()
            now = datetime.now(local_tz)
            
            # Combine the random date with the selected time
            start_time = datetime.combine(random_date.date(), time_obj)
            start_time = local_tz.localize(start_time)  # Localize the datetime to the specified timezone

            event_data = {
                'eid': eid,
                'start': start_time,
                'image_url': video_url,
                'caption': caption,
                'className': 'bg-warning',
                'socials': socials,
                'type' : 'reel',
                'access_token' : access_token,
                'instagram_user_id' : instagram_user_id,
                'status': 'pending'
            }
            eventDocRef.set(event_data, merge=True)
            messages.success(request, 'Post has been successfully uploaded to the schedule!')
            return redirect('service:clips_creator')
        
        return redirect('service:clips_creator')
    
    current_time = datetime.now(timezone.utc)
    last_clip = f"{user_settings.get('last_clip', current_time)}"
    firestore_timestamp = datetime.fromisoformat(last_clip)
    time_difference = current_time - firestore_timestamp
    is_time_less = time_difference >= timedelta(hours=3)

    print("LAST: ", last_clip)
    print("current_time: ", current_time)
    print("is_time_less: ", is_time_less)

    context = {
        'clips': clips_data,
        'user_settings': user_settings,
        'user_id': user_id,
        'is_time_less': is_time_less
    }

    return render(request, "clip_creator.html", context)


def website_builder(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()

    except firestore.NotFound:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
    except Exception:
        return redirect('login')
    
    context = {
        'user_settings': user_settings,
        'user_id': user_id,
    }
    return render(request, "website_builder.html", context)

def send_post_request(url, payload):
    requests.post(url, json=payload)

@csrf_exempt
def generate_signed_url(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    if request.method == 'POST':
        bucket = client.bucket(bucket_name)
        folder_name = request.POST.get('folder_name')
        file_name = request.POST.get('file_name')
        request.session['file_name'] = file_name
        request.session['folder_name'] = folder_name
        folder_path = f'user_folders/{user_id}/{folder_name}/'
        filename = folder_path + file_name
        blob = bucket.blob(filename)

        signed_url = blob.generate_signed_url(
            version='v4',
            expiration=600,
            method='PUT',
            content_type='application/octet-stream'
        )

        return JsonResponse({'url': signed_url, 'file_name': file_name})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def submit_brief(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    bucket = client.bucket(bucket_name)
    folder_name = request.POST.get('folder_name')
    folder_path = f'user_folders/{user_id}/{folder_name}/'
    blobs = bucket.list_blobs(prefix=folder_path)
    for blob in blobs:
        print(blob.name)
        blob.make_public()
    
    subject = request.POST.get('subject')
    email = "cjenright10@gmail.com"
    message = f"Hi CJ,\n\nA new request has been sent from: {user_id}\n\nSincerely,\nCJ Bot"
    
    from_email = config("EMAIL_HOST_USER")
    recipient_list = [email]
    send_email = EmailMessage(subject, message, from_email, recipient_list)
    send_email.send()

    redirect_url = request.POST.get('redirect_url')
    return redirect(redirect_url)

@csrf_exempt
def get_clips(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    bucket = client.bucket(bucket_name)
    folder_name = request.POST.get('folder_name')
    folder_path = f'user_folders/{user_id}/{folder_name}/'
    blobs = bucket.list_blobs(prefix=folder_path)
    for blob in blobs:
        print(blob.name)
        blob.make_public()
    
    redirect_url = request.POST.get('redirect_url')
    return redirect(redirect_url)

@csrf_exempt
def make_file_public(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            folder_name = data.get('folder_name')
            file_name = data.get('file_name')
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        bucket = client.bucket(bucket_name)
        folder_path = f'user_folders/{user_id}/{folder_name}/'
        filename = folder_path + file_name
        blob = bucket.blob(filename)

        try:
            blob.make_public()
            return JsonResponse({'success': True, 'public_url': blob.public_url})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def advertising_specialist(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user_settings = db.collection('users').document(user_id).get().to_dict()
        david_settings_ref = db.collection('users').document(user_id).collection('agents').document('david')
        david_settings_doc = david_settings_ref.get()
        david_settings = david_settings_doc.to_dict() if david_settings_doc.exists else {}

    except firestore.NotFound:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
    except Exception:
        return redirect('login')

    if request.method == 'POST':
        form = request.POST.get('form')
        if form == 'ad-proposal':
            submit_brief(request)
            copy = request.POST.get('ad_copy')
            toggleOption = request.POST.get('toggleOption')
            website = request.POST.get('website')
            fbMessage = request.POST.get('fbMessage')
            if website:
                toggleOptionAsset = website
            else:
                toggleOptionAsset = fbMessage
            print(toggleOption, toggleOptionAsset)
            david_data = {
                'isLoading': True,
                'ad_copy': copy,
                'toggleOption': toggleOption,
                'toggleOptionAsset': toggleOptionAsset,
                'message': '',
            }
            messages.success(request, 'Brief has been successfully sent.')
        elif form == 'ad-clear':
            delete_gcs_folder(user_id, 'ad_proposal')
            david_data = {
                'isLoading': False,
                'ad_copy': '',
            }
            messages.success(request, 'Graphic request has been cleared.')
        
        david_settings_ref.set(david_data, merge=True)
        return redirect('service:advertising_specialist')
    
    bucket = client.bucket(config("GS_BUCKET_NAME"))
    prefix = f'user_folders/{user_id}/ad_proposal/'
    thumbnails = list(bucket.list_blobs(prefix=prefix))
    thumbnail_urls = []
    for thumbnail in thumbnails:
        thumbnail_url = f'https://storage.googleapis.com/{bucket.name}/{thumbnail.name}'
        if thumbnail.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            file_type = 'image'
        elif thumbnail.name.lower().endswith(('.mp4', '.webm', '.ogg')):
            file_type = 'video'
        else:
            file_type = 'unknown'
        
        thumbnail_urls.append({'url': thumbnail_url, 'type': file_type})

    analytics = {
        'impressions': {
            'title': 'Impressions',
            'percentage': david_settings.get('impressions', 0),
            'value': david_settings.get('impressions', 0),
            'description': 'Impressions'
        },
        'clicks': {
            'title': 'Clicks',
            'percentage': david_settings.get('clicks', 0),
            'value': david_settings.get('clicks', 0),
            'description': 'Clicks Today'
        },
        'money_spent': {
            'title': 'Ad Credits Spent',
            'percentage': david_settings.get('money_spent', 0),
            'value': f'{david_settings.get("money_spent", 0)}%',
            'description': 'This Month'
        },
        'ctr': {
            'title': 'CTR',
            'percentage': david_settings.get('ctr', 0),
            'value': f'{david_settings.get("ctr", 0)}%',
            'description': 'Conversion Rate'
        }
    }

    context = {
        'david_settings': david_settings,
        'user_settings': user_settings,
        'user_id': user_id,
        'thumbnails': thumbnail_urls,
        'analytics': analytics,
    }

    return render(request, "advertising_specialist.html", context)

def library(request):
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        
        global_variables_ref = db.collection('variables').document('global_variables')
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()

    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        try:
            form_name = request.POST.get('form')
            if form_name == 'image-tags':
                library_folder_path = f'user_folders/{user_id}/image_library/'
                get_old_image_tags = user_settings.get('image_tags', '[]')
                old_image_tags = json.loads(get_old_image_tags)
                old_image_tags = [item.strip() for item in old_image_tags]
                post_image_tags = request.POST.get('imageTags', '')
                image_tags = [item.strip() for item in post_image_tags.split(',')] if post_image_tags else []
                removed_tags = set(old_image_tags) - set(image_tags)
                if removed_tags:
                    delete_library_images_from_gcs(removed_tags, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"))

                post_image_files = request.FILES.get('file')
                if post_image_files:
                    uploaded_image_url = upload_image_to_library(post_image_files, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), library_folder_path)
                    image_tags.append(uploaded_image_url)
                    
                image_tags_string = json.dumps(image_tags).replace("'", '"')
                user_settings_ref.set({'image_tags': image_tags_string}, merge=True)
                messages.success(request, 'Settings Updated.')
                return redirect('service:library')
            if form_name == 'video-tags':
                file_name = request.POST.get('file-name', None)
                if file_name:
                    library_folder_path = f'user_folders/{user_id}/video_library/{file_name}'
                    bucket = client.bucket(bucket_name)
                    blob = bucket.blob(library_folder_path)
                    blob.make_public()
                    url = blob.public_url
                get_old_video_tags = user_settings.get('video_tags', '[]')
                old_video_tags = json.loads(get_old_video_tags)
                old_video_tags = [item.strip() for item in old_video_tags]
                post_video_tags = request.POST.get('videoTags')
                video_tags = [item.strip() for item in post_video_tags.split(',')] if post_video_tags else []
                removed_tags = set(old_video_tags) - set(video_tags)
                if removed_tags:
                    delete_library_images_from_gcs(removed_tags, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"))
                if file_name:
                    video_tags.append(url)
                video_tags_string = json.dumps(video_tags).replace("'", '"')
                user_settings_ref.set({'video_tags': video_tags_string}, merge=True)
                messages.success(request, 'Settings Updated.')
                return redirect('service:library')
        except Exception as e:
            messages.error(request, f"Failed to update settings: {str(e)}")

    # Prepare user settings for rendering
    user_settings_strings = {key: value.isoformat() if isinstance(value, datetime) else value
                             for key, value in (user_settings or {}).items()}
    
    context = {
        'user_settings_json': json.dumps(user_settings_strings),
        'user_settings': user_settings,
        'user_id': user_id
    }
    return render(request, 'library.html', context)

# ...................................................................................
# ...SSSSSSS......OOOOOOO.......CCCCCCC...CIIII....AAAAA.....LLLL........SSSSSSS.....
# ..SSSSSSSSS....OOOOOOOOOO....CCCCCCCCC..CIIII....AAAAA.....LLLL.......SSSSSSSSS....
# ..SSSSSSSSSS..OOOOOOOOOOOO..CCCCCCCCCCC.CIIII...AAAAAA.....LLLL.......SSSSSSSSSS...
# .SSSSS..SSSS..OOOOO..OOOOO..CCCC...CCCCCCIIII...AAAAAAA....LLLL......LSSSS..SSSS...
# .SSSSS.......SOOOO....OOOOOOCCC.....CCC.CIIII..AAAAAAAA....LLLL......LSSSS.........
# ..SSSSSSS....SOOO......OOOOOCCC.........CIIII..AAAAAAAA....LLLL.......SSSSSSS......
# ...SSSSSSSSS.SOOO......OOOOOCCC.........CIIII..AAAA.AAAA...LLLL........SSSSSSSSS...
# .....SSSSSSS.SOOO......OOOOOCCC.........CIIII.AAAAAAAAAA...LLLL..........SSSSSSS...
# ........SSSSSSOOOO....OOOOOOCCC.....CCC.CIIII.AAAAAAAAAAA..LLLL.............SSSSS..
# .SSSS....SSSS.OOOOO..OOOOO..CCCC...CCCCCCIIII.AAAAAAAAAAA..LLLL......LSSS....SSSS..
# .SSSSSSSSSSSS.OOOOOOOOOOOO..CCCCCCCCCCC.CIIIIIAAA....AAAA..LLLLLLLLLLLSSSSSSSSSSS..
# ..SSSSSSSSSS...OOOOOOOOOO....CCCCCCCCCC.CIIIIIAAA.....AAAA.LLLLLLLLLL.SSSSSSSSSS...
# ...SSSSSSSS......OOOOOO.......CCCCCCC...CIIIIIAAA.....AAAA.LLLLLLLLLL..SSSSSSSS....
# ...................................................................................


def social_auth(request):
    if request.method == 'POST':
        
        if 'user_id' in request.session:
            user_id = request.session.get('user_id')
            user_settings_ref = db.collection('users').document(user_id)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
        else:
            messages.error(request, 'Please sign in.')
            return redirect('login')
        
        form_name = request.POST.get('form')
        state = secrets.token_urlsafe(16)
        redirect_uri =  config("SERVICE_REDIRECT_URI")
        if form_name == 'formLinkedinPersonal':
            request.session['account_type'] = 'personal'
            request.session['provider'] = 'linkedin'
            AUTHORIZATION_URL = 'https://www.linkedin.com/oauth/v2/authorization'
            CLIENT_ID = config("LINKEDIN_CLIENT_ID_BUSINESS")
            REDIRECT_URI = redirect_uri
            STATE = state
            PERSONAL_SCOPES = [
                'r_basicprofile',
                'w_member_social',
                'w_member_social_feed'
            ]
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(PERSONAL_SCOPES)}&state={STATE}'
        elif form_name == 'formLinkedinBusiness':
            request.session['account_type'] = 'business'
            request.session['provider'] = 'linkedin'
            AUTHORIZATION_URL = 'https://www.linkedin.com/oauth/v2/authorization'
            CLIENT_ID = config("LINKEDIN_CLIENT_ID_BUSINESS")
            REDIRECT_URI = redirect_uri
            STATE = state
            BUSINESS_SCOPES = [
                'r_basicprofile',
                'w_member_social',
                'w_member_social_feed',
                'r_organization_followers',
                'r_organization_social',
                'rw_organization_admin',
                'r_organization_social_feed',
                'w_organization_social',
                'w_organization_social_feed'
            ]
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(BUSINESS_SCOPES)}&state={STATE}'
        elif form_name == 'formGoogle':
            request.session['provider'] = 'google_business'
            AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
            CLIENT_ID =  config("GOOGLE_APP_ID")
            REDIRECT_URI = redirect_uri
            SCOPES = ['https://www.googleapis.com/auth/business.manage']
            STATE = state
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
        elif form_name == 'formFacebook':
            request.session['provider'] = 'facebook'
            AUTHORIZATION_URL = 'https://www.facebook.com/v17.0/dialog/oauth'
            CLIENT_ID =  config("FACEBOOK_APP_ID")
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
            AUTHORIZATION_URL = 'https://www.facebook.com/v17.0/dialog/oauth'
            CLIENT_ID =  config("FACEBOOK_APP_ID")
            REDIRECT_URI = redirect_uri
            STATE = state
            SCOPES = [
            'pages_show_list',
            'instagram_basic',
            'instagram_content_publish'
            ]
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(SCOPES)}&state={STATE}'
        else:
            messages.error(request, 'There was an error connecting your account. Please try again. (e1)')
            return redirect('service:settings')
    else:
        messages.error(request, 'There was an error connecting your account. Please try again. (e2)')
        return redirect('service:settings')
    
    return redirect(auth_url)


def process_page_selection(request):
# ----- Get the Firestore document reference for the user settings ----- #
    if 'user_id' in request.session:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    else:
        messages.error(request, 'Please sign in.')
        return redirect('login')
# ---------------------------------------------------------------------- #

    selected_page_id = request.POST.get('pageId', None)
    provider = request.POST.get('provider', None)
    page_name = request.POST.get('pageName', None)
    page_token = request.POST.get('pageToken', None)
    page_type = request.POST.get('pageType', None)

    if not selected_page_id:
        messages.error(request, 'Please make sure the Instagram account is linked to the selected Facebook account.')
        return redirect('service:settings')
    else:
        if provider == 'facebook':
            firestore_data = {
                f'{provider}_page_id': selected_page_id,
                f'{provider}_page_name': page_name,
                f'{provider}_page_token': page_token,
                f'{provider}_page_type': page_type,
                'isFacebook': True
            }       
            user_settings_ref.set(firestore_data, merge=True)
            messages.success(request, f"You've successfully connected your {provider} account!")
            return redirect('service:settings')
        elif provider == 'linkedin':
            firestore_data = {
                f'{provider}_id': selected_page_id,
                f'{provider}_name': page_name,
                'isLinkedin': True
            }       
            user_settings_ref.set(firestore_data, merge=True)
            messages.success(request, f"You've successfully connected your {provider} account!")
            return redirect('service:settings')
        else: 
            messages.error(request, 'There was an error connecting your account. Please try again. (e3)')
            return redirect('service:settings')

    
def unlink(request):
# ----- Get the Firestore document reference for the user settings ----- #
    if 'user_id' in request.session:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    else:
        messages.error(request, 'Please sign in.')
        return redirect('login')
# ---------------------------------------------------------------------- #
    
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
            'linkedin_token': None,
            'linkedin_id': None,
            'linkedin_name': None,
            'linkedin_personal_id': None,
            'linkedin_personal_name': None,
            'isLinkedin': False,
        }    
        user_settings_ref.set(firestore_data, merge=True)
    return redirect('service:settings')
    