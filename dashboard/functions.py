import uuid
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops, ImageOps, ExifTags
from io import BytesIO
import requests
import re
import json
from django.conf import settings
import ast
from google.cloud import storage
from google.oauth2 import service_account
from urllib.parse import urlparse
from google.cloud.storage import Blob
from openai import OpenAI
import threading
import os
from django.templatetags.static import static 
from django.contrib.staticfiles.storage import staticfiles_storage
from .graphic_designer import generate_image_from_params, hex_to_rgb
import base64
from decouple import config

# FOR DEVELOPMENT
from decouple import config
pixabay_api_key = config('PIXABAY_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

def create_text_post(select, business_description, business_name):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompts = [
    f"I need copy for social media that is a meme, pop culture, joke, or humor that relates to the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"I need some educational copy with a social media cta for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Create copy thats relevant on this date {datetime.now().date()}, and is themed and is for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"I need an engaging question, poll, quiz, fact, statistic, etc. to post on social media for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a detailed social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a business-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a professional-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a goofy-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
    f"Generate copy for a fun-toned social media post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}].",
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

def create_background_image_description (key):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompt = f"Choose one of these tags: [{key}]. Then use the tag to create a creative description that is based on it. Choose one. only have a single subject or element to highlight"
    randTypes = ["Photo", "Photo", "Photo", "Stock Image", "Stock Image", "Stock Image", "3D Render", "Graphic", "Advertisement"]
    randType = random.choice(randTypes)
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": f"Match this syntax: Type: [{randType}] - Style: [STYLE] - Scene: [SCENE] - Subject: [SUBJECT] - Description: [DESCRIPTION] - Elements: [ELEMENTS]"
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=200
        )
    original_string = response.choices[0].message.content.strip()
    return original_string

def create_stock_image_description (key):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompt = f"Choose one of these tags: [{key}]. Then use the tag to create a description for a stock image or a realistic photo that is based on it. the image should have a clear subject or element. It should be simple and should not have anything that could be flagged an innapropraite or a violation."
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": "Match this syntax: Scene: [SCENE] - Description: [DESCRIPTION] - Elements: [ELEMENTS] Aperture: [APERTURE] Lens: [LENS] - Lighting: [LIGHTING]"
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=200
        )
    original_string = response.choices[0].message.content.strip()
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
            image_io = BytesIO()
            img.save(image_io, format='JPEG')
            image_io.seek(0)
            
            filename = str(uuid.uuid4()) + ".jpg"
            blob = bucket.blob(user_folder_path + key + '/' + filename)
            blob.upload_from_file(image_io, content_type='image/jpeg')
            blob.make_public()
            image_urls.append(blob.public_url)

    return image_urls

