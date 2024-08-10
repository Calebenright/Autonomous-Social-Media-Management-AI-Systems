from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.utils import timezone
from django.conf import settings
from google.cloud import storage, firestore
from google.oauth2 import service_account
from google.cloud.firestore_v1.base_query import FieldFilter
from google.auth.transport import requests
from urllib.parse import urlparse
from .post_to_socials import *
from django.http import JsonResponse
from .functions import *
from .chatbot import schedule_post, post_to_feed, add_graphics_from_bot
from firebase_admin import firestore, auth
import ast
import json
from .tasks import enqueue_task, auth_task, gc_task, create_queue
from .upload_article import *
from datetime import date, datetime, timedelta, timezone
import uuid
import random
import requests
from decouple import config
import stripe
import secrets
import pytz
import io
import imghdr
from openai import OpenAI
import logging
from django.contrib import messages
from .login import user_login

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

open_ai_client = OpenAI(api_key=config('OPENAI_API_KEY'))
assistant_ids = {'elaine': 'asst_L22Wc8ULhvjmE1uzNCVPXhU2', 'jerry': 'asst_Jna3iY12EQYZKpxmek5ptydv'}
db = firestore.Client(project=config('FIRESTORE_ID'))
stripe.api_key = config("STRIPE_SECRET_KEY")

# .............................................................
# .VVVV....VVVVVIIII.EEEEEEEEEEEEWWW..WWWWW...WWWW.SSSSSSS.....
# .VVVV....VVVVVIIII.EEEEEEEEEEEEWWW..WWWWW..WWWW.SSSSSSSSS....
# .VVVV....VVVVVIIII.EEEEEEEEEEEEWWW..WWWWWW.WWWW.SSSSSSSSSS...
# .VVVVV..VVVV.VIIII.EEEE.......EWWW.WWWWWWW.WWWWWSSSS..SSSS...
# ..VVVV..VVVV.VIIII.EEEE.......EWWW.WWWWWWW.WWWWWSSSS.........
# ..VVVV..VVVV.VIIII.EEEEEEEEEE..WWWWWWWWWWW.WWW..SSSSSSS......
# ..VVVVVVVVV..VIIII.EEEEEEEEEE..WWWWWWW.WWWWWWW...SSSSSSSSS...
# ...VVVVVVVV..VIIII.EEEEEEEEEE..WWWWWWW.WWWWWWW.....SSSSSSS...
# ...VVVVVVVV..VIIII.EEEE........WWWWWWW.WWWWWWW........SSSSS..
# ...VVVVVVV...VIIII.EEEE........WWWWWWW.WWWWWWW.WSSS....SSSS..
# ....VVVVVV...VIIII.EEEEEEEEEEE..WWWWW...WWWWW..WSSSSSSSSSSS..
# ....VVVVVV...VIIII.EEEEEEEEEEE..WWWWW...WWWWW...SSSSSSSSSS...
# ....VVVVV....VIIII.EEEEEEEEEEE..WWWWW...WWWWW....SSSSSSSS....
# .............................................................

def dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    db_ref = db.collection('users').document(user_id)
    user_settings = db_ref.get().to_dict() or {}
    global_variables = db.collection('variables').document('global_variables').get().to_dict() or {}

    elaine_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'elaine')
    elaine_settings = (elaine_doc_ref.get().to_dict() or []) if elaine_doc_ref.get().exists else []

    jerry_doc_ref = db.collection(u'users').document(user_id).collection(u'agents').document(u'jerry')
    jerry_settings = (jerry_doc_ref.get().to_dict() or []) if jerry_doc_ref.get().exists else []

    try:
        user_email = auth.get_user(user_id).email if user_id else ''
    except:
        user_email = user_settings.get('email', '')
        
    user_settings_strings = {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in user_settings.items()
    }

    all_messages = request.session.get('all_messages', [])
    
    if request.method == 'POST':
        form_name = request.POST.get('form')
        if form_name == 'formFtue':
            business_name = request.POST.get('business_name')
            business_description = request.POST.get('business_description')
            brand_color = all_color_to_hex(request.POST.get('brand_color'))
            colors = generate_secondary_colors(brand_color)
            tags = create_tags(business_description)

            firestore_data = {
                'tags': tags,
                'business_description': business_description,
                'business_name': business_name,
                'brand_color': brand_color,
                'secondary_colors' : colors,
                'ftue': True,
                'isAutomated': False,
                'isLogo': False,
                'images_generated': 0,
                'monthly_images_generated': 0,
                'progress': 100,
                'admin': False,
                'isBusiness': False,
                'email': user_email,
                'num_sent': 0,
                'last_reset_time': datetime.now(),
                'trial': 0,
            }

            db_ref.set(firestore_data, merge=True)

            elaine_data = {
                'posts_per_week': 2,
                'text_weight': 35,
                'stock_weight': 65,
                'graphic_weight': 0,
                'combined_weight': 100,
                'ElaineSocialMedias': [],
                'ElainePostType': ["Text Post","Stock Photo Post"],
                'isElaineEmail': False,
                'ElaineTimezone': 'America/Chicago',
            }

            elaine_doc_ref.set(elaine_data, merge=True)
            messages.success(request, 'Settings have been successfully updated!')
            return redirect('dashboard')
        
        elif form_name == 'elaine-settings':
            text_weight = request.POST.get('textWeight')
            stock_weight = int(request.POST.get('stockWeight')) - int(text_weight)
            graphic_weight = 100 - (int(text_weight) + int(stock_weight))

            isElaineEmail = request.POST.get('isElaineEmail') == "on"
            
            elaine_data = {
                'posts_per_week': int(request.POST.get('posts_per_week', 0)),
                'text_weight': int(text_weight),
                'stock_weight': int(stock_weight),
                'graphic_weight': int(graphic_weight),
                'combined_weight': int(text_weight) + int(stock_weight),
                'ElaineSocialMedias': request.POST.getlist('ElaineSocialMedias[]'),
                'ElainePostType': request.POST.getlist('ElainePostType[]'),
                'isElaineEmail': isElaineEmail,
                'ElaineEmail': request.POST.get('ElaineEmail'),
                'ElaineTimezone': request.POST.get('ElaineTimezone'),
            }

            isElaineOn = request.POST.get('isElaineOn') == "on"
            elaine_data['isElaineOn'] = isElaineOn
            firestore_data = {'isAutomated': isElaineOn}
            db_ref.set(firestore_data, merge=True)

            # if isElaineOn and not elaine_settings.get('isElaineOn', False):
            #     if not user_settings.get('isAgency', True):
            #         send_new_subscriber_email(elaine_data['ElaineEmail'], user_settings.get('business_description'), user_settings.get('business_name'), 'Elaine')

            elaine_doc_ref.set(elaine_data, merge=True)

            messages.success(request, 'Settings have been successfully updated!')
            return redirect('dashboard')
        
        elif form_name == 'jerry-settings':
            jerry_data = {
                'JerryEmail': request.POST.get('JerryEmail'),
                'JerryAdDescription': request.POST.get('JerryAdDescription'),
                'isJerryOn': request.POST.get('isJerryOn') == "True"
            }

            jerry_doc_ref.set(jerry_data, merge=True)
            messages.success(request, 'Settings have been successfully updated!')
            return redirect('dashboard')
        
    context = {
        'user_settings_json': json.dumps(user_settings_strings),
        'all_messages': all_messages,
        'user_settings': user_settings,
        'user_id' : user_id,
        'elaine_settings': elaine_settings,
        'jerry_settings': jerry_settings,
        'global_variables': global_variables
    }
    
    return render(request, 'dashboard.html', context)

