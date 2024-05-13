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

db = firestore.Client(project='feed-ai-c379d')

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

    user_email = auth.get_user(user_id).email if user_id else ''
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
            library_folder_path = f'user_folders/{user_id}/image_library/'
            image_tags = add_pixabay_tags(tags, None, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), library_folder_path)
            image_tags_string = json.dumps(image_tags).replace("'", '"')

            firestore_data = {
                'tags': tags,
                'business_description': business_description,
                'business_name': business_name,
                'brand_color': brand_color,
                'secondary_colors' : colors,
                'ftue': True,
                'isSubscriber': False,
                'isUnlimited': False,
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
                'image_tags': image_tags_string
            }

            db_ref.set(firestore_data, merge=True)
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
                'ElaineTimezone': request.POST.get('ElaineTimezone')
            }

            isElaineOn = request.POST.get('isElaineOn') == "on"
            elaine_data['isElaineOn'] = isElaineOn
            firestore_data = {'isAutomated': isElaineOn}
            db_ref.set(firestore_data, merge=True)

            if isElaineOn and not elaine_settings.get('isElaineOn', False):
                if not user_settings.get('isAgencyUser', True):
                    send_new_subscriber_email(elaine_data['ElaineEmail'], user_settings.get('business_description'), user_settings.get('business_name'), 'Elaine')

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
        'jerry_settings': jerry_settings
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

