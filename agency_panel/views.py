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
from app1.login import user_login, create_or_login_user
from firebase_admin import firestore, auth, credentials
import uuid

db = firestore.Client(project='feed-ai-c379d')

def agency_panel(request):
    user_id = request.session.get('user_id')
    
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    user_data = user_doc.to_dict()
    
    if user_data.get('isAgency'):
        agency_id = user_data.get('agency_id')
        if agency_id:
            users_query = db.collection('users').where('agency_id', '==', agency_id).stream()
            firestore_data = [{'document_id': user.id, **user.to_dict()} for user in users_query]

            # Pagination
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

def agency_switch(request, document_id):
    print(document_id)
    if document_id:
        request.session['user_id'] = document_id
        return redirect('dashboard')
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