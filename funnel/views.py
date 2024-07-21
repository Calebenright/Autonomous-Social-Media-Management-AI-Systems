from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from firebase_admin import firestore
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
from google.oauth2 import service_account
import uuid
from django.conf import settings
from django.core.mail import EmailMessage
from moviepy.editor import VideoFileClip
from PIL import Image
from dashboard.tasks import enqueue_time_task, create_queue
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from dashboard.functions import correct_orientation

db = firestore.Client(project='feed-ai-c379d')

def process_email(request, redirect_success, redirect_fail, template):
    if request.method == 'POST':
        # Send to CRM
        subject = request.POST.get("funnel")
        email = request.POST.get('email')
        request.session['email'] = email
        details = {
            'email': email,
            'funnel': subject,
            'leadPriority': 1,
        }
        message = 'Email: {email}\n'.format(**details)
        
        from_email = config("EMAIL_HOST_USER")
        recipient_list = [config("INTERNAL_RECIPIENTS")]
        to_admin_email_message = EmailMessage(subject, message, from_email, recipient_list)
        
        try:
            # to_admin_email_message.send()
            doc_ref = db.collection('service').document(details['email'])
            doc_ref.set(details)
        except Exception:
            messages.error(request, "There was an error sending your email. Please wait a moment and try again.")
            return redirect(redirect_fail)
        
        # Send to User
        if request.POST.get('isSendToUser', False) == 'on':
            suggested_subject = request.POST.get('subject', "Feadl.io - Let's Get Started!")
            suggested_message = f"Hi {email},\n\nI'm excited to get you setup with feadl.io. To continue, follow this link to get your social media up and running!\n\nGetting Started Guide\nhttps://feadl.io/my_feadlio/\n\nSincerely,\nElaine\n\nMarketing Agent @ Feadl.io"

            to_user_email_message = EmailMessage(suggested_subject, suggested_message, from_email, [email])
            
            try:
                to_user_email_message.send()
                db.collection('service').document(email).update({'emailSent': True})

                return redirect(redirect_success)
            except Exception as e:
                print(f"An error occurred: {e}")
                return redirect(redirect_success)
        else:
            return redirect(redirect_success)

    return render(request, template)

def social_media_guy(request):
    return process_email(request, 'social_media_guy_success', 'social_media_guy', 'social_media_guy.html')

def social_media_guy_form(request):
    return process_email(request, 'social_media_guy_success', 'social_media_guy_form', 'social_media_guy_form.html')

def free_airbnb_photography(request):
    return process_email(request, 'social_media_guy_success', 'free_airbnb_photography', 'free_airbnb_photography.html')

def free_photography(request):
    return process_email(request, 'social_media_guy_success', 'free_photography', 'free_photography.html')

def free_smm(request):
    return process_email(request, 'social_media_guy_success', 'free_smm', 'free_smm.html')

def getting_started(request):
    return process_email(request, 'social_media_guy_success', 'getting_started', 'getting_started.html')

def social_media_guy_calendly(request):
    return render(request, 'social_media_guy_calendly.html')

def beta_signup(request):
    return process_email(request, 'my_feadlio', 'beta_signup', 'beta_signup.html')

def social_media_guy_success(request):
    return render(request, 'social_media_guy_success.html')

def price_5(request):
    return render(request, 'price_5.html')

def add_logo_to_thumbnail(thumbnail_path):
    thumbnail = Image.open(thumbnail_path)
    logo = Image.open('static/funnel/media/Youtube_logo.png')

    logo_width = int(thumbnail.width * 0.2)
    logo_height = int((logo_width / logo.width) * logo.height)
    logo_resized = logo.resize((logo_width, logo_height))

    x = (thumbnail.width - logo_resized.width) // 2
    y = (thumbnail.height - logo_resized.height) // 2
    thumbnail.paste(logo_resized, (x, y), logo_resized)

    thumbnail.save(thumbnail_path)

def kole_enright_baseball_training(request):
    return render(request, 'kole_enright_baseball_training.html')

def kole_enright_success(request):
    return render(request, 'kole_enright_success.html')

def kole_enright_paid(request):
    to_email = request.session.get('email')
    subject = "Your video is processing!"
    message = f"Your professional video breakdown from Kole Enright is processing on our server. We will email you once it's finished."
    
    from_email = config("EMAIL_HOST_USER")
    recipient_list = [to_email]
    to_kole_email = EmailMessage(subject, message, from_email, recipient_list)
    to_kole_email.send()
    return render(request, 'kole_enright_paid.html')