def download(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
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

    image_folder_path = f'user_folders/{user_id}/image_posts/'
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
            from_email = config("EMAIL_HOST_USER")
            recipient_list = [config("INTERNAL_RECIPIENTS")]
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
            ad_image_url = create_call_to_action(isLogo, logo_path, biz, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path, num_ad)
            if num_ad <= 5:
                num_ad += 1
        else:
            isLogo = request.POST.get('isLogo', False)
            request.session['isLogo'] = isLogo
            ad_image_url = create_call_to_action(isLogo, logo_path, biz, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path, num_ad)
            ad_copy = create_ad_copy(biz, user_settings['business_name'])
            if num_ad <= 5:
                num_ad += 1

        firestore_data = {
            'ad_image_url': ad_image_url,
            'ad_copy': ad_copy,
            'ad_headline': ad_headline,
            'num_ad': num_ad
        }

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
                    return redirect('post_creator')

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
                return redirect('post_creator')
            # -------------- POST --------------- #
            elif form_name == 'formPostLibrary':
                library_folder_path = f'user_folders/{user_id}/image_library/'
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
                    return redirect('post_creator')
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
                    return redirect('post_creator')

                linkedin_checked = False

                num_sent = user_settings.get('num_sent', 0)
                max_sent = global_variables.get('max_sent', 5)

                current_time = timezone.now()
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

                return redirect('post_creator')
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
                        return redirect('post_creator')
                    
                    if selected_option == 'up':
                        progress = 100
                        image = request.FILES.get('file')
                        file_extension = image.name.split('.')[-1].lower()
                        isLogo = request.POST.get('isLogo', False)

                        if file_extension not in ['jpg', 'jpeg', 'png']:
                            messages.error(request, 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png')
                            return redirect('post_creator')

                        try: 
                            if file_extension in ['mp4', 'avi', 'mov']:
                                messages.error(request, 'ONLY ACCEPTED FILE FORMATS: .jpg, .jpeg, .png')
                                return redirect('post_creator')
                                # url = upload_video_to_google(image, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), video_folder_path, file_extension)
                                # selected_option = 'video'
                            else:
                                img = create_upload(image, logo_path, isLogo)
                                url = upload_jpg_to_google(img, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), image_folder_path)
                        except:
                            messages.error(request, 'No image was uploaded or there was an error. Please try again.')
                            return redirect('post_creator')
                        
                    elif selected_option == 'text':
                        progress = 100
                        select = request.POST.get('text-platform')
                        add_credits += 0.5

                        try:
                            post = create_text_post(select, biz, biz_name)
                            url = None
                        except:
                            messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                            return redirect('post_creator')

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
                                    return redirect('post_creator')
                            else:
                                messages.error(request, 'Please upgrade to utilize our AI Stock Image Library.')
                                return redirect('post_creator')
                            
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
                                return redirect('post_creator')
                        else:
                            add_credits += 0.8
                            try:
                                progress = 95
                                url = img_url
                            except:
                                messages.error(request, 'Image failed to generate. If the problem persists, please contact us at https://feadl.io/contact/')
                                return redirect('post_creator')

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
                                    return redirect('post_creator')
                        else:
                            messages.error(request, 'Please upgrade to utilize this feature.')
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
                    messages.error(request, 'You have reached the maximum number of monthly images for your subscription. Please upgrade to continue or wait until the beginning of the next month.')
                    return redirect('post_creator')

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
            return redirect('post_creator')
        else:
            messages.error(request, 'We are here to help your business. Our generators are in high demand and accrue a cost. Please upgrade to utilize our amazing app!')
            return redirect('post_creator')
        
    context = {'user_id': user_id, 'user_settings': user_settings, 'selected_option': selected_option, 'isLogo': isLogo, 'tags': json.dumps(user_settings.get('image_tags'))}
    return render(request, 'post_creator.html', context)

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
    
    if request.session.get('tags') != ['']:
        tags = request.session.get('tags')
    else:
        try:
            tags = ast.literal_eval(user_settings['tags'])
        except (TypeError, KeyError):
            tags = ''

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
                random_int = random.randint(global_variables['random_int_min'], global_variables['random_int_max'])
                color = user_settings['brand_color']
                secondary_colors = ast.literal_eval(user_settings['secondary_colors'])
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

    context = {
        'user_settings': user_settings,
        'user_id': user_id
    }
    return render(request, 'calendar.html', context)

def library(request):
    try:
        user_id = request.session.get('user_id')
        logging.info(f"Fetching settings for user {user_id}")
        
        user_settings_ref = db.collection('users').document(user_id)
        user_settings_doc = user_settings_ref.get()
        user_settings = user_settings_doc.to_dict()
        
        global_variables_ref = db.collection('variables').document('global_variables')
        global_variables_doc = global_variables_ref.get()
        global_variables = global_variables_doc.to_dict()

    except Exception as e:
        logging.exception("An unexpected error occurred")
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        try:
            form_name = request.POST.get('form')
            logging.info(f"Processing POST request for form {form_name}")
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

                is_generate_stock_images_clicked = request.POST.get('isGenerateStockImagesClicked', 'false') == 'true'
                if is_generate_stock_images_clicked:
                    image_tags = add_stock_tags(user_settings['tags'], image_tags, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), library_folder_path)

                is_generate_pixabay_images_clicked = request.POST.get('isGeneratePixabayImagesClicked', 'false') == 'true'
                if is_generate_pixabay_images_clicked:
                    num_pixabay = user_settings.get('num_pixabay', 0)
                    if user_settings.get('num_pixabay', 0) < global_variables.get('pixabay_daily_limit', 2) or user_settings.get('isAdmin', False):
                        image_tags = add_pixabay_tags(user_settings['tags'], image_tags, config("GS_BUCKET_NAME"),  config("GS_CREDENTIALS"), library_folder_path)
                        num_pixabay += 1
                        firestore_data = {'num_pixabay': num_pixabay}
                        user_settings_ref.set(firestore_data, merge=True)
                    else:
                        messages.error(request, f"You have reached your daily limit for getting stock images. Try again tomorrow.")

                    
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


