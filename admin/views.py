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
import google.oauth2.id_token
import google.auth.transport.requests
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

db = firestore.Client(project='feed-ai-c379d')

def database(request):
    user_id = request.session.get('user_id')
    if user_id != config('MASTER_ID'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('login')
        
    query = db.collection('users')

    email = request.GET.get('email')
    uid = request.GET.get('uid')

    if email:
        query = query.where('email', '==', email)
        users = [doc.to_dict() for doc in query.stream()]
    elif uid:
        doc_ref = db.collection('users').document(uid)
        users = [doc_ref.get().to_dict()] if doc_ref.get().exists else []
    else:
        users = [doc.to_dict() for doc in query.stream()]

    for user in users:
        user['checkmark_score'] = sum([
            user.get('ftue', False),
            user.get('isAutomated', False),
            user.get('isSubscriber', False)
        ])
        
    firestore_data = sorted(users, key=lambda x: x['checkmark_score'], reverse=True)

    ftue_count = sum(user.get('ftue', False) for user in firestore_data)
    is_automated_count = sum(user.get('isAutomated', False) for user in firestore_data)
    is_subscriber_count = sum(user.get('isSubscriber', False) for user in firestore_data)

    # Pagination
    paginator = Paginator(firestore_data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if len(users) == 1:
        user_data = users[0]
        return render(request, 'database.html', {
            'user_data': user_data,
            'firestore_data': firestore_data,
        })
    
    return render(request, 'database.html', {
        'firestore_data': firestore_data,
        'ftue_count': ftue_count,
        'is_automated_count': is_automated_count,
        'is_subscriber_count': is_subscriber_count,
        'page_obj': page_obj,
    })

def crm(request):
    user_id = request.session.get('user_id')
    if user_id != config('MASTER_ID'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('login')
    
    query = db.collection('service')
    email = request.GET.get('email')
    priority = request.GET.get('priority')

    if email:
        query = query.where('email', '==', email)

    if priority == 1:
        query = query.where('leadPriority', 'in', [1, None])
        users = [doc.to_dict() for doc in query.stream() if doc.get('leadPriority') is None]
    elif priority:
        query = query.where('leadPriority', '==', int(priority))
        users = [doc.to_dict() for doc in query.stream()]
    else:
        users = [doc.to_dict() for doc in query.stream()]
        users = sorted(users, key=lambda x: x.get('leadPriority', 0), reverse=True)


    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    suggested_subject = request.session.get('suggested_subject')
    suggested_message = request.session.get('suggested_message')

    if len(users) == 1:
        user_data = users[0]
        return render(request, 'crm.html', {
            'user_data': user_data,
            'firestore_data': users,
            'suggested_subject': suggested_subject,
            'suggested_message': suggested_message
        })
    
    return render(request, 'crm.html', {
        'firestore_data': users,
        'page_obj': page_obj,
        'suggested_subject': suggested_subject,
        'suggested_message': suggested_message
    })

def update_priority(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        lead_priority = data.get('leadPriority')
        print(user_id, lead_priority)
        if user_id is not None and lead_priority is not None:
            try:
                user_ref = db.collection('service').document(user_id)
                user_ref.update({'leadPriority': int(lead_priority)})
                return JsonResponse({'success': True})
            except:
                return JsonResponse({'success': False, 'error': 'Failed to update leadPriority field'}, status=500)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request data'}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def delete_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        if user_id is not None:
            try:
                user_ref = db.collection('users').document(user_id)
                user_ref.delete()
                return JsonResponse({'success': True})
            except:
                return JsonResponse({'success': False, 'error': 'Failed to delete user'}, status=500)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request data'}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def send_crm_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        request.session['suggested_subject'] = subject
        request.session['suggested_message'] = message
        
        from_email = config("EMAIL_HOST_USER")
        recipient_list = [email]
        email_message = EmailMessage(subject, message, from_email, recipient_list)
        
        try:
            user = db.collection('service').document(email)
            user.update({'emailSent': True})
            email_message.send()
            messages.success(request, "Your email was sent! We will get back with you shortly.")
            return redirect('feadlio_crm')
        except Exception:
            messages.error(request, "There was an error sending your email. Please wait a moment and try again.")
            return redirect('feadlio_crm')
        
    return render(request, 'crm.html')

def links(request):
    return render(request, 'links.html')