# ---------------- chats ---------------- #

def start_chat(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
        user_id = request.session.get('user_id')
        user_settings_doc = db.collection('users').document(user_id).get()
        user_settings = user_settings_doc.to_dict()
    except:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    # ---------------------------------------------------------------------- #

    if request.method == "POST":

        platforms = [p for p in ['Facebook', 'Instagram'] if user_settings.get(f'is{p}')]

        character = request.POST.get('character')
        assistant_id = assistant_ids.get(character)
        thread_id = request.session.get('thread_id', open_ai_client.beta.threads.create().id)
        request.session['thread_id'] = thread_id
        user_input = request.POST.get('message')
        request.session['user_input'] = user_input

        message_context = f"[Ignore but remember this context for this user then answer the response: business name={user_settings['business_name']}, business description={user_settings['business_description']}, social_media_platforms={platforms}]"
        
        try:
            open_ai_client.beta.threads.messages.create(thread_id=thread_id, role="user", content=message_context + user_input)
            run = open_ai_client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
        except:
            open_ai_client.beta.threads.runs.cancel(thread_id=thread_id, run_id=request.session.get('run_id'))
            open_ai_client.beta.threads.messages.create(thread_id=thread_id, role="user", content=message_context + user_input)
            run = open_ai_client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

        request.session['run_id'] = run.id

        return JsonResponse({'status': 'pending', 'thread_id': thread_id, 'run_id': run.id})
    else:
        return JsonResponse({'error': 'Invalid request. If this error persists, please contact us at https://feadl.io/contact/.'}, status=400)


def get_chat(request):

    try:
        # ----- Get the Firestore document reference for the user settings ----- #
        user_id = request.session.get('user_id')
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
            return JsonResponse({'error': 'Error getting variuables.'}, status=400)
        # ---------------------------------------------------------------------- #
        pass
    
    except:
        return JsonResponse({'error': 'Error logging in user.'}, status=400)
    # ---------------------------------------------------------------------- #

    if request.method == "GET":
        assistant_id = assistant_ids.get('elaine')
        assistant = open_ai_client.beta.assistants.retrieve(assistant_id)

        user_input = request.session.get('user_input')
        all_messages = request.session.get('all_messages', [{'role': 'bot', 'content': 'How can I help you?'}])
        bot_url = request.session.get('bot_url', False)
        thread_id = request.session.get('thread_id')
        run_id = request.session.get('run_id')
    
        run = open_ai_client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

        url = ''
        caption = ''

        if run.status == 'completed':
            messages = open_ai_client.beta.threads.messages.list(thread_id=thread_id)
            all_messages.append({'role': 'user', 'content': user_input})
            if bot_url:
                all_messages.append({'role': 'bot', 'content': f'![Generated Image]({bot_url})'})
                request.session['bot_url'] = False
            if messages:
                messages_list = messages.data
                if messages_list:
                    last_message_content = messages_list[0].content[0].text.value
                    formatted_message = last_message_content
                    all_messages.append({'role': 'bot', 'content': formatted_message})
                    request.session['last_message'] = formatted_message

            request.session['all_messages'] = all_messages

            return JsonResponse({
                'all_messages': all_messages,
                'botMessage': formatted_message,
                'status': 'completed',
                'url': bot_url,
            })
        
        elif run.status == 'requires_action':
            required_action = run.required_action.submit_tool_outputs.model_dump()
            tools_output = []
            if required_action["tool_calls"]:
                action = required_action["tool_calls"][0]
                function_name = action["function"]["name"]
                arguments = json.loads(action["function"]["arguments"])
                if function_name == "get_social_media_graphic_post":
                    image_tags = json.loads(user_settings.get('image_tags', '[]'))
                    random_image_url = random.choice(image_tags)
                    if image_tags == []:
                        tools_output.append({
                            "tool_call_id": action["id"],
                            "output": "Tell the user that they need to add images to their library first.",
                        })

                        images_generated = user_settings['images_generated'] + 0.1

                        open_ai_client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tools_output
                        )

                        return JsonResponse({
                            'status': 'requires_action',
                            'function_name': function_name,
                            'url': url,
                            'caption': caption
                        })
                    edit = add_graphics_from_bot(random_image_url, user_settings, user_settings_ref, global_variables, 'graphic')
                    img = download_and_save_image_as_seek(edit)
                    url = upload_png_to_google(img, config("GS_BUCKET_NAME"), config("GS_CREDENTIALS"), 'delete_image_library/')
                    caption = create_caption(user_settings['business_description'], user_settings['business_name'])
                    tools_output.append({
                        "tool_call_id": action["id"],
                        "output": "image url for reference but do not show: " + url + "Caption: " + caption,
                        })
                    images_generated = user_settings['images_generated'] + 1
                    request.session['bot_url'] = url
                elif function_name == "get_stock_photo_post":
                    image_tags = json.loads(user_settings.get('image_tags', '[]'))
                    random_image_url = random.choice(image_tags)
                    if image_tags == []:
                        tools_output.append({
                        "tool_call_id": action["id"],
                        "output": "Tell the user that they need to add images to their library first.",
                        })
                        images_generated = user_settings['images_generated'] + 0.1
                        open_ai_client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tools_output
                        )

                        return JsonResponse({
                            'status': 'requires_action',
                            'function_name': function_name,
                            'url': url,
                            'caption': caption
                        })
                    
                    caption = create_caption(user_settings['business_description'], user_settings['business_name'])
                    edit = add_graphics_from_bot(random_image_url, user_settings, user_settings_ref, global_variables, 'photo')
                    img = download_and_save_image_as_seek(edit)
                    url = upload_png_to_google(img, config("GS_BUCKET_NAME"), config("GS_CREDENTIALS"), 'delete_image_library/')
                    tools_output.append({
                        "tool_call_id": action["id"],
                        "output": "image url for reference but do not show: " + url + "Caption: " + caption,
                        })
                    images_generated = user_settings['images_generated'] + 0.3
                    request.session['bot_url'] = url
                elif function_name == "get_stock_ad":
                    image_tags = json.loads(user_settings.get('image_tags', '[]'))
                    random_image_url = random.choice(image_tags)
                    if image_tags == []:
                        tools_output.append({
                        "tool_call_id": action["id"],
                        "output": "Tell the user that they need to add images to their library first.",
                        })
                        images_generated = user_settings['images_generated'] + 0.1
                        open_ai_client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tools_output
                        )

                        return JsonResponse({
                            'status': 'requires_action',
                            'function_name': function_name,
                            'url': url,
                            'caption': caption
                        })
                    
                    caption = create_ad_copy(user_settings['business_description'], user_settings['business_name'])
                    edit = add_graphics_from_bot(random_image_url, user_settings, user_settings_ref, global_variables, 'ad')
                    img = download_and_save_image_as_seek(edit)
                    url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), 'delete_image_library/')
                    tools_output.append({
                        "tool_call_id": action["id"],
                        "output": "image url for reference but do not show: " + url + "Caption: " + caption,
                        })
                    images_generated = user_settings['images_generated'] + 0.3
                    request.session['bot_url'] = url
                elif function_name == "post_to_feed":
                    url = arguments["url"]
                    caption = arguments["caption"]
                    platforms = arguments["platforms"]
                    post_type = arguments["post_type"]
                    post_to_feed(url, caption, platforms, post_type, user_settings, user_settings_ref, global_variables)
                    tools_output.append({
                        "tool_call_id": action["id"],
                        "output": f"Successfully posted to {platforms}",
                        })
                    images_generated = user_settings['images_generated']
                elif function_name == "schedule_post":
                    url = arguments["url"]
                    caption = arguments["caption"]
                    platforms = arguments["platforms"]
                    date_and_time = ''
                    post_type = arguments["post_type"]
                    post_details = schedule_post(url, caption, platforms, date_and_time, user_settings, user_settings_ref, post_type, elaine_settings.get('ElaineTimezone'))
                    tools_output.append({
                        "tool_call_id": action["id"],
                        "output": f"Here are the post details, only display the relevant info like date and socials: {post_details}",
                        })
                    images_generated = user_settings['images_generated']
                else:
                    url = 'There was an error'
                    caption = 'There was an error'
                    function_name = 'There was an error'
                    tools_output.append({
                        "tool_call_id": action["id"],
                        "output": "There was an error",
                        })
                    
            open_ai_client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tools_output
            )

            firestore_data = {'images_generated': images_generated}
            user_settings_ref.set(firestore_data, merge=True)

            return JsonResponse({
                'status': 'requires_action',
                'function_name': function_name,
                'url': url,
                'caption': caption
                })
        else:
            return JsonResponse({'status': 'pending'})

    else:
        return JsonResponse({'error': 'Invalid request. If the problem persists, please contact us at https://feadl.io/contact/'}, status=400)

