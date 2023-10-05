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
import random
import json
import base64
import uuid

from decouple import config
openai.api_key = config('OPENAI_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')
STABILITY_API_KEY = config('STABILITY_API_KEY')

def create_graphic(website, background_color, key, post_num):

    # DEFINE IMAGE SIZE
    image_size = 1024

    if post_num < 3:
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

        png_image = Image.open(f'static/posts/1/{post_num}/1.png')
        bg.paste(png_image, (0, 0), png_image)

        png_to_color_change = f'static/posts/1/{post_num}/2.png'
        png_color_change = tint_image(png_to_color_change, background_color)
        bg.paste(png_color_change, (0, 0), png_color_change)
    else:
        bg = Image.new("RGB", (image_size, image_size), color=background_color)

        png_image = Image.open(f'static/posts/2/1.png')
        bg.paste(png_image, (0, 0), png_image)

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

    original_string = response.choices[0].text.strip()
    print(original_string)

    if original_string.startswith('"') or original_string.endswith('"'):
        middle_text = original_string.strip('"')
    else:
        middle_text = original_string

    d = ImageDraw.Draw(bg)

    fnt = ImageFont.truetype(font_path_semibold, 50)
    text_dim = d.textbbox((0, 0), middle_text, font=fnt)
    d.text(((image_size - text_dim[2]) / 2, post_nums[post_num - 1]), middle_text, font=fnt, fill=(255, 255, 255))

    image_io = BytesIO()
    bg.save(image_io, format='JPEG')
    image_io.seek(0)

    return image_io