def create_tags(business_description):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompt = f"Produce an array of 7-10 tags that start general and get more specific and relate to the business description: {business_description}."
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": 'Generate arrays of related items in the format ["item1", "item2", "item3"].'},
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        max_tokens=200
    )
    original_string = response.choices[0].message.content.strip()
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
    days_to_add = random.randint(2, 5)
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
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompt = f"Generate 4 hex colors, I want 1 darker, 1 lighter, 1 analogous, and 1 complementary to the primary color: [PRIMARY COLOR = {color}]. Make sure none are too close to the primary color. Exclude the primary color."
    response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {
                "role": "system",
                "content": "you are not a person. respond with 4 hex colors."
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
    matches = re.findall(r'(?i)#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})', original_string)
    colors = ['#' + match for match in matches]
    if len(colors) > 4:
        colors = colors[:4]
    elif len(colors) < 4:
        colors += ['#000000'] * (4 - len(colors))
    colors_str = json.dumps(colors)

    return colors_str

def read_image(post_image_files):
    image_data = post_image_files.read()
    img = Image.open(BytesIO(image_data))
    return img

def convert_to_bytes(image, format):
    image_io = BytesIO()
    image.save(image_io, format=format)
    image_io.seek(0)

    return image_io

def upload_and_crop_image(post_image_files, user_image_folder_path):
    image_data = post_image_files.read()
    img = Image.open(BytesIO(image_data))
    img = correct_orientation(img)
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

def crop_image(image):
    image_data = image.read()
    img = Image.open(BytesIO(image_data))
    img = correct_orientation(img)
    if img.format != 'JPEG':
        img = img.convert('RGB')
    width, height = img.size
    size = min(width, height)
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2
    cropped_img = img.crop((left, top, right, bottom))
    
    return cropped_img

def correct_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(img._getexif().items())

        if exif[orientation] == 3:
            img = img.rotate(180, expand=True)
        elif exif[orientation] == 6:
            img = img.rotate(270, expand=True)
        elif exif[orientation] == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # cases: image doesn't have getexif
        pass
    return img

def download_and_save_image_as_seek(url):
    image_url = requests.get(url)
    image_data = image_url.content
    img = Image.open(BytesIO(image_data))
    image_io = BytesIO()
    img.save(image_io, format='PNG')
    image_io.seek(0)
    return image_io

def delete_from_google(public_url, bucket_credentials):
    path_parts = public_url.replace("https://storage.googleapis.com/", "").split("/")
    bucket_name = path_parts[0]
    object_name = "/".join(path_parts[1:])
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.delete()

def reupload_gcs_image(source_url, new_folder):
    path_parts = source_url.replace("https://storage.googleapis.com/", "").split("/")
    bucket_name = path_parts[0]
    object_name = "/".join(path_parts[1:])
    destination_blob_name = 'scheduled_image_library/' + str(uuid.uuid4()) + ".png"
    storage_client = storage.Client()
    source_bucket = storage_client.bucket(settings.GS_BUCKET_NAME)
    source_blob = source_bucket.blob(object_name)
    destination_blob = source_bucket.blob(destination_blob_name)
    source_bucket.copy_blob(source_blob, source_bucket, destination_blob_name)
    destination_blob.make_public()
    new_image_url = destination_blob.public_url
    return new_image_url

def create_caption (business_description, business_name):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompts = [
    f"Create a caption for a social media post for a (BUSINESS NAMED = {business_name}) and (BUSINESS DESCRIPTION = {business_description})",
    f"Create a cta for a social media post for a (BUSINESS NAMED = {business_name}) and (BUSINESS DESCRIPTION = {business_description})",
    f"Create a creative for a social media post for a (BUSINESS NAMED = {business_name}) and (BUSINESS DESCRIPTION = {business_description})",
    f"Create a fun caption for a social media post for a (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description})",
    f"Create a business toned caption for a social media post for a (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description})",
    ]
    prompt = random.choice(prompts)
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": "Keep it relatively short."
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=200
        )
    original_string = response.choices[0].message.content.strip()
    caption = original_string.strip('"')
    return caption

def create_dalle_post (key):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    ## GENERATE iMAGE
    prompt = f"describe one image you would find on social media that relates to {key} and make it a prompt so that i can generate that image in my image generator."
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    image_response = requests.get(image_url)
    image_data = BytesIO(image_response.content)

    return image_data

def create_stable_dif_post (key):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    ## GENERATE iMAGE
    prompt = f"I want you to create an image description based on these tags: {key}. The response should be less than 300 characters."

    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": "you are not a person. respond with just the output."
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=200
        )

    img = response.choices[0].message.content.strip()

    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-beta-v2-2-2/text-to-image"

    body = {
    "width": 512,
    "height": 512,
    "steps": 50,
    "cfg_scale": 7,
    "samples": 1,
    "style_preset": "photographic",
    "text_prompts": [
        {
        "text": img,
        "weight": 1
        }
    ],}
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": STABILITY_API_KEY,
    }
    response = requests.post(
    url,
    headers=headers,
    json=body,
    )
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))
    data = response.json()
    for i, image in enumerate(data["artifacts"]):
        image_content = base64.b64decode(image["base64"])
    image = Image.open(BytesIO(image_content))
    resized_img = image.resize((1024, 1024))
    image_io = BytesIO()
    resized_img.save(image_io, format='JPEG')
    image_io.seek(0)

    return image_io
    