def clear_chat(request):
    keys_to_clear = [
        'thread_id', 'run_id', 'user_input', 'all_messages'
    ]

    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    return JsonResponse({'success': 'cleared'})

def add_graphics(request):
    try:
        # ----- Get the Firestore document reference for the user settings ----- #
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

    image_folder_path = f'user_folders/{user_id}/image_posts/'
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
                random_int = random.randint(global_variables.get('random_int_min'), global_variables.get('random_int_max'))
                color = user_settings.get('brand_color')
                secondary_colors = ast.literal_eval(user_settings.get('secondary_colors'))
                img = create_call_to_action(biz, biz_name, color, secondary_colors, next_image_url, random_int, logo_path, isLogo)
                url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path)
            elif selected_option == 'ad':
                random_int = random.randint(global_variables['random_ad_int_min'], global_variables['random_ad_int_max'])
                color = user_settings['brand_color']
                secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
                img = create_ad_creative(key, biz_name, color, secondary_colors, next_image_url, random_int, logo_path, isLogo)
                url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path)
            elif selected_option == 'photo':
                if isLogo and logo_path is not None:
                    image_data = add_logo(next_image_url, logo_path)
                else:
                    image_data = download_and_save_image_as_seek(next_image_url)
                url = upload_png_to_google(image_data, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path)
            else:
                url = next_image_url
            firestore_data = {'next_image_url': url, 'progress': 100}
            user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'url': url})
    return JsonResponse({'status': 'nothing'})