def kole_enright_video_breakdown(request):
    email = request.GET.get('email')
    
    bucket_credentials = config('GS_CREDENTIALS')
    bucket_name = config('GS_BUCKET_NAME')
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    
    filename = 'thumbnail.jpg'
    folder_path = 'kole_training/' + email + '/'
    blob = bucket.blob(folder_path + filename)

    image = blob.public_url

    return render(request, 'kole_enright_video_breakdown.html', {'image': image})

@csrf_exempt
def generate_signed_url(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        request.session['email'] = email
        bucket_credentials = config('GS_CREDENTIALS')
        bucket_name = config('GS_BUCKET_NAME')
        credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
        client = storage.Client(project=credentials.project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        folder_path = 'kole_training/' + email + '/'
        file_name = request.POST.get('file_name')
        extension = os.path.splitext(file_name)[1] if file_name else None
        filename = folder_path + 'video_upload' + extension
        blob = bucket.blob(filename)

        signed_url = blob.generate_signed_url(
            version='v4',
            expiration=600,
            method='PUT',
            content_type='application/octet-stream'
        )

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"


        return JsonResponse({'url': signed_url, 'public_url': public_url, 'extension': extension})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def upload_file(request):
    if request.method == 'GET':
        email = request.GET.get('email')
        signed_url = request.GET.get('file_url')
        extension = request.GET.get('extension')
        bucket_credentials = config('GS_CREDENTIALS')
        bucket_name = config('GS_BUCKET_NAME')
        credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
        client = storage.Client(project=credentials.project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        folder_path = f'kole_training/{email}/'
        filename = folder_path + 'video_upload' + extension
        blob = bucket.blob(filename)
        blob.make_public()
        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        
        with requests.get(public_url, stream=True) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_video:
                for chunk in r.iter_content(chunk_size=8192):
                    temp_video.write(chunk)
                temp_video_path = temp_video.name

        with VideoFileClip(temp_video_path) as video_clip:
            if video_clip.rotation == 90:
                video_clip = video_clip.resize(video_clip.size[::-1])
                video_clip.rotation = 0
            thumbnail = video_clip.get_frame(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_thumbnail:
                thumbnail_path = temp_thumbnail.name
                Image.fromarray(thumbnail).save(thumbnail_path)

                add_logo_to_thumbnail(thumbnail_path)

        thumbnail_blob = bucket.blob(folder_path + "thumbnail.jpg")
        thumbnail_blob.upload_from_filename(thumbnail_path, content_type='image/jpeg')
        thumbnail_blob.make_public()
        thumbnail_url = thumbnail_blob.public_url

        os.remove(temp_video_path)
        os.remove(thumbnail_path)
        
        subject = "New Training Video Submission"
        kole_email = "enrightkole@gmail.com"
        message = f"Hi Kole,\n\nA new training video has been submitted. You can view it here: {public_url}\n\nSincerely,\nCJ Bot"
        
        from_email = config("EMAIL_HOST_USER")
        recipient_list = [kole_email]
        to_kole_email = EmailMessage(subject, message, from_email, recipient_list)
        to_kole_email.send()

        link = f"https://feadl.io/kole_enright_video_breakdown/?email={email}"
        payload = {
            "to_email": email,
            "subject": "View your remote training video breakdown!",
            "message": f"Hi {email},\n\nThank you for submitting your training video. You can view it here: {link}\n\nSincerely,\nKole Enright"
        }
        enqueue_time_task(payload, "kole-enright-baseball-training-queue", "https://feadl.io/automated_email/", 3)
        print("Task enqueued")
        return redirect('kole_enright_success')
    else:
        return redirect('kole_enright_baseball_training')

def smm_relink(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            id_token = user_login(email, password)
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            messages.error(request, 'Invalid login credentials.')
            return redirect('smm_relink')

        request.session['user_id'] = user_id
        messages.success(request, 'The form has been successfully submitted!')
        return redirect('smm_form')

    return render(request, 'smm_relink.html')

def smm_form(request):
    if 'user_id' in request.session:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    else:
        user_settings = {}
    
    if request.method == 'POST':
        firstName = request.POST.get('firstName')
        lastName = request.POST.get('lastName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        website = request.POST.get('website')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')
        business_name = request.POST.get('businessName')
        business_description = request.POST.get('businessDesc')

        id_token, pid, user_id, isUser = create_or_login_funnel(email)

        if id_token is None:
            messages.error(request, 'An error occurred while saving your info.')
            return redirect('smm_form')

        firestore_data = {
            'firstName': firstName,
            'lastName': lastName,
            'email': email,
            'phone': phone,
            'website': website,
            'address1': address1,
            'business_name': business_name,
            'business_description': business_description,
            'admin_id': pid,
            'isSubscriber': True,
        }

        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        user_settings_ref.set(firestore_data, merge=True)

        request.session['user_id'] = user_id
        messages.success(request, 'The form has been successfully submitted!')
        return redirect('smm_form')
    
    context = {'user_settings': user_settings}

    return render(request, 'smm_form.html', context)

def funnel_auth(request):
    if request.method == 'POST':
        if 'user_id' not in request.session:
            messages.error(request, 'Please submit the above form.')
            return redirect('smm_form')
        
        form_name = request.POST.get('form')
        state = secrets.token_urlsafe(16)
        redirect_uri =  config("FUNNEL_REDIRECT_URI")
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
            return redirect('smm_form')
    else:
        return redirect('smm_form')
    
    return redirect(auth_url)

def funnel_callback(request):
    state = request.GET.get('state')
    provider = request.session.get('provider')

# ----- Get the Firestore document reference for the user settings ----- #
    if 'user_id' in request.session:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    else:
        messages.error(request, 'Please submit the above form.')
        return redirect('smm_form')
# ---------------------------------------------------------------------- #

    if provider == 'linkedin':
        isCheck = 'Linkedin'
        code = request.GET.get('code')
        access_token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        params = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri':  config("FUNNEL_REDIRECT_URI"),
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
                return render(request, 'funnel_page_selection_popup.html', {'pages': transformed_organizations, 'provider': provider,})
        pass
    elif provider == 'facebook':
        isCheck = 'Facebook'
        code = request.GET.get('code')
        access_token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
        params = {
            'client_id':  config("FACEBOOK_APP_ID"),
            'client_secret': config("FACEBOOK_APP_SECRET"),
            'redirect_uri':  config("FUNNEL_REDIRECT_URI"),
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
            return render(request, 'funnel_page_selection_popup.html', {'pages': facebook_pages_and_groups, 'provider': provider,})
        else:
            isFacebook = True
            facebook_page_id = facebook_pages_and_groups[0]['id'] if facebook_pages_and_groups else None
            facebook_page_token = facebook_pages_and_groups[0]['access_token'] if facebook_pages_and_groups else None
            facebook_page_type = facebook_pages_and_groups[0]['type'] if facebook_pages_and_groups else None
            facebook_page_name = facebook_pages_and_groups[0]['name'] if facebook_pages_and_groups else None
            if not all([facebook_page_id, facebook_page_token, facebook_page_type, facebook_page_name]):
                isFacebook = False
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
                'redirect_uri':  config("FUNNEL_REDIRECT_URI"),
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
                    return redirect('smm_form')
            except Exception as e:
                messages.error(request, 'Please make sure the instagram account is linked to the selected facebook account.')
                return redirect('smm_form')
        except Exception as e:
            messages.error(request, e)
            return redirect('smm_form')
    elif provider == 'google_business':
        isCheck = 'Google'
        code = request.GET.get('code')
        access_token_url = 'https://oauth2.googleapis.com/token'
        params = {
            'client_id':  config("GOOGLE_APP_ID"),
            'client_secret': config("GOOGLE_APP_SECRET"),
            'redirect_uri':  config("FUNNEL_REDIRECT_URI"),
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

    return redirect('smm_form')
    
def funnel_process_page_selection(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    if 'user_id' in request.session:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    else:
        messages.error(request, 'There was an error unlinking your profile.')
        return redirect('smm_form')
    # ---------------------------------------------------------------------- #

    selected_page_id = request.POST.get('pageId', None)
    provider = request.POST.get('provider', None)
    page_name = request.POST.get('pageName', None)
    page_token = request.POST.get('pageToken', None)
    page_type = request.POST.get('pageType', None)

    if not selected_page_id:
        messages.error(request, 'Please make sure the Instagram account is linked to the selected Facebook account.')
        return redirect('smm_form')
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
            return redirect('smm_form')
        elif provider == 'linkedin':
            firestore_data = {
                f'{provider}_id': selected_page_id,
                f'{provider}_name': page_name,
                'isLinkedin': True
            }       
            user_settings_ref.set(firestore_data, merge=True)
            messages.success(request, f"You've successfully connected your {provider} account!")
            return redirect('smm_form')
        else: 
            messages.error(request, 'There was an error connecting your account. Please try again.')
            return redirect('smm_form')

    
def funnel_unlink(request):
    if 'user_id' in request.session:
        user_id = request.session.get('user_id')
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
    else:
        messages.error(request, 'There was an error unlinking your profile.')
        return redirect('smm_form')
    
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
    return redirect('smm_form')
    