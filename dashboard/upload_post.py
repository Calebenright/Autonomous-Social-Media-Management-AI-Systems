import requests

# # FOR DEVELOPMENT
# from decouple import config
# API_KEY = config('AYRSHARE_API_KEY')

from project1.secrets_manager import get_secret_value
API_KEY = get_secret_value('AYRSHARE_API_KEY')

def send_post(caption, image_url):
    payload = {
        'post': caption,
        'platforms': ['facebook', 'instagram'],
        'mediaUrls': [image_url]
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {API_KEY}'
    }

    r = requests.post('https://app.ayrshare.com/api/post', json=payload, headers=headers)

    print(r.json())