def callback(request):
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
                return render(request, 'page_selection_popup.html', {'pages': transformed_organizations, 'provider': provider,})
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
            return render(request, 'page_selection_popup.html', {'pages': facebook_pages_and_groups, 'provider': provider,})
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
                    return redirect('service:settings')
            except Exception as e:
                messages.error(request, 'Please make sure the instagram account is linked to the selected facebook account.')
                return redirect('service:settings')
        except Exception as e:
            messages.error(request, e)
            return redirect('service:settings')
        
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

    return redirect('service:settings')
    


# ...................................................................
# ......................AAAAA.....PPPPPPPPP..PIIII...................
# ......................AAAAA.....PPPPPPPPPP.PIIII...................
# .....................AAAAAA.....PPPPPPPPPPPPIIII...................
# .....................AAAAAAA....PPPP...PPPPPIIII...................
# ....................AAAAAAAA....PPPP...PPPPPIIII...................
# ....................AAAAAAAA....PPPPPPPPPPPPIIII...................
# ....................AAAA.AAAA...PPPPPPPPPP.PIIII...................
# ...................AAAAAAAAAA...PPPPPPPPP..PIIII...................
# ...................AAAAAAAAAAA..PPPP.......PIIII...................
# ...................AAAAAAAAAAA..PPPP.......PIIII...................
# ..................AAAA....AAAA..PPPP.......PIIII...................
# ..................AAAA.....AAAA.PPPP.......PIIII...................
# ..................AAAA.....AAAA.PPPP.......PIIII...................
# ...................................................................


API_TOKEN = config("API_TOKEN")

