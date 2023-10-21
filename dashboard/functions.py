import uuid
import random
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import openai
import requests
import re
import json

# FOR DEVELOPMENT
from decouple import config
pixabay_api_key = config('PIXABAY_API_KEY')
openai.api_key = config('OPENAI_API_KEY')

def create_text_post(platform, business_description, business_name):
    prompt = f"I need a social media text post for the business named [BUSINESS NAME = {business_name}] and has a business description [BUSINESS DESCRIPTION = {business_description}] and is specific to the platform [PLATFORM = {platform}]."
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    original_string = original_string.replace('"', '').replace("'", "")
    return original_string

def create_tags(business_description):
    prompt = f"Produce an array of 7-10 tags that start general and get more specific and relate to the business description: {business_description}."
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    print('ORIGINAL: ', original_string)
    items = re.split(r'\d+\.', original_string)
    items = [item.strip() for item in items if item.strip()]
    tags = '["' + '", "'.join(items) + '"]'
    print('Tags: ', tags)
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