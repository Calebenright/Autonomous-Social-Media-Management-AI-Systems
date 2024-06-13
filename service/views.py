from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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

db = firestore.Client(project='feed-ai-c379d')

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
        if form_name == 'postToSocials':
            messages.error(request, 'Please upgrade to the Unlimited plan to post directly to your social medias.')
            return redirect('service_dashboard')
    
    context = {
        'user_settings': user_settings,
        'elaine_settings': elaine_settings,
        'user_id' : user_id,
    }
    return render(request, "service_dashboard.html", context)

def service_brand_settings(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        print('2')
        user_id = request.session.get('user_id')
        print('3')
        user_settings_ref = db.collection('users').document(user_id)
        global_variables_ref = db.collection('variables').document('global_variables')
        print('4')
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()
        print('5')
        pass
    
    except:
        return redirect('login') 
    # ---------------------------------------------------------------------- #s

    print('6')
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
    print('7')
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
        suggested_message = f"Your response has been received and one of our social media agents will get back to you soon.\n\nSincerely,\nCJ\n\nCJ | Marketing Agent @ Feadl.io\n407.516.6380\nExperience our platform: https://feadl.io/beta_signup/"

        to_user_email_message = EmailMessage(suggested_subject, suggested_message, from_email, [email])
        
        try:
            to_user_email_message.send()
            db.collection('service').document(email).update({'emailSent': True})

        except Exception as e:
            print(f"An error occurred: {e}")

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
        selectedPlan = request.POST.get('selectedPlan')
        if selectedPlan == 'plan1':
            selectedPlan = 'Basic'
        else:
            selectedPlan = 'Unlimited'
        bname = request.POST.get('business-name')
        bdesc = request.POST.get('business-description')
        color = request.POST.get('brand-color')

        print(selectedImage, selectedPlan, bname, bdesc, color)

        lead_ref.update({
            'selectedImage': selectedImage,
            'selectedPlan': selectedPlan,
            'business_name': bname,
            'business_description': bdesc,
            'color': color,
        })

        process_email(request, 'my_feadlio_success', 'my_feadlio', 'my_feadlio.html', bname, bdesc, color, selectedImage, selectedPlan, email)

        try:
            password = email.split('@')[0] + config("AGENCY_PASSWORD_ADDON")
            user = auth.create_user(email=email, password=password)
            doc_ref = db.collection('users').document(user.uid)
            firestore_data = {'isSubscriber': False, 'email': email, 'selectedPlan': selectedPlan, 'selectedImage': selectedImage, 'business_name': bname, 'business_description': bdesc, 'color': color, 'agency_id': 'ef6a81bf-6388-4cef-b522-e8fd9c667b0c', 'isAgency': True}
            doc_ref.set(firestore_data, merge=True)
            
            elaine_ref = db.collection('users').document(user.uid).collection('agents').document('elaine')
            elaine_data = {'scheduled_caption_1': 'Blog posts will be featured here without an image.', 'scheduled_caption_0': 'You can check your scheduled content in the schedule tab and make any changes necessary.', 'scheduled_image_1': '', 'scheduled_image_0': 'https://storage.googleapis.com/starter_web_app_bucket/assets/index.png'}
            elaine_ref.set(elaine_data, merge=True)

            request.session['user_id'] = user.uid
        except EmailAlreadyExistsError:
            messages.success(request, ("Please sign in with your email"))
            return redirect('login')
        except Exception as e:
            messages.error(request, ("An error occurred: {}".format(e)))
            return redirect('my_feadlio')
        
        return redirect('my_feadlio_success')
    
    context = {'lead': lead}
    return render(request, "my_feadlio.html", context)

def my_feadlio_success(request):
    return render(request, "my_feadlio_success.html")

def my_account_relink(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        request.session['email'] = email
        return redirect('my_account')

    return render(request, 'my_account_relink.html')

def my_account_stripe_redirect(request):
    email = request.session.get('email', None)
    if email:
        lead_ref = db.collection('service').document(email)
        lead_ref.update({'isSubscriber': True})
    return redirect('my_account')

def my_account(request):
    email = request.session.get('email', None)
    lead_ref = db.collection('service').document(email)
    lead = lead_ref.get().to_dict()

    if not email:
        return redirect('my_account_relink')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        business_name = request.POST.get('business_name')
        business_description = request.POST.get('business_description')


        firestore_data = {
            'email': email,
            'business_name': business_name,
            'business_description': business_description,
        }

        lead_ref.set(firestore_data, merge=True)
        messages.success(request, 'Your settings have been updated!')
        return redirect('my_account')
    
    context = {'lead': lead}
    return render(request, 'my_account.html', context)

def service_auth(request):
    if request.method == 'POST':
        
        if 'user_id' in request.session:
            user_id = request.session.get('user_id')
            user_settings_ref = db.collection('users').document(user_id)
            user_settings_doc = user_settings_ref.get()
            user_settings = user_settings_doc.to_dict()
            if user_settings.get('isSubscriber', False) == False:
                messages.error(request, 'Please upgrade to the Unlimited plan to post directly to your social medias.')
                return redirect('service_brand_settings')
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
    