@csrf_exempt  
@require_http_methods(["POST"])
def elaine_generate_post(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {API_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        request_json = json.loads(request.body)
        uid = request_json.get('uid')
    except Exception as e:
        return JsonResponse({'error': f'Bad request: {str(e)}'}, status=400)

    if not uid:
        return JsonResponse({'error': 'Missing uid'}, status=400)

    try:
        user_settings_ref = db.collection('users').document(uid)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()

        elaine_doc_ref = db.collection(u'users').document(uid).collection(u'agents').document(u'elaine')
        elaine_doc = elaine_doc_ref.get()

        if elaine_doc.exists:
            elaine_settings = elaine_doc.to_dict()
        else:
            elaine_settings = {'posts_per_week': 0}
            elaine_doc_ref.set(elaine_settings, merge=True)

        posts_per_week = elaine_settings.get('posts_per_week', 0)

        if posts_per_week > 0:
            payload = {"uid": uid}
            create_queue(uid)
            gc_task(payload, uid, config("GS_CREATE_POSTS_PER_WEEK"))

        return HttpResponse("Tasks completed successfully, Elaine settings retrieved.", status=200)
    except Exception as e:
        return JsonResponse({'error': f'Failed to retrieve Elaine settings: {str(e)}'}, status=500)
    
@csrf_exempt  
@require_http_methods(["POST"])
def elaine_email(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {API_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        request_json = json.loads(request.body)
        uid = request_json.get('uid')
        if not uid:
            raise ValueError("Missing uid")
    except Exception as e:
        return JsonResponse({'error': f'Bad request: {str(e)}'}, status=400)

    db = firestore.Client(project='feed-ai-c379d')

    user_settings = db.collection('users').document(uid).get().to_dict()
    character = "CJ" if user_settings.get('isAgencyUser') else "elaine"
    owner = user_settings.get('firstName')
    elaine_doc = db.collection('users').document(uid).collection('agents').document('elaine').get().to_dict()

    def get_week_date_range():
        start_of_week = date.today() - timedelta(days=date.today().weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return f"{start_of_week.strftime('%b %d')} to {end_of_week.strftime('%b %d')}"

    prompts = []
    captions = []

    for i in range(elaine_doc.get(f'posts_per_week')):
        try:
            caption = elaine_doc.get(f'scheduled_caption_{i}')
            captions.append(caption)
        except Exception as e:
            print(f"Error processing info {i}: {e}")
    
    email = elaine_doc.get(f'ElaineEmail', user_settings.get('email'))
    week_date_range = get_week_date_range()
    subject = f'Social Media Report - {week_date_range}'
    message = create_email(user_settings.get('business_description'), user_settings.get('business_name'), character, owner)
    from_email = config("EMAIL_HOST_USER")
    recipient_list = [email]

    text_content = message + "\n--\nPlease see the attached images and their corresponding captions:\n"

    for i in range(elaine_doc.get('posts_per_week', 0)):
        caption = elaine_doc.get(f'scheduled_caption_{i}')
        if caption:
            text_content += f'\n\nPost #{i+1}: {caption}'

    email_message = EmailMessage(subject, text_content, from_email, recipient_list)
    email_message.content_subtype = "plain" 

    for i in range(elaine_doc.get('posts_per_week', 0)):
        image_url = elaine_doc.get(f'scheduled_image_{i}')
        if image_url:
            response = requests.get(image_url)
            if response.status_code == 200:
                email_message.attach(f'image_{i}.jpg', response.content, 'image/jpeg')
            else:
                print(f"Failed to download image {i}: Status code {response.status_code}")

    email_message.send()

    return JsonResponse({'success': "Email successfully sent to user."}, status=200)

@csrf_exempt  
@require_http_methods(["POST"])
def add_graphics_api(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {API_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        request_json = json.loads(request.body)
        uid = request_json.get('uid')
        img_url = request_json.get('img_url')
        selected_option = request_json.get('selected_option')

        db = firestore.Client(project='feed-ai-c379d')

        global_variables_ref = db.collection('variables').document('global_variables')
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()

        user_settings_ref = db.collection('users').document(uid)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()

        if selected_option == 'random':
            selected_option = random.choice(['graphic', 'ad'])
        
        edit = add_graphics_from_bot(img_url, user_settings, user_settings_ref, global_variables, selected_option)
        img = download_and_save_image_as_seek(edit)
        url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), f"user_folders/{uid}/scheduled_image_library/")

        return JsonResponse({'url': url}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'Exception: {e}'}, status=400)
    

@csrf_exempt  
@require_http_methods(["POST"])
def elaine_functions(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {API_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        request_json = json.loads(request.body)
        uid = request_json.get('uid')
        post = request_json.get('post')
        function_name = request_json.get('function_name')

    except Exception as e:
        return JsonResponse({'error': f'Exception: {e}'}, status=400)

    if not uid:
        return JsonResponse({'error': 'Missing uid'}, status=400)

    try:
        db = firestore.Client(project='feed-ai-c379d')

        global_variables_ref = db.collection('variables').document('global_variables')
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()

        user_settings_ref = db.collection('users').document(uid)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        
        elaine_doc_ref = db.collection(u'users').document(uid).collection(u'agents').document(u'elaine')
        elaine_doc = elaine_doc_ref.get()
        elaine_settings = elaine_doc.to_dict()

        image_tags = json.loads(user_settings.get('image_tags', '[]'))
        tags = ast.literal_eval(user_settings.get('tags', '[]'))

        if image_tags == []:
            function_name = "get_text_post"
        else:
            random_image_url = random.choice(image_tags)

        random_tag = random.choice(tags) if tags else None
        business_description = user_settings.get("business_description")
        post_type = 'image'

        if function_name == "get_ai_post":
            img_url = get_image(create_stock_image_description(business_description))
            edit = add_graphics_from_bot(img_url, user_settings, user_settings_ref, global_variables, 'graphic')
            img = download_and_save_image_as_seek(edit)
            url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), f"user_folders/{uid}/scheduled_image_library/")
            caption = create_caption(user_settings['business_description'], user_settings['business_name'])
        elif function_name == "get_library_post":
            edit = add_graphics_from_bot(random_image_url, user_settings, user_settings_ref, global_variables, 'graphic')
            img = download_and_save_image_as_seek(edit)
            url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), f"user_folders/{uid}/scheduled_image_library/")
            caption = create_caption(user_settings['business_description'], user_settings['business_name'])
        elif function_name == "get_ai_image":
            img_url = get_image(create_stock_image_description(business_description))
            edit = add_graphics_from_bot(img_url, user_settings, user_settings_ref, global_variables, 'photo')
            img = download_and_save_image_as_seek(edit)
            url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), f"user_folders/{uid}/scheduled_image_library/")
            caption = create_caption(user_settings['business_description'], user_settings['business_name'])
        elif function_name == "get_stock_image":
            img_url = create_unsplash_post(create_stock_image_description(random_tag))
            edit = add_graphics_from_bot(img_url, user_settings, user_settings_ref, global_variables, 'photo')
            img = download_and_save_image_as_seek(edit)
            url = upload_png_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), f"user_folders/{uid}/scheduled_image_library/")
            caption = create_caption(user_settings['business_description'], user_settings['business_name'])
        elif function_name == "get_text_post":
            post_type = 'text'
            url = ''
            caption = create_text_post('Social media', business_description, user_settings['business_name'])

        event_id = uuid.uuid4()
        eid = str(event_id)

        eventDocRef = user_settings_ref.collection('events').document(eid)

        existing_events = user_settings_ref.collection('events').order_by('start').stream()
        existing_event_times = []
        for event in existing_events:
            event_data = event.to_dict()
            if 'start' in event_data:
                existing_event_times.append(event_data['start'])

        facebook_checked = user_settings.get('isFacebook', False)
        instagram_checked = user_settings.get('isInstagram', False)

        socials = [platform for platform, checked in [
            ('facebook', facebook_checked),
            ('instagram', instagram_checked)
        ] if checked]

        if not socials:
            elaine_settings = {f'scheduled_image_{post}': url, f'scheduled_caption_{post}': caption}
            elaine_doc_ref.set(elaine_settings, merge=True)

            return HttpResponse("Tasks completed successfully, Elaine settings retrieved.", status=200)
        
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
            'caption': caption,
            'className': 'bg-success',
            'socials': socials,
            'type' : post_type,
            'status': 'pending'
        }
        
        eventDocRef.set(event_data, merge=True)

        elaine_settings = {f'scheduled_image_{post}': url, f'scheduled_caption_{post}': caption}
        elaine_doc_ref.set(elaine_settings, merge=True)

        return HttpResponse("Tasks completed successfully, Elaine settings retrieved.", status=200)
    except Exception as e:
        return JsonResponse({'error': f'Failed to retrieve Elaine settings: {str(e)}'}, status=500)
    

