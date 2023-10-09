## Copyright CJ Enright - 2023
## Feadl.io 1.0
## Feadl.io is a placeholder name for this software Application

## This Script uses a prompt to generate an image, convert it to jpg, and upload to instagram.

import openai
import os
import re
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account
from django.conf import settings
from django.templatetags.static import static 
from django.contrib.staticfiles.storage import staticfiles_storage
from .functions import generate_unique_filename, tint_image, getPixabayImg
from .graphic_designer import create_graphic
import random
import json
import base64
import uuid

from decouple import config
openai.api_key = config('OPENAI_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

def create_caption (business_description, business_name):
    # Define the Business We Are Creating Media For
    prompts = [
    f"Create a short social media caption for (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description}) | Remove quotations.",
    f"Create a short social media caption for (BUSINESS DESCRIPTION = {business_description}) | Remove quotations.",
    ]
    prompt = random.choice(prompts)
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    if original_string.startswith('"') or original_string.endswith('"'):
        caption = original_string.strip('"')
    else:
        caption = original_string

    return caption

def create_dalle_post (key):

    ## GENERATE iMAGE
    prompt = f"describe one image you would find on social media that relates to {key} and make it a prompt so that i can generate that image in my image generator."

    # Make a request to the OpenAI API
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )

    # Extract the generated description from the response
    img = response.choices[0].text.strip()

    print("IMAGE DESCRIPTION:", img)

    ## CREATE IMAGE USING DALLE
    response = openai.Image.create(
        prompt= img,
        n=1,
        size="1024x1024",
    )
    # Retrieve the URL of the generated image from the API response
    image_url = response['data'][0]['url']

    # Download the image from the URL
    image_response = requests.get(image_url)
    image_data = BytesIO(image_response.content)

    return image_data

def create_stable_dif_post (key):
    ## GENERATE iMAGE
    prompt = f"I want you to create an image description based on these tags: {key}. The response should be less than 300 characters."

    # Make a request to the OpenAI API
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )

    # Extract the generated description from the response
    img = response.choices[0].text.strip()

    print("IMAGE DESCRIPTION:", img)

    ## CREATE IMAGE USING STABLE DIFFUSION
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
    ],
    }

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

    # Create a BytesIO buffer to save the image
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
        'count': 1,
    }

    response = requests.get(f'{base_url}photos/random', headers=headers, params=params)
    response.raise_for_status()  
    data = response.json()
    for photo in data:
        image_url = photo['urls']['regular']

    # Download the image from the URL
    image_response = requests.get(image_url)
    image_data = image_response.content

    # Open the image using PIL
    img = Image.open(BytesIO(image_data))

    # Get the dimensions of the image
    width, height = img.size

    # Calculate the size of the square to crop (using the smaller dimension)
    size = min(width, height)

    # Calculate the cropping box (centered)
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2

    # Crop the image to the calculated square
    cropped_img = img.crop((left, top, right, bottom))
    resized_img = cropped_img.resize((1024, 1024))

    image_io = BytesIO()
    resized_img.save(image_io, format='JPEG')
    image_io.seek(0) 

    return image_io

def create_call_to_action(website, background_color, key, random_int):

    # DEFINE IMAGE SIZE
    image_size = 1024

    if random_int <= 3:
        base_url = 'https://api.unsplash.com/'
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_API_KEY}',
        }
        params = {
            'query': key,
            'count': 1,
        }

        response = requests.get(f'{base_url}photos/random', headers=headers, params=params)
        response.raise_for_status()  
        data = response.json()
        for photo in data:
            image_url = photo['urls']['regular']

        # Download the image from the URL
        image_response = requests.get(image_url)
        image_data = BytesIO(image_response.content)
        bg = Image.open(image_data)

        width, height = bg.size
        size = min(width, height)

        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2

        cropped_img = bg.crop((left, top, right, bottom))
        bg = cropped_img.resize((image_size, image_size))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=3))

        png_image = Image.open(f'static/posts/1/{random_int}/1.png')
        bg.paste(png_image, (0, 0), png_image)

        png_to_color_change = f'static/posts/1/{random_int}/2.png'
        png_color_change = tint_image(png_to_color_change, background_color)
        bg.paste(png_color_change, (0, 0), png_color_change)
    else:
        bg = Image.new("RGB", (image_size, image_size), color=background_color)

        png_image = Image.open(f'static/posts/2/1.png')
        bg.paste(png_image, (0, 0), png_image)


    image_io = BytesIO()
    bg.save(image_io, format='JPEG')
    image_io.seek(0)

    return image_io

