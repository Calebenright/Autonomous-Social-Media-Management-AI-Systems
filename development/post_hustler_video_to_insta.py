import requests
from google.cloud import storage, tasks_v2
from google.oauth2 import service_account
import time
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import json
from datetime import datetime, timedelta
from google.protobuf.timestamp_pb2 import Timestamp

def hustler_video(input_video_path, text, font='Staging Functions/videos/SYLFAEN.TTF', font_size=70, font_color='white'):
    video = VideoFileClip(input_video_path)
    text_clip = TextClip(text, fontsize=font_size, color=font_color, font=font)
    text_clip = text_clip.set_position(("center", video.h - 400)).set_duration(video.duration)
    result = CompositeVideoClip([video, text_clip])
    output_filepath = 'Staging Functions/videos/output/video1.mp4'
    result.write_videofile(output_filepath, codec="libx264", audio_codec="aac")
    return output_filepath

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    creds = service_account.Credentials.from_service_account_file('credentials.json')
    client = storage.Client(project=creds.project_id, credentials=creds)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    blob.make_public()
    return blob.public_url

def upload_video_to_instagram_reels(access_token, user_id, video_url, caption):

    video_upload_url = f"https://graph.facebook.com/v17.0/{user_id}/media"
    
    video_data = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'access_token': access_token
    }
    
    response = requests.post(video_upload_url, data=video_data)
    response_data = response.json()

    if 'id' not in response_data:
        print("Error uploading video:", response_data)
        return

    container_id = response_data['id']

     # Step 2: Check the status of the media
    media_status_url = f"https://graph.facebook.com/v17.0/{container_id}"
    status_params = {
        'fields': 'status_code',
        'access_token': access_token
    }

    media_ready = False
    while not media_ready:
        status_response = requests.get(media_status_url, params=status_params)
        status_response_data = status_response.json()
        print(status_response_data)
        if status_response_data.get('status_code') == 'FINISHED':
            media_ready = True
        else:
            print("Media is not ready yet. Waiting...")
            time.sleep(25)

    # Step 2: Publish the video to Instagram
    publish_url = f"https://graph.facebook.com/v17.0/{user_id}/media_publish"
    publish_data = {
        'creation_id': container_id,
        'access_token': access_token,
        'feed_target': 'REELS'
    }
    
    publish_response = requests.post(publish_url, data=publish_data)
    publish_response_data = publish_response.json()

    if 'id' in publish_response_data:
        print("Video successfully uploaded to Instagram Reels!")
    else:
        print("Error publishing video:", publish_response_data)

def schedule_post(video_url, caption, uid, date_and_time):
    queue_name = 'reels'
    queue_url = 'https://us-central1-starter-web-app-389316.cloudfunctions.net/post-reel-development'
    credentials = service_account.Credentials.from_service_account_file('credentials.json')
    client = tasks_v2.CloudTasksClient(credentials=credentials)
    parent = client.queue_path('starter-web-app-389316', 'us-central1', queue_name)
    API_TOKEN = '53461460913485354656279465'

    dt = datetime.fromisoformat(date_and_time)  # Assuming ISO 8601 format
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)

    task_payload = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": queue_url,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_TOKEN}"
            },
            "oidc_token": {
                "service_account_email": "main-service@starter-web-app-389316.iam.gserviceaccount.com"
            },
            "body": json.dumps({
                "video_url": video_url,
                "caption": caption,
                "uid": uid
            }).encode(),
        },
        "schedule_time": timestamp
    }

    task = client.create_task(parent=parent, task=task_payload)
    print(f"Task created: {task.name}")

def schedule_posts(day, users, video_path, caption, bucket_name, folder, video_type, total_video, current_date):
    for n in range(total_video):
        text = f"Day {day}        {users}/200000"
        filepath = hustler_video(video_path, text)
        destination_blob_name = f'{video_type}_{n}.mp4'
        video_url = upload_to_gcs(bucket_name, filepath, folder + destination_blob_name)
        upload_date = current_date.strftime('%Y-%m-%d')
        upload_time = 'T15:00:00'
        schedule_datetime = upload_date + upload_time
        schedule_post(video_url, caption, 'BlFcVyzerSSX5dr4hxccYlgtLH03', schedule_datetime)
        current_date += timedelta(days=1)
        day += 1
        print('Another One: ', day, current_date)

    return print('Posts have been made and scheduled')

video_path = 'Staging Functions/videos/base.mp4'
caption = 'Link in my bio'
caption2 = '🚨'

users = 2
day = 7

bucket_name = 'starter_web_app_bucket'
folder = 'development/'
total_video = 10
video_type = 'daily_hustler'

current_date = datetime.now() + timedelta(days=1)

# T15:00:00 is 10AM

schedule_posts(day, users, video_path, caption, bucket_name, folder, video_type, total_video, current_date)

# access_token = 'EAADFIOXHRl4BOwIWAYNn4szfDAB1rau4JiHROGuuLyQydnZAbbL0hHDhbtdp4LtKwEbFcRhuqZAQunoSwValn9UlYk4SFHdYtsMYLoFEAfpWCUvzZBBk2QtqtHPbN5nAkJAZAgXZBQIM2ARylVa4rTWiIGDQLBRWPueDhOX9KZBLIaznuz9954Q0mAUZCf8PbLnMqXRgUJf'
# user_id = '17841431479346652'
# filepath = add_text_to_video(video_path, text)
# destination_blob_name = f'{video_type}_{video_num}.mp4'
# video_url = upload_to_gcs(bucket_name, filepath, folder + destination_blob_name)
# upload_video_to_instagram_reels(access_token, user_id, video_url, caption)
