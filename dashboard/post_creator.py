## Copyright CJ Enright - 2023
## FEEDAI 1.0
## FeedAI is a placeholder name for this software Application

## This Script uses a prompt to generate an image, convert it to jpg, and upload to instagram.

import openai
import os
import re
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account
from django.conf import settings
from django.templatetags.static import static 
from django.contrib.staticfiles.storage import staticfiles_storage
from .generate_unique_filename import generate_unique_filename
import random
import json
import base64


# FOR DEVELOPMENT
from decouple import config
openai.api_key = config('OPENAI_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

# from project1.secrets_manager import get_secret_value
# openai.api_key = get_secret_value('OPENAI_API_KEY')
# UNSPLASH_API_KEY = get_secret_value('UNSPLASH_API_KEY')

def create_caption (business_description, business_name):
    # Define the Business We Are Creating Media For
    prompts = [
    f"Create a short social media caption for ([BUSINESS NAME] = [{business_name}]) and ([BUSINESS DESCRIPTION] = [{business_description}]) | Remove quotations.",
    f"Create a short social media caption for ([BUSINESS DESCRIPTION] = [{business_description}]) | Remove quotations.",
    ]
    prompt = random.choice(prompts)
    
    print(prompt)
    print(business_name)
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": prompt},
        ]
    )
    # Store Caption as CAP for use in the caption later
    original_string = response["choices"][0]["message"]["content"]
    if original_string.startswith('"') and original_string.endswith('"'):
        caption = original_string.strip('"')
    else:
        caption = original_string
    # print("CAPTION:", caption)

    return caption

def create_dalle_post (business_description, bucket_name, bucket_credentials, user_folder_path):

    ## GENERATE iMAGE
    img = f"describe one image you would find on social media that relates to {business_description} and make it a prompt so that i can generate that image in my image generator. Remove mention of family, people, and text from this prompt. Simplify the following image prompt in under 150 characters."

    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": img},
        ]
    )
    # Store Caption as CAP for use in the caption later
    img = response["choices"][0]["message"]["content"]
    # print("IMAGE DESCRIPTION:", img)

    ## CREATE IMAGE USING DALLE
    # Query Dalle for Image 
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

def create_stable_dif_post (business_description, bucket_name, bucket_credentials, user_folder_path):

    ## GENERATE iMAGE
    img = f"I want you to create an image description based on these tags: {business_description}. The response should be less than 300 characters."

    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": img},
        ]
    )
    # Store Caption as CAP for use in the caption later
    img = response["choices"][0]["message"]["content"]
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

def create_stock_post (business_description, bucket_name, bucket_credentials, user_folder_path):

    ## CREATE IMAGE USING Unsplash
    base_url = 'https://api.unsplash.com/'
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_API_KEY}',
    }
    params = {
        'query': business_description,
        'count': 1,
    }

    response = requests.get(f'{base_url}photos/random', headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
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

def create_call_to_action(website, background_color, logo_path, business_description, bucket_name, bucket_credentials, user_folder_path):
    # DEFINE IMAGE SIZE
    image_size = 1024

    middle_text = f"Create a 2-4 word business call to action about {business_description}. respond with only the call to action. remove quotations."
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": middle_text},
        ]
    )
    # Store Caption as CAP for use in the caption later
    middle_text = response["choices"][0]["message"]["content"]
    
    # Prompt the user for a Dalle prompt
    myPrompt = "Create a texture that is black and white so that i can overlay it on a background image"
    # Generate an image based on the Dalle prompt
    response = openai.Image.create(
        prompt= myPrompt,
        n=1,
        size="1024x1024",
    )

    # Retrieve the URL of the generated image from the API response
    image_url = response['data'][0]['url']

    # Download the image from the URL
    image_response = requests.get(image_url)
    image_data = BytesIO(image_response.content)

    # Create an image object with dimensions image_size x image_size
    img = Image.new('RGB', (image_size, image_size), color=background_color)

    # Open the black and white texture image and resize it to match the dimensions of the final image
    texture = Image.open(image_data)
    texture = texture.resize((image_size, image_size))

    # Apply the texture overlay onto the background image using blend mode
    img = Image.blend(img, texture, alpha=0.07)  # Adjust alpha as needed

    # Create a Draw object for the image
    d = ImageDraw.Draw(img)

    font_path_semibold = 'static/dashboard/fonts/Poppins-SemiBold.ttf'
    font_path_regular = 'static/dashboard/fonts/Poppins-Regular.ttf'

    fnt = ImageFont.truetype(font_path_semibold, int(image_size * 1 / 14))
    fnt_smaller = ImageFont.truetype(font_path_regular, int(image_size * 1 / 30))

    # Calculate text dimensions for call to action and website
    text_dim = d.textbbox((0, 0), middle_text, font=fnt)
    text_dim_website = d.textbbox((0, 0), website, font=fnt_smaller)

    # Write call to action in the middle of the image in white
    d.text(((img.width - text_dim[2]) / 2, (img.height - text_dim[3]) / 2), middle_text, font=fnt, fill=(255, 255, 255))

    # Write the website at the bottom of the image
    d.text(((img.width - text_dim_website[2]) / 2, img.height - (text_dim_website[3] * 3/2)), website, font=fnt_smaller, fill=(255, 255, 255))

    image_io = BytesIO()
    img.save(image_io, format='JPEG')
    image_io.seek(0)

    return image_io

