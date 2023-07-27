from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UserSettingsForm
from .models import UserSettings
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
import os
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .post_creator import create_post
from .upload_post import send_post
from .generate_comment import generate_comment
from django.http import JsonResponse
import time
from .generate_unique_filename import generate_unique_filename


@login_required
def dashboard(request):
    try:
        user_settings = UserSettings.objects.get(user=request.user)
    except:
        user_settings = UserSettings.objects.create(user=request.user)

    context = {
        'user_settings': user_settings
    }
    return render(request, 'dashboard.html', context)

def apps_calendar(request):
    return render(request, 'apps_calendar.html')

def comments(request):
    if request.method == 'POST':
        recent_comment = 'The parallax is a little odd but O.o that house build is awesome!!'
        comment = generate_comment(recent_comment)
        return render(request, 'comments.html', {'comment': comment}) 
    return render(request, 'comments.html')


def post_creator(request):
    if request.method == 'POST':
        # # Call the script's code to generate the image
        user_settings = UserSettings.objects.get(user=request.user)
        user_folder_path = f'user_folders/{request.user.id}/images/'
        post, url = create_post(user_settings.business_description, settings.GS_BUCKET_NAME, settings.GS_CREDENTIALS, user_folder_path)
        user_settings.last_image_url = user_settings.next_image_url
        user_settings.last_caption = user_settings.next_caption
        user_settings.next_image_url = url
        user_settings.next_caption = post
        user_settings.save()
        return render(request, 'post_creator.html', {'post': post, 'image_url': url})

    return render(request, 'post_creator.html')

def upload_post(request):
    if request.method == 'POST':
        user_settings = UserSettings.objects.get(user=request.user)
        image_url = user_settings.next_image_url
        caption = user_settings.next_caption

        # Call the function to post image to Instagram
        send_post(caption, image_url)
        return render(request, 'dashboard.html')

    return render(request, 'post_creator.html')


def brand_settings(request):
    try:
        user_settings = UserSettings.objects.get(user=request.user)
    except:
        user_settings = UserSettings.objects.create(user=request.user)


    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=user_settings)
        if form.is_valid():
            user_settings = form.save(commit=False)
            user_settings.user = request.user
            # Handle logo upload to GCP
            logo = request.FILES.get('logo')
            if logo:
                credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
                client = storage.Client(project=credentials.project_id, credentials=credentials)
                bucket = client.bucket(settings.GS_BUCKET_NAME)
                
                # Specify the user's folder path within the bucket
                user_folder_path = f'user_folders/{request.user.id}/logo/'  # Customize the folder structure as needed
                blob = bucket.blob(user_folder_path + 'logo.png')
                blob.upload_from_file(logo)
                blob.make_public()
                user_settings.logo = blob.public_url
                # Assign the new user input value

            user_settings.save()
            return redirect('brand_settings')  # Redirect to the brand settings page after saving settings
    else:
        form = UserSettingsForm(instance=user_settings)

    context = {
        'form': form,
        'user_settings': user_settings
    }
    return render(request, 'brand_settings.html', context)
