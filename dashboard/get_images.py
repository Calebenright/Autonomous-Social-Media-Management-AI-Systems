from decouple import config
import firebase_admin
from firebase_admin import firestore, auth, credentials
import uuid
import random
from datetime import datetime
from PIL import Image
from io import BytesIO
import requests
import ast
from google.cloud import storage
from google.oauth2 import service_account
from openai import OpenAI
from datetime import date, datetime, timedelta, timezone

UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
bucket_credentials = config('GS_CREDENTIALS')
bucket_name = config('GS_BUCKET_NAME')

creds = service_account.Credentials.from_service_account_file(bucket_credentials)
client = storage.Client(project=creds.project_id, credentials=creds)
bucket = client.bucket(bucket_name)
db = firestore.Client(project='feed-ai-c379d')

def create_caption(business_description, business_name):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompts = [
    f"I need copy for social media that is a meme, pop culture, joke, or humor that relates to the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"I need some educational copy with a social media cta for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Create copy thats relevant on this date {datetime.now().date()}, and is themed and is for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"I need an engaging question, poll, quiz, fact, statistic, etc. to post on social media for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a detailed social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a business-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a professional-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a fun-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a detailed social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}]. The copy should not include the business name or description.",
    f"Generate copy for a business-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}]. The copy should not include the business name or description.",
    f"Generate copy for a professional-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}]. The copy should not include the business name or description.",
    f"Generate copy for a fun-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}]. The copy should not include the business name or description.",
    ]
    prompt = random.choice(prompts)
    options = [15, 25, 50, 75, 100]
    weights = [5, 20, 45, 20, 10]
    selected_number = random.choices(options, weights, k=1)[0]
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": f"It should be less than {selected_number} words."
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=300
        )
    original_string = response.choices[0].message.content.strip()
    caption = original_string.strip('"')
    return caption

def create_search_term(business_description):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompt = f'I need a short search key based on this business description: {business_description}. It will be used to get an image from a databse and for the businesses media.'
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": f"you are a search key generator and should only generate a 1-3 word search key. It should be vague enough so that It can pull an image from a database that deosn't have specific search features."
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=300
        )
    original_string = response.choices[0].message.content.strip()
    text = original_string.strip('"')
    return text

def get_stock(user_id, num):
    try:
        # Fetch user settings
        db_ref = db.collection('users').document(user_id)
        user_settings = db_ref.get().to_dict() or {}

        # Define document reference for Elaine
        elaine_doc_ref = db.collection('users').document(user_id).collection('agents').document('elaine')

        business_description = user_settings.get('business_description', 'Social Media')
        key = create_search_term(business_description)

        # Unsplash API request
        base_url = 'https://api.unsplash.com/'
        headers = {'Authorization': f'Client-ID {UNSPLASH_API_KEY}'}
        params = {'page': 1, 'query': key, 'content_filter' : 'high'}
        response = requests.get(f'{base_url}search/photos', headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Get the num-th photo
        if num < len(data['results']):
            photo = data['results'][num]
            image_url = photo['urls']['regular']
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_data = image_response.content
            img = Image.open(BytesIO(image_data))
            image_io = BytesIO()
            img.save(image_io, format='JPEG')
            image_io.seek(0)

            # Upload to Google Cloud Storage
            filename = f"{uuid.uuid4()}.jpg"
            user_folder_path = f'user_folders/{user_id}/image_library/'
            blob = bucket.blob(user_folder_path + filename)
            blob.upload_from_file(image_io, content_type='image/jpeg')
            blob.make_public()
            url = blob.public_url
            # Update user settings with new image URL
            image_library = ast.literal_eval(user_settings.get('image_tags', '[]'))
            image_library.append(url)
            user_settings['image_tags'] = str(image_library)

            # Create and store caption
            caption = create_caption(business_description, user_settings.get('business_name', ''))
            elaine_settings = {f'scheduled_image_{num}': url, f'scheduled_caption_{num}': caption}
            elaine_doc_ref.set(elaine_settings, merge=True)

            return blob.public_url
        else:
            print(f"No photo available at index {num}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