@csrf_exempt  
@require_http_methods(["POST"])
def automated_email(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {API_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        request_json = json.loads(request.body)
        to_email = request_json.get('to_email')
        subject = request_json.get('subject')
        message = request_json.get('message')

        db = firestore.Client(project='feed-ai-c379d')

        from_email = config("EMAIL_HOST_USER")
        recipient_list = [to_email]
        to_user_email_message = EmailMessage(subject, message, from_email, [to_email])
        to_user_email_message.send()
        
        return JsonResponse({'success': 'Task completed'}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'Exception: {e}'}, status=400)
    
# ..............................................................................................................
# ....CCCCCCC....RRRRRRRRRR.....OOOOOOO.....NNNN...NNNN...........JJJJ....OOOOOOO.....BBBBBBBBBB....SSSSSSS.....
# ...CCCCCCCCC...RRRRRRRRRRR...OOOOOOOOOO...NNNNN..NNNN...........JJJJ...OOOOOOOOOO...BBBBBBBBBBB..SSSSSSSSS....
# ..CCCCCCCCCCC..RRRRRRRRRRR..OOOOOOOOOOOO..NNNNN..NNNN...........JJJJ..OOOOOOOOOOOO..BBBBBBBBBBB..SSSSSSSSSS...
# ..CCCC...CCCCC.RRRR...RRRRR.OOOOO..OOOOO..NNNNNN.NNNN...........JJJJ..OOOOO..OOOOO..BBBB...BBBB.BSSSS..SSSS...
# .CCCC.....CCC..RRRR...RRRRROOOOO....OOOOO.NNNNNN.NNNN...........JJJJ.JOOOO....OOOOO.BBBB...BBBB.BSSSS.........
# .CCCC..........RRRRRRRRRRR.OOOO......OOOO.NNNNNNNNNNN...........JJJJ.JOOO......OOOO.BBBBBBBBBBB..SSSSSSS......
# .CCCC..........RRRRRRRRRRR.OOOO......OOOO.NNNNNNNNNNN...........JJJJ.JOOO......OOOO.BBBBBBBBBB....SSSSSSSSS...
# .CCCC..........RRRRRRRR....OOOO......OOOO.NNNNNNNNNNN...........JJJJ.JOOO......OOOO.BBBBBBBBBBB.....SSSSSSS...
# .CCCC.....CCC..RRRR.RRRR...OOOOO....OOOOO.NNNNNNNNNNN......JJJJ.JJJJ.JOOOO....OOOOO.BBBB....BBBB.......SSSSS..
# ..CCCC...CCCCC.RRRR..RRRR...OOOOO..OOOOO..NNNN.NNNNNN......JJJJ.JJJJ..OOOOO..OOOOO..BBBB....BBBBBSSS....SSSS..
# ..CCCCCCCCCCC..RRRR..RRRRR..OOOOOOOOOOOO..NNNN..NNNNN......JJJJJJJJJ..OOOOOOOOOOOO..BBBBBBBBBBBBBSSSSSSSSSSS..
# ...CCCCCCCCCC..RRRR...RRRRR..OOOOOOOOOO...NNNN..NNNNN......JJJJJJJJ....OOOOOOOOOO...BBBBBBBBBBB..SSSSSSSSSS...
# ....CCCCCCC....RRRR....RRRR....OOOOOO.....NNNN...NNNN.......JJJJJJ.......OOOOOO.....BBBBBBBBBB....SSSSSSSS....
# ..............................................................................................................


CRON_TOKEN = config("CRON_TOKEN")

@csrf_exempt  
@require_http_methods(["POST"])
def feadlio_automatic_manager_task_creator(request):
    logger.info("Processing request to create tasks.")
    token = request.headers.get('Authorization')
    if token != f"Bearer {CRON_TOKEN}":
        logger.warning("Unauthorized attempt to access the function.")
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    users_ref = db.collection(u'users')
    docs = users_ref.stream()

    for doc in docs:
        user = doc.to_dict()
        if user.get('isAutomated'):
            payload = {"uid": doc.id}
            create_queue(doc.id)
            auth_task(payload, doc.id, config("ELAINE_GENERATE_IMAGE"))
            logger.info(f"Task created for user ID: {doc.id}")
    
    logger.info("All tasks created successfully.")
    return HttpResponse("Tasks created successfully", status=200)


@csrf_exempt  
@require_http_methods(["POST"])
def master_automatic_manager_task_creator(request):
    logger.info("Processing request to create tasks.")
    token = request.headers.get('Authorization')
    if token != f"Bearer {CRON_TOKEN}":
        logger.warning("Unauthorized attempt to access the function.")
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    user_ref = db.collection(u'users').document(config('MASTER_ID'))
    doc = user_ref.get()
    if doc.exists:
        user = doc.to_dict()
        if user.get('isAutomated'):
            payload = {"uid": doc.id}
            create_queue(doc.id)
            auth_task(payload, doc.id, config("ELAINE_GENERATE_IMAGE"))
            logger.info(f"Task created for user ID: {doc.id}")
            return HttpResponse("Task created successfully for user ID: " + doc.id, status=200)
        else:
            return HttpResponse("No action taken. User is not set for automation.", status=200)
    else:
        return HttpResponse("User ID 'Blk23fw44' not found.", status=404)

@csrf_exempt  
@require_http_methods(["POST"])
def cron_reset_monthly_limits(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {CRON_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    users_ref = db.collection(u'users')
    
    batch = db.batch()
    for user in users_ref.stream():

        user_data = user.to_dict()
        current_usage = user_data.get("monthly_images_generated", 0)
        
        updates = {
            "last_month_images_generated": current_usage,
            "monthly_images_generated": 0,
        }
        
        batch.update(user.reference, updates)
    
    batch.commit()
    return HttpResponse("Limits Reset", status=200)

@csrf_exempt  
@require_http_methods(["POST"])
def cron_auto_add_article(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {CRON_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    collection_name = 'articles'
    topic = 'online marketing, soloprenuer, service based business, Dallas TX'

    title = create_title(topic)
    content = create_article(title)

    key = 'Social Media management, Dallas Texas'
    img = pull_stock(key)

    article_data = {
        'title': title,
        'content': content,
        'publishedDate': firestore.SERVER_TIMESTAMP,
        'slug': generate_slug(title),
        'image': img
    }

    add_document_auto_id(collection_name, article_data)

    return HttpResponse("Article Added", status=200)

@csrf_exempt  
@require_http_methods(["POST"])
def cron_delete_images_in_gcp_folder(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {CRON_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    bucket_name = config("GS_BUCKET_NAME")
    folder_path = 'delete_image_library/'
    storage_client = storage.Client(project='starter-web-app-389316')
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_path)
    deleted_files = []
    try:
        for blob in blobs:
            blob.delete()
            deleted_files.append(blob.name)
        logger.info(f"Deleted files: {deleted_files}")
    except Exception as e:
        logger.error(f"Error deleting files: {e}", severity="ERROR")
        return HttpResponse("An error occurred while deleting images.", status=500)

    return HttpResponse("Images deleted successfully", status=200)

@csrf_exempt  
@require_http_methods(["POST"])
def cron_inactive_users(request):
    token = request.headers.get('Authorization')
    if token != f"Bearer {CRON_TOKEN}":
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    all_users = auth.list_users().iterate_all()
    for user in all_users:
        try:
            doc_ref = db.collection('users').document(user.uid)
            doc = doc_ref.get()

            if not doc.exists or (doc.exists and ('ftue' not in doc.to_dict() or doc.to_dict().get('ftue') is False)):
                auth.delete_user(user.uid)
                
                if doc.exists:
                    doc_ref.delete()

        except Exception as e:
            print(f"Error processing user {user.uid}: {e}")

    return HttpResponse("Users deleted successfully", status=200)


# .........................................................................................................................................................................
# ...SSSSSSS....TTTTTTTTTTTRRRRRRRRRR..IIIII.PPPPPPPPP...EEEEEEEEEEE.... WWW..WWWWW...WWWWEEEEEEEEEEE.BBBBBBBBBB...HHHH...HHHH....OOOOOOO.......OOOOOOO.....KKKK...KKKKK..
# ..SSSSSSSSS...TTTTTTTTTTTRRRRRRRRRRR.IIIII.PPPPPPPPPP..EEEEEEEEEEE..... WWW..WWWWW..WWWW.EEEEEEEEEEE.BBBBBBBBBBB..HHHH...HHHH...OOOOOOOOOO....OOOOOOOOOO...KKKK..KKKKK...
# ..SSSSSSSSSS..TTTTTTTTTTTRRRRRRRRRRR.IIIII.PPPPPPPPPPP.EEEEEEEEEEE..... WWW..WWWWWW.WWWW.EEEEEEEEEEE.BBBBBBBBBBB..HHHH...HHHH..OOOOOOOOOOOO..OOOOOOOOOOOO..KKKK.KKKKK....
# .SSSSS..SSSS.....TTTT....RRRR...RRRRRIIIII.PPPP...PPPP.EEEE............ WWW.WWWWWWW.WWWW.EEEE........BBBB...BBBB..HHHH...HHHH..OOOOO..OOOOO..OOOOO..OOOOO..KKKKKKKKK.....
# .SSSSS...........TTTT....RRRR...RRRRRIIIII.PPPP...PPPP.EEEE............ WWW.WWWWWWW.WWWW.EEEE........BBBB...BBBB..HHHH...HHHH.HOOOO....OOOOOOOOOO....OOOOO.KKKKKKKK......
# ..SSSSSSS........TTTT....RRRRRRRRRRR.IIIII.PPPPPPPPPPP.EEEEEEEEEE.......WWWWWWWWWWW.WWW..EEEEEEEEEE..BBBBBBBBBBB..HHHHHHHHHHH.HOOO......OOOOOOOO......OOOO.KKKKKKKK......
# ...SSSSSSSSS.....TTTT....RRRRRRRRRRR.IIIII.PPPPPPPPPP..EEEEEEEEEE.......WWWWWWW.WWWWWWW..EEEEEEEEEE..BBBBBBBBBB...HHHHHHHHHHH.HOOO......OOOOOOOO......OOOO.KKKKKKKK......
# .....SSSSSSS.....TTTT....RRRRRRRR....IIIII.PPPPPPPPP...EEEEEEEEEE.......WWWWWWW.WWWWWWW..EEEEEEEEEE..BBBBBBBBBBB..HHHHHHHHHHH.HOOO......OOOOOOOO......OOOO.KKKKKKKKK.....
# ........SSSSS....TTTT....RRRR.RRRR...IIIII.PPPP........EEEE.............WWWWWWW.WWWWWWW..EEEE........BBBB....BBBB.HHHH...HHHH.HOOOO....OOOOOOOOOO....OOOOO.KKKK.KKKKK....
# .SSSS....SSSS....TTTT....RRRR..RRRR..IIIII.PPPP........EEEE.............WWWWWWW.WWWWWWW..EEEE........BBBB....BBBB.HHHH...HHHH..OOOOO..OOOOO..OOOOO..OOOOO..KKKK..KKKK....
# .SSSSSSSSSSSS....TTTT....RRRR..RRRRR.IIIII.PPPP........EEEEEEEEEEE.......WWWWW...WWWWW...EEEEEEEEEEE.BBBBBBBBBBBB.HHHH...HHHH..OOOOOOOOOOOO..OOOOOOOOOOOO..KKKK..KKKKK...
# ..SSSSSSSSSS.....TTTT....RRRR...RRRRRIIIII.PPPP........EEEEEEEEEEE.......WWWWW...WWWWW...EEEEEEEEEEE.BBBBBBBBBBB..HHHH...HHHH...OOOOOOOOOO....OOOOOOOOOO...KKKK...KKKKK..
# ...SSSSSSSS......TTTT....RRRR....RRRRIIIII.PPPP........EEEEEEEEEEE.......WWWWW...WWWWW...EEEEEEEEEEE.BBBBBBBBBB...HHHH...HHHH.....OOOOOO........OOOOOO.....KKKK...KKKKK..
# .........................................................................................................................................................................


@csrf_exempt 
@require_http_methods(["POST"])
def create_checkout_session(request, plan):
    domain_url = config("STRIPE_DOMAIN_URL")
    user_id = request.session.get('user_id', None)
    if user_id == None:
        return JsonResponse({'error': 'no user id'}, status=400)
    
    price_id = config(f"{plan}")

    if plan == '20_DOLLAR_MONTHLY_PRICE_ID':
        discounts = [{'coupon': 'NqeYbQag'}]
    else:
        discounts = []

    stripe_cancel_url = domain_url + 'login/'
    stripe_success_url = domain_url + 'login/'

    try:
        checkout_session  = stripe.checkout.Session.create(
            success_url=stripe_success_url,
            cancel_url=stripe_cancel_url,
            payment_method_types=['card'],
            mode='subscription',
            client_reference_id=user_id,
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            discounts=discounts,
        )
        
        return JsonResponse({
            'sessionId': checkout_session.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
@csrf_exempt
def success(request):
    messages.success(request, 'Thank you for subscribing to Feadl.io! You have been redirected to the dashboard.')
    return redirect('service:social_media')

@csrf_exempt
def cancel(request):
    messages.error(request, 'We were unable to complete your subscription. Please try again.')
    return redirect('service:social_media')

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = config("STRIPE_SECRET_KEY")
    endpoint_secret = config("STRIPE_ENDPOINT")
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
        id_token = user_login(config("MASTER_EMAIL"), config("MASTER_PASSWORD"))
        decoded_token = auth.verify_id_token(id_token)
        master_id = decoded_token['uid']

        if event['type'] == 'checkout.session.completed':
            customer_id = event['data']['object']['customer']
            subscription_id = event['data']['object']['subscription']
            amount_subtotal = event['data']['object']['amount_subtotal']
            isUnlimited = False
            isAds = False
            try:
                def get_plan_name_by_id(amount_subtotal):
                    plan_mappings = {
                        '300': '3 Dollar Plan',
                        '500': '5 Dollar Plan',
                        '1000': '10 Dollar Plan',
                        '2000': '20 Dollar Plan',
                        '2500': '25 Dollar Plan',
                        '6000': '60 Dollar Plan',
                        '12000': '120 Dollar Plan',
                        '30000': '300 Dollar Plan',
                        '50000': '500 Dollar Plan',
                        '150000': '1500 Dollar Plan',
                        '3500': '5 Dollar Annual Plan',
                        '18000': '20 Dollar Annual Plan',
                    }
                    return plan_mappings.get(amount_subtotal, 'Unknown Plan')
            
                plan = get_plan_name_by_id(amount_subtotal)
                isUnlimited = plan in ["60 Dollar Plan"]
                isAds = plan in ['120 Dollar Plan', '300 Dollar Plan', '500 Dollar Plan', '1500 Dollar Plan']
            except Exception as e:
                plan = 'Unknown Plan'
                pass

            if subscription_id:
                user_settings_ref = db.collection('users').document(uid)
                if user_settings_ref.get().exists:
                    user_settings_doc = user_settings_ref.get()
                    user_settings = user_settings_doc.to_dict()
                    firestore_data = {'customer_id': customer_id, 'service_ftue': '0','subscription_id': subscription_id, 'isSubscriber': True, 'isAutomated': True, 'subscription_status': 'Subscribed', 'subscription_plan': plan, 'isUnlimited': isUnlimited, 'isAds': isAds}
                    user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'status': 'Checkout Complete'})
        
        if event['type'] == 'customer.subscription.updated':
            customer_id = event['data']['object']['customer']
            plan_id = event['data']['object']['items']['data'][0]['plan']['id']
            subscription_status = event['data']['object']['status']
            canceled_at = event['data']['object'].get('canceled_at', None)

            def get_plan_name_by_id(plan_id):
                plan_mappings = {
                    config("3_DOLLAR_MONTHLY_PRICE_ID"): '3 Dollar Plan',
                    config("5_DOLLAR_MONTHLY_PRICE_ID"): '5 Dollar Plan',
                    config("10_DOLLAR_MONTHLY_PRICE_ID"): '10 Dollar Plan',
                    config("20_DOLLAR_MONTHLY_PRICE_ID"): '20 Dollar Plan',
                    config("25_DOLLAR_MONTHLY_PRICE_ID"): '25 Dollar Plan',
                    config("60_DOLLAR_MONTHLY_PRICE_ID"): '60 Dollar Plan',
                    config("120_DOLLAR_MONTHLY_PRICE_ID"): '120 Dollar Plan',
                    config("300_DOLLAR_MONTHLY_PRICE_ID"): '300 Dollar Plan',
                    config("500_DOLLAR_MONTHLY_PRICE_ID"): '500 Dollar Plan',
                    config("1500_DOLLAR_MONTHLY_PRICE_ID"): '1500 Dollar Plan',
                    config("5_DOLLAR_ANNUAL_PRICE_ID"): '5 Dollar Annual Plan',
                    config("20_DOLLAR_ANNUAL_PRICE_ID"): '20 Dollar Annual Plan',
                }
                return plan_mappings.get(plan_id, 'Unknown Plan')
            
            plan_name = get_plan_name_by_id(plan_id)

            docs = db.collection('users').where("customer_id", "==", customer_id).stream()

            for doc in docs:
                user_id = doc.id
                user_settings_ref = db.collection('users').document(user_id)
                user_settings = doc.to_dict()
                update_data = {}

                if subscription_status == "canceled" or canceled_at is not None:
                    update_data = {
                        'isSubscriber': False,
                        'subscription_status': 'Canceled',
                        'subscription_plan': 'Canceled',
                        'isUnlimited': False,
                        'isAds': False
                    }
                elif plan_name != user_settings.get('subscription_plan', None):
                    isUnlimited = plan_name in ["60 Dollar Plan"]
                    isAds = plan_name in ['120 Dollar Plan', '300 Dollar Plan', '500 Dollar Plan', '1500 Dollar Plan']
                    update_data = {
                        'subscription_plan': plan_name,
                        'isUnlimited': isUnlimited,
                        'isAds': isAds,
                        
                    }
                if update_data:
                    user_settings_ref.set(update_data, merge=True)
                    action = "Handled cancellation" if subscription_status == "canceled" or canceled_at is not None else "Plan Changed"
                    print(f"{action} for user {user_id}.")

            return JsonResponse({'status': 'Plan Changed'})
        
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
                firestore_data = {
                    'isSubscriber': False,
                    'subscription_status': 'Canceled',
                    'subscription_plan': 'Canceled',
                    'isUnlimited': False,
                    'isAds': False
                }
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
                firestore_data = {
                    'isSubscriber': False,
                    'subscription_status': 'Canceled',
                    'subscription_plan': 'Canceled',
                    'isUnlimited': False,
                    'isAds': False
                }
                user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'status': 'Subscription Canceled'})
        return JsonResponse({'status': 'nothing'})
        
    except Exception as e:
        return JsonResponse({'error': e})
    # ---------------------------------------------------------------------- #

