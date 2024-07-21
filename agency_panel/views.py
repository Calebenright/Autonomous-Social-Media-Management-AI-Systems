from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from google.cloud import storage, firestore
from firebase_admin import firestore
from decouple import config
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from app1.login import user_login, create_or_login_user
from firebase_admin import firestore, auth, credentials
import uuid
from dashboard.functions import delete_gcs_folder
import mimetypes
import json

db = firestore.Client(project='feed-ai-c379d')

def agency_panel(request):
    user_id = request.session.get('user_id')
    
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    user_data = user_doc.to_dict()
    
    susan_settings = db.collection('users').document(user_id).collection('agents').document('susan').get().to_dict() or {}
    george_settings = db.collection('users').document(user_id).collection('agents').document('george').get().to_dict() or {}
    david_settings = db.collection('users').document(user_id).collection('agents').document('david').get().to_dict() or {}

    if user_data.get('isAgency'):
        agency_id = user_data.get('agency_id')
        if agency_id:
            users_query = db.collection('users').where('agency_id', '==', agency_id).stream()
            firestore_data = []
            
            for user in users_query:
                user_data = user.to_dict()
                susan_settings = db.collection('users').document(user.id).collection('agents').document('susan').get().to_dict() or {}
                george_settings = db.collection('users').document(user.id).collection('agents').document('george').get().to_dict() or {}
                david_settings = db.collection('users').document(user.id).collection('agents').document('david').get().to_dict() or {}

                user_with_settings = {
                    'document_id': user.id,
                    **user_data,
                    'susan_settings': susan_settings,
                    'george_settings': george_settings,
                    'david_settings': david_settings,
                }
                
                firestore_data.append(user_with_settings)

            sort = request.GET.get('sort')
            if sort:
                request.session['sort'] = sort
            else:
                sort = request.session.get('sort')
                
            if sort:
                if sort == 'Paid':
                    firestore_data = [user for user in firestore_data if user.get('isSubscriber')]
                elif sort == 'Free':
                    firestore_data = [user for user in firestore_data if not user.get('isSubscriber') and user.get('isAutomated')]
                elif sort == 'Lead':
                    firestore_data = [user for user in firestore_data if not user.get('isSubscriber') and not user.get('isAutomated') and not user.get('isLegacy')]
                elif sort == 'Archive':
                    firestore_data = [user for user in firestore_data if not user.get('isSubscriber') and not user.get('isAutomated') and user.get('isLegacy')]

            paginator = Paginator(firestore_data, 25)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            return render(request, 'agency_panel.html', {
                'agency_id': agency_id, 
                'firestore_data': firestore_data,
                'page_obj': page_obj,
            })
        else:
            messages.error(request, 'Agency ID not found.')
            return redirect('login')
    else:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('login')
    
def agency_tasks(request, document_id):
    if request.session.get('user_id') != document_id:
        request.session['user_id'] = document_id

    user_settings = db.collection('users').document(document_id).get().to_dict()
    susan_settings = db.collection('users').document(document_id).collection('agents').document('susan').get().to_dict() or {}
    george_settings = db.collection('users').document(document_id).collection('agents').document('george').get().to_dict() or {}
    david_settings = db.collection('users').document(document_id).collection('agents').document('david').get().to_dict() or {}

    credentials = service_account.Credentials.from_service_account_file(config("GS_CREDENTIALS"))
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(config("GS_BUCKET_NAME"))

    def get_file_details(prefix):
        file_blobs = list(bucket.list_blobs(prefix=prefix))
        files = []
        for file_blob in file_blobs:
            file_url = f'https://storage.googleapis.com/{bucket.name}/{file_blob.name}'
            mime_type, _ = mimetypes.guess_type(file_url)
            is_image = mime_type.startswith('image') if mime_type else False
            is_video = mime_type.startswith('video') if mime_type else False
            files.append({
                'file': file_url,
                'is_image': is_image,
                'is_video': is_video,
            })
        return files
    
    graphic_prefix = f'user_folders/{document_id}/graphic_proposal/'
    video_prefix = f'user_folders/{document_id}/video_proposal/'
    ad_prefix = f'user_folders/{document_id}/ad_proposal/'

    graphic_files = get_file_details(graphic_prefix)
    video_files = get_file_details(video_prefix)
    ad_files = get_file_details(ad_prefix)

    context = {
        'graphic_files': graphic_files,
        'video_files': video_files,
        'ad_files': ad_files,
        'user_settings': user_settings,
        'susan_settings': susan_settings,
        'george_settings': george_settings,
        'david_settings': david_settings,
        'user_id': document_id,
    }
    return render(request, 'agency_tasks.html', context)

