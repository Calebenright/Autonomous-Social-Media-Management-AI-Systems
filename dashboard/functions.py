import uuid
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops, ImageOps
from io import BytesIO
import openai
import requests
import re
import json
from django.conf import settings
import ast
from google.cloud import storage
from google.oauth2 import service_account

# FOR DEVELOPMENT
from decouple import config
pixabay_api_key = config('PIXABAY_API_KEY')
openai.api_key = config('OPENAI_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

def create_text_post(platform, business_description, business_name):
    prompts = [
    f"Create a social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}] and is specific to the social media platform [PLATFORM = {platform}].",
    f"Create a business-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}] and is specific to the social media platform [PLATFORM = {platform}].",
    f"Create a proffesional-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}] and is specific to the social media platform [PLATFORM = {platform}].",
    f"Create a goofy-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}] and is specific to the social media platform [PLATFORM = {platform}].",
    f"Create a fun-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}] and is specific to the social media platform [PLATFORM = {platform}].",]
    prompt = random.choice(prompts)
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    original_string = original_string.replace('"', '').replace("'", "")
    return original_string

def add_stock_tags(tags, stock_images, bucket_name, bucket_credentials, user_folder_path):
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    tags_list = ast.literal_eval(tags)

    if stock_images == None:
        image_urls = []
    else:
       image_urls = stock_images

    for key in tags_list[:2]:
        base_url = 'https://api.unsplash.com/'
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_API_KEY}',
        }
        params = {
            'query': key,
            'count': 2,
        }
        response = requests.get(f'{base_url}photos/random', headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for photo in data:
            image_url = photo['urls']['regular']
            image_response = requests.get(image_url)
            image_data = image_response.content
            img = Image.open(BytesIO(image_data))
            width, height = img.size
            size = min(width, height)
            left = (width - size) / 2
            top = (height - size) / 2
            right = (width + size) / 2
            bottom = (height + size) / 2
            cropped_img = img.crop((left, top, right, bottom))
            resized_img = cropped_img.resize((1024, 1024))
            image_io = BytesIO()
            resized_img.save(image_io, format='JPEG')
            image_io.seek(0)
            
            filename = str(uuid.uuid4()) + ".jpg"
            blob = bucket.blob(user_folder_path + filename)
            blob.upload_from_file(image_io, content_type='image/jpeg')
            blob.make_public()
            image_urls.append(blob.public_url)

    return image_urls

def create_tags(business_description):
    prompt = f"Produce an array of 7-10 tags that start general and get more specific and relate to the business description: {business_description}."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": 'You are a helpful assistant. Generate arrays of related items in the format ["item1", "item2", "item3"].'},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=1
    )
    original_string = response['choices'][0]['message']['content'].strip()
    if "'" in original_string:
        tags_list = [tag.strip().strip("'") for tag in original_string.strip("[]").split(",")]
    else:
        tags_list = [tag.strip().strip('"') for tag in original_string.strip("[]").split(",")]
    tags_json = json.dumps(tags_list)
    tags= str(tags_json)
    return tags

def generate_unique_filename(extension):
    unique_filename = str(uuid.uuid4()) + extension
    return unique_filename

def generate_random_date(last_date, existing_dates):
    days_to_add = random.randint(2, 6)
    new_datetime = last_date + timedelta(days=days_to_add)
    new_date = new_datetime.strftime('%Y-%m-%d')

    return new_date

def tint_image(img, color):
    src = Image.open(img)  
    src.load()
    r, g, b, alpha = src.split()
    gray = ImageOps.grayscale(src)
    result = ImageOps.colorize(gray, '#000000', color)
    result.putalpha(alpha)

    return result

def getPixabayImg(query):
    num_results = 50
    random_page = random.randint(1, 10)
    endpoint = f"https://pixabay.com/api/?key={pixabay_api_key}&q={query}&per_page={num_results}&page={random_page}&image_type=photo"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            image_urls = [image_info.get("largeImageURL") for image_info in data.get("hits", [])]
            random_image_url = random.choice(image_urls)

            return random_image_url

    except Exception as e:
        pass

def generate_secondary_colors(color):
    prompt = f"Generate 4 hex colors, I want 1 darker, 1 lighter, 1 analogous, and 1 complementary to the primary color: [PRIMARY COLOR = {color}]. Make sure none are too close to the primary color. Exclude the primary color."
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    matches = re.findall(r'(?i)#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})', original_string)
    colors = ['#' + match for match in matches]
    colors_str = json.dumps(colors)

    return colors_str

def upload_and_crop_image(post_image_files, user_image_folder_path):
    
    image_data = post_image_files.read()
    img = Image.open(BytesIO(image_data))
    if img.format != 'JPEG':
        img = img.convert('RGB')
    width, height = img.size
    size = min(width, height)
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2
    cropped_img = img.crop((left, top, right, bottom))
    cropped_img = cropped_img.resize((1024, 1024))
    image_io = BytesIO()
    cropped_img.save(image_io, format='JPEG')
    image_io.seek(0)
    credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(settings.GS_BUCKET_NAME)
    filename = str(uuid.uuid4()) + ".jpg"
    blob = bucket.blob(user_image_folder_path + filename)
    blob.upload_from_file(image_io, content_type='image/jpeg')
    blob.make_public()
    uploaded_image_url = blob.public_url
    
    return uploaded_image_url