def all_auth(request):
    if request.method == 'POST':
        form_name = request.POST.get('form')
        state = secrets.token_urlsafe(16)
        redirect_uri =  config("REDIRECT_URI")
        if form_name == 'formLinkedinPersonal':
            request.session['account_type'] = 'personal'
            request.session['provider'] = 'linkedin'
            AUTHORIZATION_URL = 'https://www.linkedin.com/oauth/v2/authorization'
            CLIENT_ID = config("LINKEDIN_CLIENT_ID_BUSINESS")
            REDIRECT_URI =  config("REDIRECT_URI")
            STATE = state
            PERSONAL_SCOPES = [
                'r_basicprofile',
                'w_member_social',
                'w_member_social_feed'
            ]
            auth_url = f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={"+".join(PERSONAL_SCOPES)}&state={STATE}'
            print(auth_url)
        elif form_name == 'formLinkedinBusiness':
            request.session['account_type'] = 'business'
            request.session['provider'] = 'linkedin'
            AUTHORIZATION_URL = 'https://www.linkedin.com/oauth/v2/authorization'
            CLIENT_ID = config("LINKEDIN_CLIENT_ID_BUSINESS")
            REDIRECT_URI =  config("REDIRECT_URI")
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
            print(auth_url)
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
                'redirect_uri':  config("REDIRECT_URI"),
                'client_id': config("LINKEDIN_CLIENT_ID_BUSINESS"),
                'client_secret': config("LINKEDIN_CLIENT_SECRET_BUSINESS"),
            }
            response = requests.post(access_token_url, data=params)
            data = response.json()
            access_token = data.get('access_token')

            account_type = request.session.get('account_type', 'personal')

            def get_user_managed_organizations(access_token):
                """Fetches organizations that the authenticated user can manage."""
                url = "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(*,roleAssignee~(localizedFirstName, localizedLastName), organization~(localizedName)))"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                }
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    print("Failed to fetch organizations:", response.json())
                    return None
            
            profile_response = requests.get(
                    'https://api.linkedin.com/v2/me',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
            
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
                print(organizations_data)
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
                'redirect_uri':  config("REDIRECT_URI"),
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
                    'redirect_uri':  config("REDIRECT_URI"),
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
                        return redirect('brand_settings')
                except Exception as e:
                    messages.error(request, 'Please make sure the instagram account is linked to the selected facebook account.')
                    return redirect('brand_settings')
            except Exception as e:
                messages.error(request, e)
                return redirect('brand_settings')
        elif provider == 'google_business':
            isCheck = 'Google'
            code = request.GET.get('code')
            access_token_url = 'https://oauth2.googleapis.com/token'
            params = {
                'client_id':  config("GOOGLE_APP_ID"),
                'client_secret': config("GOOGLE_APP_SECRET"),
                'redirect_uri':  config("REDIRECT_URI"),
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
    except Exception as e:
        messages.error(request, "There was an error connecting your profile.")
        return redirect('brand_settings')
    
def process_page_selection(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
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
    selected_page_id = request.POST.get('pageId', None)
    provider = request.POST.get('provider', None)
    page_name = request.POST.get('pageName', None)
    page_token = request.POST.get('pageToken', None)
    page_type = request.POST.get('pageType', None)

    if not selected_page_id:
        messages.error(request, 'Please make sure the Instagram account is linked to the selected Facebook account.')
        return redirect('brand_settings')
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
            return redirect('brand_settings')
        elif provider == 'linkedin':
            print(selected_page_id)
            firestore_data = {
                f'{provider}_id': selected_page_id,
                f'{provider}_name': page_name,
                'isLinkedin': True
            }       
            user_settings_ref.set(firestore_data, merge=True)
            messages.success(request, f"You've successfully connected your {provider} account!")
            return redirect('brand_settings')
        else: 
            messages.error(request, 'There was an error connecting your account. Please try again.')
            return redirect('brand_settings')

    
def unlink(request):
    # ----- Get the Firestore document reference for the user settings ----- #
    try:
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
            'linkedin_token': None,
            'linkedin_id': None,
            'linkedin_name': None,
            'linkedin_personal_id': None,
            'linkedin_personal_name': None,
            'isLinkedin': False,
        }    
        user_settings_ref.set(firestore_data, merge=True)
    return redirect('brand_settings')
    
def logout_view(request):
    request.session.flush()
    return redirect('index')


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
            return JsonResponse({'error': 'Please select a social media.'}, status=400)
        
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
    
    db = firestore.Client(project='feed-ai-c379d')
    
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
def create_checkout_session(request, plan, billing_cycle):
    domain_url = config("STRIPE_DOMAIN_URL")
    user_id = request.session.get('user_id', None)
    if user_id == None:
        return redirect('login')
    price_id = settings.PRODUCT_IDS.get(f"{plan}_{billing_cycle}")
    prices_with_trial = [config("PREMIUM_MONTHLY_PRICE_ID"), config("PREMIUM_ANNUAL_PRICE_ID")]
    if price_id in prices_with_trial:
        trial_period_days = 7
    else:
        trial_period_days = None
    
    try:
        checkout_session  = stripe.checkout.Session.create(
            success_url=domain_url + 'success/',
            cancel_url=domain_url + 'cancel/',
            payment_method_types=['card'],
            mode='subscription',
            client_reference_id=user_id,
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            subscription_data={'trial_period_days': 7} if trial_period_days is not None else {},
        )
        
        return JsonResponse({
            'sessionId': checkout_session.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
@csrf_exempt 
def checkout(request):
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
            user_settings = {}
        # ---------------------------------------------------------------------- #
        pass
    except:
        messages.error(request, 'Please try logging in again.')
        return redirect('login')
        
    if user_settings is None:
        user_settings_strings = {}
    else:
        user_settings_strings = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in user_settings.items()
        }
        
    context = {
        'ENVIRONMENT': config("ENVIRONMENT"),
        'user_settings': user_settings,
        'user_settings_json': json.dumps(user_settings_strings),
        'user_id': user_id,
        'isStripeDev': global_variables['isStripeDev']
    }
    return render(request, 'checkout.html', context)

@csrf_exempt
def success(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for subscribing to Feadl.io! You have been redirected to the dashboard.')
        return redirect('dashboard')
    return render(request, 'success.html')

@csrf_exempt
def cancel(request):
    messages.error(request, 'We were unable to complete your subscription. Please try again.')
    return redirect('dashboard')

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
            isUnlimited = False
            try:
                line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)
                for item in line_items.data:
                    plan = item.description
                    if plan == "Unlimited Plan":
                        isUnlimited = True
            except Exception as e:
                print(f"Error fetching line items: {e}")
                return JsonResponse({'errro': f'{e}'})

            if subscription_id:
                user_settings_ref = db.collection('users').document(uid)
                user_settings_doc = user_settings_ref.get()
                user_settings = user_settings_doc.to_dict()
                # send_new_subscriber_email(user_settings.get('email'), user_settings.get('business_description'), user_settings.get('business_name'), 'Elaine')
                firestore_data = {'customer_id': customer_id, 'subscription_id': subscription_id, 'isSubscriber': True, 'subscription_status': 'Subscribed', 'subscription_plan': plan, 'isUnlimited': isUnlimited}
                user_settings_ref.set(firestore_data, merge=True)
                if user_settings.get('isBusiness', False):
                    new_doc_ref = db.collection('accounts').document(uid)
                    new_doc_ref.set({'name': user_settings['business_name']})
            return JsonResponse({'status': 'Checkout Complete'})
        
        if event['type'] == 'customer.subscription.updated':
            customer_id = event['data']['object']['customer']
            plan_id = event['data']['object']['items']['data'][0]['plan']['id']
            subscription_status = event['data']['object']['status']
            canceled_at = event['data']['object'].get('canceled_at', None)

            def get_plan_name_by_id(plan_id):
                plan_mappings = {
                    config("STANDARD_MONTHLY_PRICE_ID"): 'Standard Plan',
                    config("PREMIUM_MONTHLY_PRICE_ID"): 'Full Plan',
                    config("AGENCY_MONTHLY_PRICE_ID"): 'Unlimited Plan',
                    config("STANDARD_ANNUAL_PRICE_ID"): 'Standard Annual Plan',
                    config("PREMIUM_ANNUAL_PRICE_ID"): 'Full Annual Plan',
                    config("AGENCY_ANNUAL_PRICE_ID"): 'Unlimited Annual Plan',
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
                        'isUnlimited': False
                    }
                elif plan_name != user_settings.get('subscription_plan', None):
                    isUnlimited = plan_name in ["Unlimited Plan", "Unlimited Annual Plan"]
                    update_data = {
                        'subscription_plan': plan_name,
                        'isUnlimited': isUnlimited
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
                    'isUnlimited': False
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
                    'isUnlimited': False
                }
                user_settings_ref.set(firestore_data, merge=True)
            return JsonResponse({'status': 'Subscription Canceled'})
        return JsonResponse({'status': 'nothing'})
        
    except Exception as e:
        return JsonResponse({'error': e})
    # ---------------------------------------------------------------------- #

