from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from google.cloud import storage
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

def feadlio_admin(request):
    user_id = request.session.get('user_id')
    if user_id != config('MASTER_ID'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('login')
        
    db = firestore.Client(project='feed-ai-c379d')
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