def create_stock_post (key):
    ## CREATE IMAGE USING Unsplash
    base_url = 'https://api.unsplash.com/'
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_API_KEY}',
    }
    params = {
        'query': key,
        'count': 3,
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

    return image_io

def create_call_to_action(business_description, business_name, primary_color, colors_as_array, img_url, random_int, logo_path, isLogo):
    bg = generate_image_from_params(str(random_int), business_description, business_name, primary_color, colors_as_array, img_url, logo_path, 'graphic', isLogo)
    image_io = BytesIO()
    bg.save(image_io, format='PNG')
    image_io.seek(0)

    return image_io

def create_ad_creative(business_description, business_name, primary_color, colors_as_array, img_url, random_int, logo_path, isLogo):
    bg = generate_image_from_params(str(random_int), business_description, business_name, primary_color, colors_as_array, img_url, logo_path, 'ad', isLogo)
    image_io = BytesIO()
    bg.save(image_io, format='PNG')
    image_io.seek(0)

    return image_io

def create_upload(image_name, logo_path, isLogo, isCrop=False, coverage=0.015, gap_percentage=0.03):
    image_data = image_name.read()
    img = Image.open(BytesIO(image_data))
    img = correct_orientation(img)
    if img.format != 'JPEG':
        img = img.convert('RGB')

    if isCrop:
        width, height = img.size
        size = min(width, height)
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        img = img.crop((left, top, right, bottom))
        img = img.resize((1024, 1024))

    if isLogo:
        response = requests.get(logo_path)
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        img_area = img.width * img.height
        logo_area = img_area * coverage
        logo_side = int((logo_area ** 0.5))
        logo_resized = logo.resize((logo_side, logo_side), Image.LANCZOS)
        smaller_dimension = min(img.width, img.height)
        gap = int(smaller_dimension * gap_percentage)
        position = (img.width - logo_side - gap, img.height - logo_side - gap)
        img.paste(logo_resized, position, logo_resized)

    image_io = BytesIO()
    img.save(image_io, format='JPEG')
    image_io.seek(0) 

    return image_io

def create_placeholder(business_description, bucket_name, bucket_credentials, user_folder_path):
    image_url = 'https://th.bing.com/th/id/OIG.CO2sHWK_IEYIwzXsC2hX'
    image_size = 1024
    image_response = requests.get(image_url)
    image = Image.open(BytesIO(image_response.content))
    image.resize((image_size, image_size))
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return image_io

def create_ad_headline (business_description, business_name):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    ad_headline_prompt = f"Write me a maximum 30 character persuasive PAS-based Facebook Ad Headline call to action based on the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}]"
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": "you are not a person. respond with just the output."
                },
                {
                "role": "user",
                "content": ad_headline_prompt
                }
            ],
            temperature=1,
            max_tokens=200
        )
    ad_headline = response.choices[0].message.content.strip()
    ad_headline_str = re.sub(r'"+', '', ad_headline)

    return ad_headline_str

def create_ad_copy (business_description, biz_name):
    # Define the Business We Are Creating Media For
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    platform = "Social Media"
    ad_copy_prompt = f"Write me a persuasive PAS-based {platform} Ad that promotes {business_description}. The name of my business is {biz_name}\
    \
    Start by calling out the main problem, outlining the market's pain points, and providing details on the impacts that the [Create a Main Problem or Pain Point based on {business_description}] has on their life or business. Write this first part in 1 to 2 sentences max.\
    \
    Next, present the Agitation by digging deeper into the consequences and the emotional discomfort the reader experiences due to the problem, emphasizing the urgency to find a solution. Write this next part in 1 to 2 sentences max.\
    \
    Then, present the Solution by showcasing [{business_description}] as the answer to their needs. Then highlight the benefits [1-3 benefits based on {business_description}] that make it stand out.\
    \
    Motivate the reader to take the [A desired action based on {business_description}] and create a sense of urgency.\
    \
    Ensure that the output is a ready-to-use {platform} Ad that can be published immediately.\
    \
    Remember, this {platform} Ad needs to be persuasive and compelling and entices the market to take action."
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
            "role": "system",
            "content": "Respond with text that is less than than either 100, 75, or 50 words and is written at a Grade 4 readability level."
            },
            {
            "role": "user",
            "content": ad_copy_prompt
            }
        ],
        temperature=1,
        max_tokens=1000
    )
    original_string = response.choices[0].message.content.strip()
    ad_copy = re.sub(r'"+', '', original_string)

    return ad_copy

def add_logo (img, logo_path, coverage=0.015, gap_percentage=0.03):
    image_url = requests.get(img)
    img = Image.open(BytesIO(image_url.content))
    response = requests.get(logo_path)
    logo = Image.open(BytesIO(response.content)).convert("RGBA")
    img_area = img.width * img.height
    logo_area = img_area * coverage
    logo_side = int((logo_area ** 0.5))
    logo_resized = logo.resize((logo_side, logo_side), Image.LANCZOS)
    smaller_dimension = min(img.width, img.height)
    gap = int(smaller_dimension * gap_percentage)
    position = (img.width - logo_side - gap, img.height - logo_side - gap)
    img.paste(logo_resized, position, logo_resized)

    image_io = BytesIO()
    img.save(image_io, format='PNG')
    image_io.seek(0) 

    return image_io