def add_text(image_url, key, random_int, website):
    image_size = 1024
    font_path_extrabold = 'static/dashboard/fonts/Poppins-ExtraBold.ttf'
    font_path_bold = 'static/dashboard/fonts/Poppins-Bold.ttf'
    font_path_semibold = 'static/dashboard/fonts/Poppins-SemiBold.ttf'
    font_path_regular = 'static/dashboard/fonts/Poppins-Regular.ttf'
    font_path_thin = 'static/dashboard/fonts/Poppins-Thin.ttf'
    post_nums = [
        800,
        600,
        830,
        170
    ]

    prompt = f"Create a short 2-5 word business call to action about {key}."
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )

    middle_text = response.choices[0].text.strip()
    print(middle_text)


    image_response = requests.get(image_url)
    image = Image.open(BytesIO(image_response.content))

    d = ImageDraw.Draw(image)

    fnt = ImageFont.truetype(font_path_semibold, 50)
    text_dim = d.textbbox((0, 0), middle_text, font=fnt)
    d.text(((image_size - text_dim[2]) / 2, post_nums[random_int - 1]), middle_text, font=fnt, fill=(255, 255, 255))

    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)

    return image_io

def create_upload(image_name, isGraphic):
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
    resized_img = cropped_img.resize((1024, 1024))

        # if isGraphic:
        #     pass

    image_io = BytesIO()
    resized_img.save(image_io, format='JPEG')
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

def create_ad_copy (business_description, biz_name):
    # Define the Business We Are Creating Media For
    # biz = input("WHAT TYPE OF BUSINESS ARE WE MAKING CONTENT FOR? ENTER RESPONSE: ")

    biz = business_description

    ad_copy_prompt = f"Write me a persuasive PAS-based Facebook Ad that promotes [Your Product/Service]. The name of my business is [Your Business Name]\
    \
    Start by calling out the main problem, outlining the market's pain points, and providing details on the impacts that the [Main Problem] has on their life or business. Write this first part in 1 to 2 sentences max.\
    \
    Next, present the Agitation by digging deeper into the consequences and the emotional discomfort the reader experiences due to the problem, emphasizing the urgency to find a solution. Write this next part in 1 to 2 sentences max.\
    \
    Then, present the Solution by showcasing [Your Product/Service] as the answer to their needs. Introduce the Solution by starting with: “Don't worry. We've got you covered. Our [Your Product/Service] will help you:” Then highlight the benefits [Benefit 1, Benefit 2] that make it stand out.\
    \
    Motivate the reader to take the [Desired Action] and emphasize [Your Offer] to create a sense of urgency.\
    \
    Ensure that the output is a ready-to-use Facebook Ad that can be published immediately.\
    \
    Remember, this Facebook Ad needs to be persuasive and compelling and entices the market to take action.\
    \
    Make sure this ad is less than [Max # of words in ad] words and is written at a Grade 4 readability level.\
    \
    [Your Product/Service] = {biz}\
    [Your Business Name] = {biz_name}\
    [Main Problem or Pain Point] = Create a Main Problem or Pain Point based on {biz}\
    [Benefit 1] = Create a Benefit based on this business description, {biz}\
    [Benefit 2] = Create another Benefit based on this business description, {biz}\
    [Desired Action] = Send us a Direct Message\
    [Your Offer] = Limited Time\
    [Max # of words in ad] = 400\
    "
    # Make a request to the OpenAI API
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=ad_copy_prompt,
        max_tokens=500,
        temperature=1
    )

    # Extract the generated description from the response
    ad_copy = response.choices[0].text.strip()

    print("AD_COPY:", ad_copy)

    return ad_copy

def add_watermark (image, logo_path):

    image = Image.open(image)

    # Load the logo
    response2 = requests.get(logo_path)
    logo = Image.open(BytesIO(response2.content))

    # Resize the logo to a specific width and maintain the aspect ratio
    logo_width = int(0.34 * 1024)
    logo_height = int(logo_width * logo.size[1] / logo.size[0])
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

    # Calculate the position to place the logo in the bottom right corner
    position = (1024 - logo.width, 1024 - logo.height)

    # Paste the logo on the image at the defined position
    image.paste(logo, position, logo)

    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0) 

    return image_io

def upload_to_google (image, bucket_name, bucket_credentials, user_folder_path):

    # Upload the image to Google Cloud Storage
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    # Generate a unique filename for the image
    filename = str(uuid.uuid4()) + ".jpg"

    # Upload the image file to the GCS bucket
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image, content_type='image/jpeg')
    blob.make_public()

    return blob.public_url

def create_image (website, color, selected_option, isLogo, logo_path, business_description, bucket_name, bucket_credentials, user_folder_path, post_num):

    if selected_option == 'cta':
        img = create_call_to_action(website, color, business_description, post_num)
    elif selected_option == 'text':
        img = add_text(logo_path, business_description, post_num, website)
        isLogo = False

    if isLogo == 'true':
       if logo_path is not None:
            img = add_watermark(img, logo_path)

    url = upload_to_google(img, bucket_name, bucket_credentials, user_folder_path)

    return url

def create_ad (isLogo, logo_path, key, bucket_name, bucket_credentials, user_folder_path, num_ad):

    options = ['stable-dif', 'stock']
    selected_option = random.choice(options)
    if selected_option == 'stable-dif':
        img = create_stable_dif_post(key)
    elif selected_option == 'stock':
        img = create_stock_post(key)

    if isLogo == 'true':
        if logo_path is not None:
                img = add_watermark(img, logo_path)

    url = upload_to_google(img, bucket_name, bucket_credentials, user_folder_path)

    return url

# create_post('roofing', 'starter_web_app_bucket', 'credentials.json')
# DONE :)