def create_upload(image_name):
    image_data = image_name.read()

    # Open the image using PIL
    img = Image.open(BytesIO(image_data))

    # Check if the image is not already in JPEG format
    if img.format != 'JPEG':
        # Convert the image to JPEG format
        img = img.convert('RGB')

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

def create_placeholder(business_description, bucket_name, bucket_credentials, user_folder_path):
    image_url = 'https://th.bing.com/th/id/OIG.CO2sHWK_IEYIwzXsC2hX'
    image_size = 1024
    # Download the image from the URL
    image_response = requests.get(image_url)
    image = Image.open(BytesIO(image_response.content))
    image.resize((image_size, image_size))

    # Create a BytesIO buffer to save the image
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return image_io

def create_ad_copy (business_description, bucket_name, bucket_credentials, user_folder_path):
    # Define the Business We Are Creating Media For
    # biz = input("WHAT TYPE OF BUSINESS ARE WE MAKING CONTENT FOR? ENTER RESPONSE: ")

    biz = business_description

    ad_copy_prompt = f"Write me a persuasive PAS-based Facebook Ad that promotes [Your Product/Service].\
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
    [Main Problem or Pain Point] = Create a Main Problem or Pain Point based on {biz}\
    [Benefit 1] = Create a Benefit based on this business description, {biz}\
    [Benefit 2] = Create another Benefit based on this business description, {biz}\
    [Desired Action] = Send us a Direct Message\
    [Your Offer] = Limited Time\
    [Max # of words in ad] = 400\
    "
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": ad_copy_prompt},
        ]
    )
    # Store Caption as CAP for use in the caption later
    ad_copy = response["choices"][0]["message"]["content"]
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

def upload_to_google (image, bucket_name, bucket_credentials, user_folder_path, num_post):

    # Upload the image to Google Cloud Storage
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    # Generate a unique filename for the image
    filename = str(num_post) + ".jpg"

    # Upload the image file to the GCS bucket
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image, content_type='image/jpeg')
    blob.make_public()

    return blob.public_url

def create_image (website, color, selected_option, isLogo, logo_path, business_description, bucket_name, bucket_credentials, user_folder_path, num_post):

    if selected_option == 'stable-dif':
        img = create_stable_dif_post(business_description, bucket_name, bucket_credentials, user_folder_path)
    elif selected_option == 'stock':
        img = create_stock_post(business_description, bucket_name, bucket_credentials, user_folder_path)
    elif selected_option == 'cta':
        img = create_call_to_action(website, color, logo_path, business_description, bucket_name, bucket_credentials, user_folder_path)
    elif selected_option == 'up':
        img = create_upload(business_description)
    else:
        img = create_dalle_post(business_description, bucket_name, bucket_credentials, user_folder_path)

    if isLogo == 'true':
       if logo_path is not None:
            img = add_watermark(img, logo_path)

    url = upload_to_google(img, bucket_name, bucket_credentials, user_folder_path, num_post)

    return url

def create_ad (isLogo, logo_path, business_description, bucket_name, bucket_credentials, user_folder_path, num_ad):

    options = ['stable-dif', 'stock']
    selected_option = random.choice(options)
    if selected_option == 'stable-dif':
        img = create_stable_dif_post(business_description, bucket_name, bucket_credentials, user_folder_path)
    elif selected_option == 'stock':
        img = create_stock_post(business_description, bucket_name, bucket_credentials, user_folder_path)
    else:
        img = create_stable_dif_post(business_description, bucket_name, bucket_credentials, user_folder_path)

    if isLogo == 'true':
        if logo_path is not None:
                img = add_watermark(img, logo_path)

    url = upload_to_google(img, bucket_name, bucket_credentials, user_folder_path, num_ad)

    return url

# create_post('roofing', 'starter_web_app_bucket', 'credentials.json')
# DONE :)

