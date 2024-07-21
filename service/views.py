from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
import io
from firebase_admin import firestore
from firebase_admin.auth import EmailAlreadyExistsError
from decouple import config
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import requests
import google.oauth2.id_token
import google.auth.transport.requests
import secrets
from dashboard.post_to_socials import *
from app1.login import *
from google.cloud import storage, firestore
import random
import string
from django.core.mail import EmailMessage
from datetime import date, datetime, timedelta, timezone
from dashboard.functions import *
from dashboard.get_images import *
import json

db = firestore.Client(project='feed-ai-c379d')
bucket_credentials = config('GS_CREDENTIALS')
bucket_name = config('GS_BUCKET_NAME')
credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
client = storage.Client(project=credentials.project_id, credentials=credentials)

def service_dashboard(request):
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
                post_to_social_feed(request, user_settings, user_settings_ref, 'service_dashboard')
                return redirect('service_dashboard')
            else:
                messages.error(request, 'Please upgrade to the Unlimited plan to post directly to your social medias.')
                return redirect('service_dashboard')
        elif form_name == 'formCheckout':
            firestore_data = {
                'isPlan': True,
            }
            user_settings_ref.set(firestore_data, merge=True)

            if user_settings.get('isSubscriber'):
                return redirect('service_business_checkout')
            return redirect('service_checkout')
        elif form_name == 'formLibrary':
            firestore_data = {
                'isLibrary': True,
            }
            user_settings_ref.set(firestore_data, merge=True)
            return redirect('service_library')
        elif form_name == 'elaine-settings':
            isElaineEmail = request.POST.get('isElaineEmail') == "on"
            
            elaine_data = {
                'isElaineEmail': isElaineEmail,
                'ElaineEmail': request.POST.get('ElaineEmail'),
            }

            elaine_doc_ref.set(elaine_data, merge=True)

            messages.success(request, 'Settings have been successfully updated!')
            return redirect('service_dashboard')
        
    try:
        if user_settings.get('service_ftue', '0') == '1':
            return redirect('service_dashboard_ftue')
        
        if not user_settings.get('isSubscriber', False):
            return redirect('service_checkout')
    except:
        return redirect('my_feadlio')
    
    image_tags_num = len(json.loads(user_settings.get('image_tags', '[]')))
    
    context = {
        'image_tags_num': image_tags_num,
        'user_settings': user_settings,
        'elaine_settings': elaine_settings,
        'user_id' : user_id,
    }
    return render(request, "service_dashboard.html", context)

def service_dashboard_ftue(request):
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
        email = user_settings.get('email')
        lead_ref = db.collection('service').document(email)
        lead_doc = lead_ref.get()
        if form_name == 'formFtue1':
            notificationMethod = request.POST.get('notificationMethod')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            fbMessage = request.POST.get('fbMessage')
            if notificationMethod == 'email':
                user_settings_ref.set({'service_ftue': '2', 'notify_email': email, 'notification_method': notificationMethod}, merge=True)
                lead_ref.set({'notify_email': email, 'notification_method': notificationMethod, 'leadPriority': 3, 'user_id': user_id}, merge=True)
            elif notificationMethod == 'phone':
                user_settings_ref.set({'service_ftue': '2', 'notify_phone': phone, 'notification_method': notificationMethod}, merge=True)
                lead_ref.set({'notify_phone': phone, 'notification_method': notificationMethod, 'leadPriority': 3, 'user_id': user_id}, merge=True)
            elif notificationMethod == 'fbMessage':
                user_settings_ref.set({'service_ftue': '2', 'notify_name': fbMessage, 'notification_method': notificationMethod, 'leadPriority': 3}, merge=True)
                lead_ref.set({'notify_name': fbMessage, 'notification_method': notificationMethod, 'leadPriority': 3, 'user_id': user_id}, merge=True)
            email_template("New user has submitted FTUE", f"User {email} has submitted their FTUE form.\nBusiness Name: {lead_doc.get('business_name')}\nBusiness Description: {lead_doc.get('business_description')}\nNotification Method: {notificationMethod}\nNotify: {fbMessage},{phone},{email}\nSelected Plan: {lead_doc.get('selectedPlan')}")
            
            repeat = 2
            for num in range(repeat):
                get_stock(user_id, num)

            messages.success(request, 'We are creating your posts now! We will notify you when they are ready.')
            return redirect('service_dashboard')
        elif form_name == 'formFtue2':
            user_settings_ref.set({'service_ftue': '2', 'leadPriority': 3}, merge=True)
            lead_ref.set({'leadPriority': 3, 'user_id': user_id}, merge=True)
            email_template("New user has submitted FTUE", f"User {email} has submitted their FTUE form.\nBusiness Name: {lead_doc.get('business_name')}\nBusiness Description: {lead_doc.get('business_description')}")
    
            messages.success(request, 'We are creating your posts now! Please select a plan to continue.')
            return redirect('service_dashboard_ftue')
        
    if user_settings.get('service_ftue', '0') == '1':
        render_template = "service_dashboard_ftue_2.html"
    elif user_settings.get('service_ftue', '0') == '2':
        return redirect('service_checkout')
    else:
        return redirect('service_dashboard')

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

