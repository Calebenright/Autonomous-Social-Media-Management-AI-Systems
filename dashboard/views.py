from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UserSettingsForm
from .models import UserSettings
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
import os
from .post_creator import create_image, create_stock_post, create_call_to_action, create_caption, create_dalle_post, create_stable_dif_post, create_ad_copy, create_ad, create_placeholder
from .upload_post import send_post
from .generate_comment import generate_comment
from django.http import JsonResponse
import time
from .generate_unique_filename import generate_unique_filename
from .brand_settings import create_tags
from firebase_admin import firestore, auth, credentials
import base64
import ast
import json
from .tasks import enqueue_task

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
                        'endFtue': True
                    }
                    user_settings_ref.set(firestore_data, merge=True)
                    return redirect(link)
                
        elif form_name == 'formAutomate':
            image_folder_path = f'user_folders/{user_id}/images/'
            tags = user_settings['tags']
            key = user_settings['business_description']

            # Enqueue the task with the required payload
            payload = {
                'user_id': user_id
            }

            enqueue_task(payload)

             # Prepare the data to be saved in Firestore
            firestore_data = {
                'status': '10',
                'noAuto': False
            }
                
            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()

            context = {
                'user_settings': user_settings,
                'user_id' : user_id
            }
            return render(request, 'dashboard.html', context)
        
        elif form_name == 'formSchedule':

            # Prepare the data to be saved in Firestore
            firestore_data = {
                'noAuto': True
            }
                
            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()

            context = {
                'user_settings': user_settings,
                'user_id' : user_id
            }
            return render(request, 'dashboard.html', context)
        
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
        if num_post < 10:
            if form_name == 'formCaption1':
                selected_option = request.session.get('selected_radio', None)
                isLogo = request.session.get('isLogo', None)
                post = create_caption(biz, biz_name)
                firestore_data = {'next_caption': post}
                url = user_settings['next_image_url']
            
            elif form_name == 'formPostSchedule':
                post = request.POST.get('caption')
                url = request.POST.get('url')
                selected_option = request.session.get('selected_radio', None)
                isLogo = request.session.get('isLogo', None)
                if num_schedule >= 8:
                    num_schedule = 1
                else:
                    num_schedule += 1

                firestore_data = {
                    'schedule_img_' + str(num_schedule): url,
                    'schedule_cap_' + str(num_schedule): post,
                    'next_caption': post,
                    'num_schedule': num_schedule
                }

            else:
        # ------------------- Get Selected Post Type --------------------------- #
                selected_option = request.POST.get('flexRadioDefault')
                request.session['selected_radio'] = selected_option
                isLogo = request.POST.get('isLogo', None)
                request.session['isLogo'] = isLogo
        # ---------------------------------------------------------------------- #
                
                if selected_option == 'up':
                    key = request.FILES.get('file')

                    # Get the file extension
                    file_extension = key.name.split('.')[-1].lower()

                    # Check if the file extension is not allowed
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
                elif selected_option == 'cta':
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
                post = create_caption(biz, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, image_folder_path)

                if num_post >= 10:
                    num_post = 1
                else:
                    num_post += 1
                    

                firestore_data = {
                    'last_image_url': last_image_url,
                    'last_caption': last_caption,
                    'next_image_url': url,
                    'next_caption': post,
                    'num_post': num_post
                }

            # Save the data to Firestore
            user_settings_ref.set(firestore_data, merge=True)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()

            user_settings['tags'] = json.dumps(tags)

            return render(request, 'post_creator.html', {'selected_radio': selected_option, 'isLogo': isLogo, 'user_settings': user_settings})
        else:
            user_settings['deny'] = True
    context = {
        'user_settings': user_settings,
    }
    
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
                input_string = request.POST.get('tags')
                output_list = [item.strip() for item in input_string.split(',')]
                output_string = json.dumps(output_list)
                tags = output_string
            else:
                if request.POST.get('business_description'):
                    tags = create_tags(request.POST.get('business_description'))
                else:
                    tags = ''

            firestore_data = {
                'business_name': request.POST.get('business_name'),
                'business_description': request.POST.get('business_description'),
                'brand_color': request.POST.get('brand_color'),
                'temperature': request.POST.get('temperature'),
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
            user_settings = {}
        # ---------------------------------------------------------------------- #
        context = {
        'user_settings': user_settings,
        'success': 'Settings Updated'
        }
        return render(request, 'brand_settings.html', context)

    context = {
        'user_settings': user_settings,
    }
    return render(request, 'brand_settings.html', context)

def error(request):
    return render(request, 'error.html', status=500)

