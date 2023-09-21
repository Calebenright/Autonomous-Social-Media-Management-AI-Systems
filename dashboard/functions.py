import uuid
import random
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import requests

# FOR DEVELOPMENT
from decouple import config
pixabay_api_key = config('PIXABAY_API_KEY')

def generate_unique_filename(extension):
    # Generate a unique filename using UUID
    unique_filename = str(uuid.uuid4()) + extension
    return unique_filename

# Define a function to generate random dates within your rules
def generate_random_date(last_date, existing_dates):
        
    # Generate a random number of days between 1 and 7
    days_to_add = random.randint(2, 6)
    
    # Calculate the new date by adding days_to_add to the last date
    new_datetime = last_date + timedelta(days=days_to_add)
    
    # Format the new date as 'YYYY-MM-DD'
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