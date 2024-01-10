## Copyright CJ Enright - 2023
## Feadl.io 1.0
## Feadl.io is a placeholder name for this software Application

## This Script uses a prompt to generate an image, convert it to jpg, and upload to instagram.

import os
import re
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account
from django.conf import settings
from django.templatetags.static import static 
from django.contrib.staticfiles.storage import staticfiles_storage
from .functions import tint_image, getPixabayImg
from .graphic_designer import generate_image_from_params, hex_to_rgb
import random
import json
import base64
import uuid
from decouple import config
from openai import OpenAI

UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

def create_caption (business_description, business_name):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompts = [
    f"Create a short social media caption for (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description}) | Remove quotations.",
    f"Create a goofy toned, short social media caption for (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description}) | Remove quotations.",
    f"Create a sophisticated toned, short social media caption for (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description}) | Remove quotations.",
    ]
    prompt = random.choice(prompts)
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
    original_string = response.choices[0].message.content.strip()
    caption = re.sub(r'"+', '', original_string)
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

def create_call_to_action(business_description, business_name, primary_color, colors_as_array, img_url, random_int, logo_path):
    bg = generate_image_from_params(str(random_int), business_description, business_name, primary_color, colors_as_array, img_url, logo_path, 'graphic')
    image_io = BytesIO()
    bg.save(image_io, format='PNG')
    image_io.seek(0)

    return image_io

def create_ad_creative(business_description, business_name, primary_color, colors_as_array, img_url, random_int, logo_path):
    bg = generate_image_from_params(str(random_int), business_description, business_name, primary_color, colors_as_array, img_url, logo_path, 'ad')
    image_io = BytesIO()
    bg.save(image_io, format='PNG')
    image_io.seek(0)

    return image_io

def create_upload(image_name, logo_path, isLogo, isGraphic, color, name):
    def add_drop_shadow(img, blur_radius=110, alpha=255):
        shadow = Image.new('RGBA', img.size, (0, 0, 0, alpha))
        expanded_shadow = Image.new('RGBA', (img.width + 2*blur_radius, img.height + 2*blur_radius), (0, 0, 0, 0))
        position = (blur_radius, blur_radius)
        expanded_shadow.paste(shadow, position)
        blurred_shadow = expanded_shadow.filter(ImageFilter.GaussianBlur(blur_radius))
        shadow_img = Image.new('RGBA', (img.width + 2*blur_radius, img.height + 2*blur_radius), (0, 0, 0, 0))
        shadow_img.paste(blurred_shadow, (0, 0), blurred_shadow)
        if img.mode == 'RGBA':
            mask = img.split()[3]
        else:
            mask = None
        shadow_img.paste(img, position, mask)

        return shadow_img

    image_data = image_name.read()
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
    
    if isGraphic:
        new_size = (int(cropped_img.width * 0.85), int(cropped_img.height * 0.85))
        cropped_img = cropped_img.resize(new_size, Image.Resampling.LANCZOS)
        cropped_img = add_drop_shadow(cropped_img)
        font_size = 40
        font = ImageFont.truetype("arial.ttf", font_size)
        name = "@" + name
        bg = Image.new('RGB', (1024, 1024), color)
        paste_position = ((bg.width - cropped_img.width) // 2, (bg.height - cropped_img.height) // 2)
        bg.paste(cropped_img.convert('RGB'), paste_position, cropped_img.split()[3])
        # r, g, b = hex_to_rgb(color)
        draw = ImageDraw.Draw(bg)
        draw.text((int(cropped_img.width * 0.15)/2 + 5, int(cropped_img.height * 0.85) - font_size * 1), name, font=font, fill=(255, 255, 255, 50))
        cropped_img = bg
    if isLogo:
        response = requests.get(logo_path)
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        if isGraphic:
            logo_width = int(0.14 * 1024)
            logo_height = int(logo_width * logo.size[1] / logo.size[0])
            logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
            position = (1024 - logo_width - 120, 1024 - logo_height - 120)
        else:
            logo_width = int(0.24 * 1024)
            logo_height = int(logo_width * logo.size[1] / logo.size[0])
            logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
            position = (1024 - logo_width - 20, 1024 - logo_height - 20)
        cropped_img.paste(logo, position, logo)
    image_io = BytesIO()
    cropped_img.save(image_io, format='JPEG')
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

def create_ad_copy (business_description, biz_name, platform):
    # Define the Business We Are Creating Media For
    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    ad_copy_prompt = f"Write me a persuasive PAS-based {platform} Ad that promotes {business_description}. The name of my business is {biz_name}\
    \
    Start by calling out the main problem, outlining the market's pain points, and providing details on the impacts that the [Create a Main Problem or Pain Point based on {business_description}] has on their life or business. Write this first part in 1 to 2 sentences max.\
    \
    Next, present the Agitation by digging deeper into the consequences and the emotional discomfort the reader experiences due to the problem, emphasizing the urgency to find a solution. Write this next part in 1 to 2 sentences max.\
    \
    Then, present the Solution by showcasing [{business_description}] as the answer to their needs. Introduce the Solution by starting with: “Don't worry. We've got you covered. Our {business_description} will help you:” Then highlight the benefits [1-3 benefits based on {business_description}] that make it stand out.\
    \
    Motivate the reader to take the [A desired action based on {business_description}] and emphasize [An offer based on {business_description}] to create a sense of urgency.\
    \
    Ensure that the output is a ready-to-use Facebook Ad that can be published immediately.\
    \
    Remember, this Facebook Ad needs to be persuasive and compelling and entices the market to take action.\
    \
    Make sure this ad is less than either 100, 75, or 50 words and is written at a Grade 4 readability level."
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
            "role": "system",
            "content": "you are not a person. respond with just the output."
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

def add_logo (img, logo_path):
    image_url = requests.get(img)
    image = Image.open(BytesIO(image_url.content))
    response2 = requests.get(logo_path)
    logo = Image.open(BytesIO(response2.content))
    logo_width = int(0.14 * 1024)
    logo_height = int(logo_width * logo.size[1] / logo.size[0])
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
    position = (1005 - logo.width, 1005 - logo.height)
    image.paste(logo, position, logo)

    image_io = BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0) 

    return image_io

def upload_jpg_to_google (image, bucket_name, bucket_credentials, user_folder_path):

    # Upload the image to Google Cloud Storage
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    filename = str(uuid.uuid4()) + ".jpg"
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image, content_type='image/jpeg')
    blob.make_public()

    return blob.public_url

def upload_png_to_google (image, bucket_name, bucket_credentials, user_folder_path):

    # Upload the image to Google Cloud Storage
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    filename = str(uuid.uuid4()) + ".png"
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image, content_type='image/png')
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