def agency_upload_graphic(request):
    user_id = request.session.get('user_id')
    user_doc = db.collection('users').document(user_id)
    user_settings = user_doc.get().to_dict()
    george_doc = db.collection('users').document(user_id).collection('agents').document('george')
    george_data = george_doc.get().to_dict()
    
    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'graphic_upload':
            try:
                file = request.FILES['graphic']
                file_name = file.name
                file_type = file_name.split('.')[-1]
                library_folder_path = f'user_folders/{user_id}/image_library/{file_name}'
                
                bucket_credentials = config('GS_CREDENTIALS')
                bucket_name = config('GS_BUCKET_NAME')
                credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
                client = storage.Client(project=credentials.project_id, credentials=credentials)
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(library_folder_path)
                blob.upload_from_file(file)
                blob.make_public()
                url = blob.public_url

                delete_gcs_folder(user_id, 'graphic_proposal')

                # get_old_image_tags = user_settings.get('image_tags', '[]')
                # old_image_tags = json.loads(get_old_image_tags)
                # old_image_tags = [item.strip() for item in old_image_tags]
                # if url not in old_image_tags:
                #     old_image_tags.append(url)
                #     image_tags_string = json.dumps(old_image_tags).replace("'", '"')
                #     user_doc.set({'image_tags': image_tags_string}, merge=True)

                george_data = {
                    'isLoading': False,
                    'graphic': url,
                    'progress': 100,
                }

                george_doc.set(george_data, merge=True)
                messages.success(request, 'Graphic uploaded successfully.')
                return redirect('agency_tasks', document_id=user_id)
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('agency_tasks', document_id=user_id)
            
        elif form_name == 'graphic_message':
            message = request.POST.get('message')
            george_data = {
                'isLoading': False,
                'message': message,
            }
            george_doc.set(george_data, merge=True)
            messages.success(request, 'Message sent successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'graphic_clear':
            george_data = {
                'graphic': None,
                'message': '',
            }
            george_doc.set(george_data, merge=True)
            messages.success(request, 'Message cleared successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'graphic_message_clear':
            george_data = {
                'message': '',
            }
            george_doc.set(george_data, merge=True)
            messages.success(request, 'Message cleared successfully.')
            return redirect('agency_tasks', document_id=user_id)
    
    return redirect('agency_tasks', document_id=user_id)   

def agency_upload_video(request):
    user_id = request.session.get('user_id')
    user_doc = db.collection('users').document(user_id)
    user_settings = user_doc.get().to_dict()
    susan_doc = db.collection('users').document(user_id).collection('agents').document('susan')
    susan_data = susan_doc.get().to_dict()
    
    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'video_upload':
            delete_gcs_folder(user_id, 'video_proposal')
            folder_name = request.session.get('folder_name')
            file_name = request.session.get('file_name')
            bucket_credentials = config('GS_CREDENTIALS')
            bucket_name = config('GS_BUCKET_NAME')
            credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
            client = storage.Client(project=credentials.project_id, credentials=credentials)
            bucket = client.bucket(bucket_name)
            folder_path = f'user_folders/{user_id}/{folder_name}/'
            filename = folder_path + file_name
            blob = bucket.blob(filename)
            blob.make_public()
            url = blob.public_url

            get_old_video_tags = user_settings.get('video_tags', '[]')
            old_video_tags = json.loads(get_old_video_tags)
            old_video_tags = [item.strip() for item in old_video_tags]
            if url not in old_video_tags:
                old_video_tags.append(url)
                video_tags_string = json.dumps(old_video_tags).replace("'", '"')
                user_doc.set({'video_tags': video_tags_string}, merge=True)

            susan_data = {
                'isLoading': False,
                'video': url,
                'progress': 100,
            }
            susan_doc.set(susan_data, merge=True)
            messages.success(request, 'Message sent successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'video_message':
            message = request.POST.get('message')
            susan_data = {
                'isLoading': False,
                'message': message,
            }
            susan_doc.set(susan_data, merge=True)
            messages.success(request, 'Message sent successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'video_message_clear':
            susan_data = {
                'message': '',
            }
            susan_doc.set(susan_data, merge=True)
            messages.success(request, 'Message cleared successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'video_clear':
            susan_data = {
                'video': None,
                'message': '',
            }
            susan_doc.set(susan_data, merge=True)
            messages.success(request, 'Message cleared successfully.')
            return redirect('agency_tasks', document_id=user_id)
    
    return redirect('agency_tasks', document_id=user_id)


def agency_upload_ad(request):
    user_id = request.session.get('user_id')
    user_doc = db.collection('users').document(user_id)
    user_settings = user_doc.get().to_dict()
    david_doc = db.collection('users').document(user_id).collection('agents').document('david')
    david_data = david_doc.get().to_dict()
    
    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'ad_approved':
            david_data = {
                'isLoading': False,
                'isRunning': True,
            }
            david_doc.set(david_data, merge=True)
            messages.success(request, 'Ad has been approved successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'ad_paused':
            david_data = {
                'isLoading': False,
                'isRunning': False,
            }
            david_doc.set(david_data, merge=True)
            messages.success(request, 'Ad has been paused.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'switchLink':
            needsLink = not david_data.get('needsLink', False)

            david_data = {
                'needsLink': needsLink,
            }
            david_doc.set(david_data, merge=True)

            if needsLink:
                needsLinkMessage = 'Link Ad Account video is now showing.'
            else:
                needsLinkMessage = 'Link Ad Account is hidden.'

            messages.success(request, needsLinkMessage)
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'ad_analytics':
            impressions = request.POST.get('impressions')
            clicks = request.POST.get('clicks')
            money_spent = request.POST.get('money_spent')
            ctr = request.POST.get('ctr')
            ad_credits = request.POST.get('ad_credits')
            david_data = {
                'impressions': impressions,
                'clicks': clicks,
                'money_spent': money_spent,
                'ctr': ctr,
            }
            david_doc.set(david_data, merge=True)
            user_doc.set({'ad_credits':ad_credits}, merge=True)
            messages.success(request, 'Message sent successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'ad_message':
            message = request.POST.get('message')
            david_data = {
                'isLoading': False,
                'message': message,
            }
            david_doc.set(david_data, merge=True)
            messages.success(request, 'Message sent successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'ad_message_clear':
            david_data = {
                'message': '',
            }
            david_doc.set(david_data, merge=True)
            messages.success(request, 'Message cleared successfully.')
            return redirect('agency_tasks', document_id=user_id)
        elif form_name == 'ad_clear':
            david_data = {
                'message': '',
                'impressions': 0,
                'clicks': 0,
                'money_spent': 0,
                'ctr': 0,
            }
            david_doc.set(david_data, merge=True)
            messages.success(request, 'Message cleared successfully.')
            return redirect('agency_tasks', document_id=user_id)
    
    return redirect('agency_tasks', document_id=user_id)

def agency_switch(request, document_id):
    if document_id:
        request.session['user_id'] = document_id
        return redirect('dashboard')
    else:
        messages.error(request, 'User ID not found.')
        return redirect('login')
    
def agency_service_switch(request, document_id):
    if document_id:
        request.session['user_id'] = document_id
        return redirect('service_dashboard')
    else:
        messages.error(request, 'User ID not found.')
        return redirect('login')
    
def agency_delete(request, document_id):
    try:
        user_doc_ref = db.collection('users').document(document_id)
        user_doc = user_doc_ref.get()

        if not user_doc.exists:
            messages.error(request, 'User not found.')
            return redirect('agency_panel')
        
        user_data = user_doc.to_dict()
        
        if user_data.get('isSubscriber') != True and user_data.get('agency_master') != True:
            user_doc_ref.delete()
            messages.success(request, 'User account deleted successfully.')
        else:
            messages.error(request, 'Cannot delete user account. User is either a subscriber or an agency admin.')

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    return redirect('agency_panel')

def agency_archive(request, document_id):
    try:
        user_doc_ref = db.collection('users').document(document_id)
        user_doc = user_doc_ref.get()

        if not user_doc.exists:
            messages.error(request, 'User not found.')
            return redirect('agency_panel')
        
        user_data = user_doc.to_dict()
        
        if user_data.get('isSubscriber') != True and user_data.get('agency_master') != True:
            data = {
                'isLegacy': True,
            }
            user_doc_ref.update(data)
            messages.success(request, 'User archived successfully.')
        else:
            messages.error(request, 'Cannot archived user account. User is either a subscriber or an agency admin.')

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    return redirect('agency_panel')

def add_account(request, agency_id):
    if request.method == 'POST':
        agency_master_query = db.collection('users').where('agency_id', '==', agency_id).where('agency_master', '==', True).stream()
        
        agency_master_user = None
        for user in agency_master_query:
            agency_master_user = user.to_dict()
            break
        
        if not agency_master_user:
            messages.error(request, 'Agency master not found.')
            return redirect('agency_panel')
        
        email = agency_master_user.get('email')
        new_user_data = {
            'agency_id': agency_id,
            'isAgency': True,
            'email': email,
            'business_name': 'New Account',
        }
        
        db.collection('users').add(new_user_data)
        messages.success(request, 'Account added successfully.')
    
    return redirect('agency_panel')

def agency_form(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            id_token = user_login(email, password)
            decoded_token = auth.verify_id_token(id_token)

            new_user_data = {
                'isAgency': True,
                'agency_master': True,
                'agency_id': str(uuid.uuid4()),
            }
            
            db.collection('users').document(decoded_token.get('uid')).update(new_user_data)
            messages.success(request, 'Agency account created successfully.')
            return redirect('agency_panel')
        except Exception as e:
            messages.error(request, 'An error occurred. Please make sure you already have a feadl.io account.')
    return render(request, 'agency_form.html')