def service_brand_settings(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #s

    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'brand-settings':

            firestore_data = {
                'business_name': request.POST.get('business_name', '').strip(),
                'brand_color': all_color_to_hex(request.POST.get('brand_color')),

            }

        elif form_name == 'user-settings':
            firstName = request.POST.get('firstName')
            lastName = request.POST.get('lastName')
            phone = request.POST.get('phone')
            website = request.POST.get('website')
            address1 = request.POST.get('address1')

            firestore_data = {
                'firstName': firstName,
                'lastName': lastName,
                'phone': phone,
                'website': website,
                'address1': address1
            }

        user_settings_ref.set(firestore_data, merge=True)

        messages.success(request, 'Settings Have Been Updated.')
        return redirect('service_brand_settings')
    
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
    }
    return render(request, "service_brand_settings.html", context)

def service_calendar(request):
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
    return render(request, "service_calendar.html", context)

def service_checkout(request):
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

    return render(request, "service_checkout.html", context)

def service_business_checkout(request):
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

    return render(request, "service_business_checkout.html", context)


def service_ad_checkout(request):
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

    return render(request, "service_ad_checkout.html", context)

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

def service_download(request):
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
        if form_name == 'smm-download':
            imageNumber = request.POST.get('imageNum')
            url = elaine_settings.get(f'scheduled_image_{imageNumber}', '')
            parsed_url = urlparse(url)
            print(parsed_url.netloc)
            if parsed_url.netloc == 'storage.googleapis.com':
                parts = parsed_url.path.strip('/').split('/')
                bucket_name = parts[0]
                object_name = '/'.join(parts[1:])
            else:
                messages.error(request, 'There was an error downloading the image. Please try again.')
                return redirect('service_dashboard')
            
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
            else:
                messages.error(request, 'There was an error downloading the image. Please try again.')
            
    return response

def my_feadlio(request):
    email = request.session.get('email', None)
    lead_ref = db.collection('service').document(email)
    lead = lead_ref.get().to_dict()

    if not email:
        return redirect('beta_signup')

    if request.method == 'POST':
        selectedImage = request.POST.get('selectedImage')
        if selectedImage == 'image1':
            selectedImage = 'Graphics'
        else:
            selectedImage = 'Simple'
        selectedPlan = request.POST.get('selectedPlan', 'None')
        # if selectedPlan == 'plan1':
        #     selectedPlan = 'Basic'
        # else:
        #     selectedPlan = 'Unlimited'
        bname = request.POST.get('business-name')
        bdesc = request.POST.get('business-description')
        color = request.POST.get('brand-color')

        try:
            password = email.split('@')[0] + config("AGENCY_PASSWORD_ADDON")

            try:
                user = auth.create_user(email=email, password=password)
            except EmailAlreadyExistsError:
                user = auth.get_user_by_email(email)

            doc_ref = db.collection('users').document(user.uid)
            firestore_data = {'isSubscriber': False, 'email': email, 'selectedPlan': selectedPlan, 'selectedImage': selectedImage, 'business_name': bname, 'business_description': bdesc, 'brand_color': color, 'agency_id': config("AGENCY_MASTER_ID"), 'isAgency': True, 'service_ftue': '1'}
            doc_ref.set(firestore_data, merge=True)

            request.session['user_id'] = user.uid

            lead_ref.update({
                'selectedImage': selectedImage,
                'selectedPlan': selectedPlan,
                'business_name': bname,
                'business_description': bdesc,
                'color': color,
                'leadPriority': 2,
                'user_id': user.uid
            })

        except Exception as e:
            messages.error(request, ("An error occurred: {}".format(e)))
            return redirect('my_feadlio')
        
        return redirect('my_feadlio_success')
    
    context = {'lead': lead}
    return render(request, "my_feadlio.html", context)

def my_feadlio_success(request):
    if request.method == 'POST':
        return redirect('service_dashboard_ftue')

    return render(request, "my_feadlio_success.html")