def upload_jpg_to_google (image, bucket_name, bucket_credentials, user_folder_path):
    image_data = image.read()
    img = Image.open(BytesIO(image_data))
    image = correct_orientation(img)
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    filename = str(uuid.uuid4()) + ".jpg"
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image, content_type='image/jpeg')
    blob.make_public()

    return blob.public_url

def upload_png_to_google (image, bucket_name, bucket_credentials, user_folder_path):
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    filename = str(uuid.uuid4()) + ".png"
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image, content_type='image/png')
    blob.make_public()

    return blob.public_url

def upload_image_to_library (image, bucket_name, bucket_credentials, user_folder_path):
    image_data = image.read()
    img = Image.open(BytesIO(image_data))
    image = correct_orientation(img)
    if image.format != 'JPEG':
        image = image.convert('RGB')

    max_size = 1900

    # Open the image using PIL if it's not already an Image object
    if not isinstance(image, Image.Image):
        image = Image.open(image)

    # Resize the image if it's larger than the max size
    if image.width > max_size or image.height > max_size:
        if image.width > image.height:
            new_height = int(max_size * (image.height / image.width))
            new_size = (max_size, new_height)
        else:
            new_width = int(max_size * (image.width / image.height))
            new_size = (new_width, max_size)
        image = image.resize(new_size, Image.LANCZOS)

    # Convert the image to JPEG format
    image_bytes = BytesIO()
    image.save(image_bytes, format='JPEG')
    image_bytes.seek(0)

    # Setup Google Cloud Storage client
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    # Upload the image to GCS
    filename = str(uuid.uuid4()) + ".jpg"
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image_bytes, content_type='image/jpeg')
    blob.make_public()

    return blob.public_url

def upload_video_to_google(video, bucket_name, bucket_credentials, user_folder_path, file_extension):
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    print(1)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    print(2)
    bucket = client.bucket(bucket_name)
    print(3)
    filename = str(uuid.uuid4()) + "." + file_extension
    print(4)
    blob = bucket.blob(user_folder_path + filename)
    print(5)
    content_type = 'video/' + file_extension
    chunk_size = 1024 * 1024
    blob.chunk_size = chunk_size
    print(6)
    blob.upload_from_file(video, content_type=content_type)
    print(7)
    blob.make_public()

    return blob.public_url

def send_task (key, uid, dimensions, number):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    ## GENERATE iMAGE
    prompt = f"I want you to create an image description based on these tags: {key}. The response should be less than 300 characters."

    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                "role": "system",
                "content": "you are not a person. respond with just the output."
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            temperature=1,
            max_tokens=200
        )

    img_description = response.choices[0].message.content.strip()
    payload = {'uid': uid, 'prompt': prompt, 'dimensions': dimensions, 'number': number}
    DALLE3_URL = config('DALLE3_URL')
    def trigger_cloud_function_async():
        def send_request():
            requests.post(DALLE3_URL, json=payload)
        thread = threading.Thread(target=send_request)
        thread.start()

    trigger_cloud_function_async()

    return print('done')

def convert_color_to_hex(color):
    colors = {
    "white": "#FFFFFF",
    "black": "#000000",
    "red": "#FF0000",
    "green": "#008000",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "silver": "#C0C0C0",
    "gray": "#808080",
    "grey": "#808080",
    "maroon": "#800000",
    "olive": "#808000",
    "purple": "#800080",
    "teal": "#008080",
    "navy": "#000080",
    "fuchsia": "#FF00FF",
    "aqua": "#00FFFF",
    "lime": "#00FF00",
    "orange": "#FFA500",
    "brown": "#A52A2A",
    "pink": "#FFC0CB",
    "gold": "#FFD700",
    "beige": "#F5F5DC",
    "coral": "#FF7F50",
    "ivory": "#FFFFF0",
    "khaki": "#F0E68C",
    "lavender": "#E6E6FA",
    "turquoise": "#40E0D0",
    }

    if color.lower() in colors:
        return colors[color.lower()]

    if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color):
        return color

    if color.startswith("rgb"):
        rgb_values = color[4:-1].split(",")
        if all(value.strip().isdigit() for value in rgb_values):
            rgb_values = [int(value.strip()) for value in rgb_values]
            # Convert RGB to hex
            hex_color = "#{:02x}{:02x}{:02x}".format(*rgb_values)
            return hex_color

    return "#000000"