def service_graphic_designer(request):
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
            service_submit_brief(request)
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
        return redirect('service_graphic_designer')
    
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

    credentials = service_account.Credentials.from_service_account_file(config("GS_CREDENTIALS"))
    client = storage.Client(project=credentials.project_id, credentials=credentials)
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

    return render(request, "service_graphic_designer.html", context)

def service_video_editor(request):
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
            service_submit_brief(request)
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
        return redirect('service_video_editor')
    
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

    credentials = service_account.Credentials.from_service_account_file(config("GS_CREDENTIALS"))
    client = storage.Client(project=credentials.project_id, credentials=credentials)
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

    return render(request, "service_video_editor.html", context)

@csrf_exempt
def service_generate_signed_url(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    if request.method == 'POST':
        bucket_credentials = config('GS_CREDENTIALS')
        bucket_name = config('GS_BUCKET_NAME')
        credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
        client = storage.Client(project=credentials.project_id, credentials=credentials)
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
def service_submit_brief(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    bucket_credentials = config('GS_CREDENTIALS')
    bucket_name = config('GS_BUCKET_NAME')
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
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
def service_make_file_public(request):
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
        
        bucket_credentials = config('GS_CREDENTIALS')
        bucket_name = config('GS_BUCKET_NAME')
        credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
        client = storage.Client(project=credentials.project_id, credentials=credentials)
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

def service_advertising_specialist(request):
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
            service_submit_brief(request)
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
        return redirect('service_advertising_specialist')
    
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

    return render(request, "service_advertising_specialist.html", context)


def service_library(request):
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
                return redirect('service_library')
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
                return redirect('service_library')
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
    return render(request, 'service_library.html', context)

def service_auth(request):
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
            return redirect('service_brand_settings')
    else:
        messages.error(request, 'There was an error connecting your account. Please try again. (e2)')
        return redirect('service_brand_settings')
    
    return redirect(auth_url)

def service_callback(request):
    state = request.GET.get('state')
    provider = request.session.get('provider')

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

    if provider == 'linkedin':
        isCheck = 'Linkedin'
        code = request.GET.get('code')
        access_token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        params = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri':  config("SERVICE_REDIRECT_URI"),
            'client_id': config("LINKEDIN_CLIENT_ID_BUSINESS"),
            'client_secret': config("LINKEDIN_CLIENT_SECRET_BUSINESS"),
        }
        response = requests.post(access_token_url, data=params)
        data = response.json()
        access_token = data.get('access_token')
        account_type = request.session.get('account_type', 'personal')

        def get_user_managed_organizations(access_token):
            url = "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(*,roleAssignee~(localizedFirstName, localizedLastName), organization~(localizedName)))"
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        profile_response = requests.get('https://api.linkedin.com/v2/me', headers={'Authorization': f'Bearer {access_token}'})
        profile_data = profile_response.json()
        profile_data_id = profile_data.get('id')
        personal_name = profile_data.get('localizedFirstName', '')
        if account_type == 'personal':
            firestore_data = {
                f'{provider}_type': 'personal',
                f'{provider}_id': profile_data_id,
                f'{provider}_token': access_token,
                f'{provider}_name': personal_name,
                f'is{isCheck}': True
            }
            user_settings_ref.set(firestore_data, merge=True)
        else:
            organizations_list = get_user_managed_organizations(access_token)
            organizations_data = organizations_list.get('elements', [])
            transformed_organizations = [
                {
                    'id': org['organization'].split(':')[-1],
                    'name': org.get('organization~', {}).get('localizedName', 'Unknown Organization Name'),
                    'type': 'page'
                }
                for org in organizations_data
            ]

            if len(transformed_organizations) == 1:
                organization_details = organizations_data[0].get('organization~', {})
                organization_details_id = organization_details.get('id')
                username = organization_details.get('localizedName', '')
                firestore_data = {
                    f'{provider}_type': 'business',
                    f'{provider}_personal_id': profile_data_id,
                    f'{provider}_personal_name': personal_name,
                    f'{provider}_id': organization_details_id,
                    f'{provider}_token': access_token,
                    f'{provider}_name': username,
                    f'is{isCheck}': True
                }

                user_settings_ref.set(firestore_data, merge=True)
            else:
                firestore_data = {
                    f'{provider}_personal_id': profile_data_id,
                    f'{provider}_personal_name': personal_name,
                    f'{provider}_type': 'business',
                    f'{provider}_token': access_token,
                }

                user_settings_ref.set(firestore_data, merge=True)
                return render(request, 'service_page_selection_popup.html', {'pages': transformed_organizations, 'provider': provider,})
        pass
    elif provider == 'facebook':
        isCheck = 'Facebook'
        code = request.GET.get('code')
        access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
        params = {
            'client_id':  config("FACEBOOK_APP_ID"),
            'client_secret': config("FACEBOOK_APP_SECRET"),
            'redirect_uri':  config("SERVICE_REDIRECT_URI"),
            'code': code
        }
        response = requests.get(access_token_url, params=params, verify=False)
        data = response.json()
        short_lived_access_token = data.get('access_token')
        access_token = exchange_short_lived_token_for_long_lived(short_lived_access_token,  config("FACEBOOK_APP_ID"), config("FACEBOOK_APP_SECRET"))
        facebook_pages_and_groups, has_multiple = get_facebook_pages_and_groups(access_token)
        if has_multiple:
            firestore_data = {
                f'{provider}_token': access_token,
            }
            user_settings_ref.set(firestore_data, merge=True)
            return render(request, 'service_page_selection_popup.html', {'pages': facebook_pages_and_groups, 'provider': provider,})
        else:
            isFacebook = True
            facebook_page_id = facebook_pages_and_groups[0]['id'] if facebook_pages_and_groups else None
            facebook_page_token = facebook_pages_and_groups[0]['access_token'] if facebook_pages_and_groups else None
            facebook_page_type = facebook_pages_and_groups[0]['type'] if facebook_pages_and_groups else None
            facebook_page_name = facebook_pages_and_groups[0]['name'] if facebook_pages_and_groups else None
            if not all([facebook_page_id, facebook_page_token, facebook_page_type, facebook_page_name]):
                isFacebook = False
                access_token = None
                messages.error(request, 'Please make sure the facebook account is linked to the selected page.')
            firestore_data = {
                f'{provider}_token': access_token,
                f'{provider}_page_id': facebook_page_id,
                f'{provider}_page_name': facebook_page_name,
                f'{provider}_page_token': facebook_page_token,
                f'{provider}_page_type': facebook_page_type,
                'isFacebook': isFacebook,
            }
            user_settings_ref.set(firestore_data, merge=True)
            pass
    elif provider == 'instagram':
        try:
            isCheck = 'Instagram'
            code = request.GET.get('code')
            access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
            params = {
                'client_id':  config("FACEBOOK_APP_ID"),
                'client_secret': config("FACEBOOK_APP_SECRET"),
                'redirect_uri':  config("SERVICE_REDIRECT_URI"),
                'code': code
            }
            response = requests.get(access_token_url, params=params, verify=False)
            data = response.json()
            short_lived_access_token = data.get('access_token')
            access_token = exchange_short_lived_token_for_long_lived(short_lived_access_token,  config("FACEBOOK_APP_ID"), config("FACEBOOK_APP_SECRET"))
            facebook_page_ids, has_multiple = get_facebook_pages_and_groups(access_token)
            got_instagram_id = None
            got_facebook_page_id = None
            username = None
            firestore_data = {}
            try:
                for facebook_page_id in facebook_page_ids:
                    instagram_id = get_instagram_user_id(facebook_page_id['id'], access_token)
                    if instagram_id:
                        got_instagram_id = instagram_id
                        got_facebook_page_id = facebook_page_id['id']
                        break

                if not got_instagram_id == None:
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
                    return redirect('service_brand_settings')
            except Exception as e:
                messages.error(request, 'Please make sure the instagram account is linked to the selected facebook account.')
                return redirect('service_brand_settings')
        except Exception as e:
            messages.error(request, e)
            return redirect('service_brand_settings')
        
    elif provider == 'google_business':
        isCheck = 'Google'
        code = request.GET.get('code')
        access_token_url = 'https://oauth2.googleapis.com/token'
        params = {
            'client_id':  config("GOOGLE_APP_ID"),
            'client_secret': config("GOOGLE_APP_SECRET"),
            'redirect_uri':  config("SERVICE_REDIRECT_URI"),
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

    return redirect('service_brand_settings')
    
def service_process_page_selection(request):
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
        return redirect('service_brand_settings')
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
            return redirect('service_brand_settings')
        elif provider == 'linkedin':
            firestore_data = {
                f'{provider}_id': selected_page_id,
                f'{provider}_name': page_name,
                'isLinkedin': True
            }       
            user_settings_ref.set(firestore_data, merge=True)
            messages.success(request, f"You've successfully connected your {provider} account!")
            return redirect('service_brand_settings')
        else: 
            messages.error(request, 'There was an error connecting your account. Please try again. (e3)')
            return redirect('service_brand_settings')

    
def service_unlink(request):
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
    return redirect('service_brand_settings')
    