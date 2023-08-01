## Copyright CJ Enright - 2023
## FEEDAI 1.0
## FeedAI is a placeholder name for this software Application

## This Script uses a prompt to generate an image, convert it to jpg, and upload to instagram.

import openai
import re
import requests
from PIL import Image
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account
from django.conf import settings
from .generate_unique_filename import generate_unique_filename
import random
import json

# FOR DEVELOPMENT
from decouple import config
openai.api_key = config('OPENAI_API_KEY')
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY')

# from project1.secrets_manager import get_secret_value
# openai.api_key = get_secret_value('OPENAI_API_KEY')
# UNSPLASH_API_KEY = get_secret_value('UNSPLASH_API_KEY')

def create_post (business_description, bucket_name, bucket_credentials, user_folder_path):
    post, url = create_AI_post (business_description, bucket_name, bucket_credentials, user_folder_path)
    return post, url

def create_AI_post (business_description, bucket_name, bucket_credentials, user_folder_path):
    # Define the Business We Are Creating Media For
    # biz = input("WHAT TYPE OF BUSINESS ARE WE MAKING CONTENT FOR? ENTER RESPONSE: ")

    biz = business_description

    # Generate a random number between 0 and 1 (inclusive)
    random_number = random.random()

    if random_number < 0.5:
            prompt = f"If i was givin a word cloud and one of the words was {biz}, What are 3-5 other descriptive phrases? Give the response only in the form of an array and include {biz}."
            # Query OpenAI for a prompt 
            response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                    {"role": "user", "content": prompt},
                ]
            )

            prompt = response["choices"][0]["message"]["content"]
            biz = random.choice(json.loads(prompt))

    caption = f"create a social media caption about {biz} in under 150 characters. add 1-3 relevent social-media hashtags related to this caption. "
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": caption},
        ]
    )
    # Store Caption as CAP for use in the caption later
    caption = response["choices"][0]["message"]["content"]

    # ## GENERATE HASHTAGS
    # hashtags = "generate 1-3 relevent social-media hashtags related to this caption: " + caption
    # # Query OpenAI to Generate Some Hashtags
    # response = openai.ChatCompletion.create(
    # model="gpt-3.5-turbo",
    # messages=[
    #         {"role": "user", "content": hashtags},
    #     ]
    # )
    # # Remove the numbers from the hashtags
    # hashtags = re.findall(r'#\w+', response["choices"][0]["message"]["content"])
    # hashtags = ' '.join(hashtags)
    # # Append to Create New Caption
    # print("CAPTION:", caption)
    # print("HASHTAGS:", hashtags)

    post = "clean up the following social media caption by removing numbers, quotations, mention of AI language model, and word counts: " + caption
    # Query OpenAI to Generate New Number-less prompt
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": post},
        ]
    )
    # Store New Value
    post = response["choices"][0]["message"]["content"]
    # Print
    print("POST:", post)

    ## GENERATE iMAGE
    img = f"describe one image you would find on social media that relates to {business_description} and make it a prompt so that i can generate that image in my image generator. remove any mention of family, people, and text from this prompt. Simplify the following image prompt in under 150 characters."

    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": img},
        ]
    )
    # Store Caption as img for use in the caption later
    img = response["choices"][0]["message"]["content"]

    # # Query Open AI for an image description
    # response = openai.ChatCompletion.create(
    # model="gpt-3.5-turbo",
    # messages=[
    #         {"role": "user", "content": img},
    #     ]
    # )
    # # Store Value
    # img = "remove mention of family, people, and text from this prompt: " + response["choices"][0]["message"]["content"]
    
    # # Query OpenAI to Remove Family Mention
    # response = openai.ChatCompletion.create(
    # model="gpt-3.5-turbo",
    # messages=[
    #         {"role": "user", "content": img},
    #     ]
    # )
    # # Store Value
    # img = "Simplify the following image prompt in under 150 characters: " + response["choices"][0]["message"]["content"]
    # # Query OpenAI to Remove Family Mention
    # response = openai.ChatCompletion.create(
    # model="gpt-3.5-turbo",
    # messages=[
    #         {"role": "user", "content": img},
    #     ]
    # )
    # # Store Value
    # img = response["choices"][0]["message"]["content"]
    # Print
    print("IMAGE DESCRIPTION:", img)


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

    # Upload the image to Google Cloud Storage
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    # Generate a unique filename for the image
    filename = generate_unique_filename(".jpg")

    # Upload the image file to the GCS bucket
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image_data, content_type='image/jpeg')
    blob.make_public()

    # Return the public URL of the uploaded image
    return post, blob.public_url

def create_stock_post (business_description, bucket_name, bucket_credentials, user_folder_path):
    # Define the Business We Are Creating Media For
    # biz = input("WHAT TYPE OF BUSINESS ARE WE MAKING CONTENT FOR? ENTER RESPONSE: ")

    biz = business_description

    # Generate a random number between 0 and 1 (inclusive)
    random_number = random.random()

    if random_number < 0.5:
        prompt = f"If i was givin a word cloud and one of the words was {biz}, What are 3-5 other descriptive phrases? Give the response only in the form of an array and include {biz}."
        # Query OpenAI for a prompt 
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "user", "content": prompt},
            ]
        )

        prompt = response["choices"][0]["message"]["content"]
        biz = random.choice(json.loads(prompt))

    caption = f"create a social media caption about {biz} in under 150 characters"
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": caption},
        ]
    )
    # Store Caption as CAP for use in the caption later
    caption = response["choices"][0]["message"]["content"]

    ## GENERATE HASHTAGS
    hashtags = "generate 1-3 relevent social-media hashtags related to this caption: " + caption
    # Query OpenAI to Generate Some Hashtags
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": hashtags},
        ]
    )
    # Remove the numbers from the hashtags
    hashtags = re.findall(r'#\w+', response["choices"][0]["message"]["content"])
    hashtags = ' '.join(hashtags)
    # Append to Create New Caption
    print("CAPTION:", caption)
    print("HASHTAGS:", hashtags)

    post = "clean up the following social media caption by removing numbers, quotations, mention of AI language model, and word counts: " + caption + " " + hashtags
    # Query OpenAI to Generate New Number-less prompt
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": post},
        ]
    )
    # Store New Value
    post = response["choices"][0]["message"]["content"]
    # Print
    print("POST:", post)

    ## CREATE IMAGE USING Unsplash
    base_url = 'https://api.unsplash.com/'
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_API_KEY}',
    }
    params = {
        'query': biz,
        'count': 1,
    }

    response = requests.get(f'{base_url}photos/random', headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
    data = response.json()
    for photo in data:
        image_url = photo['urls']['regular']

    # Download the image from the URL
    image_response = requests.get(image_url)
    image_data = BytesIO(image_response.content)

    # Upload the image to Google Cloud Storage
    credentials = service_account.Credentials.from_service_account_file(bucket_credentials)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    # Generate a unique filename for the image
    filename = generate_unique_filename(".jpg")

    # Upload the image file to the GCS bucket
    blob = bucket.blob(user_folder_path + filename)
    blob.upload_from_file(image_data, content_type='image/jpeg')
    blob.make_public()

    # Return the public URL of the uploaded image
    return post, blob.public_url

def create_call_to_action (business_description, bucket_name, bucket_credentials, user_folder_path):

    biz = business_description

    # Generate a random number between 0 and 1 (inclusive)
    random_number = random.random()

    if random_number < 0.5:
        prompt = f"If i was givin a word cloud and one of the words was {biz}, What are 3-5 other descriptive phrases? Give the response only in the form of an array and include {biz}."
        # Query OpenAI for a prompt 
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "user", "content": prompt},
            ]
        )

        prompt = response["choices"][0]["message"]["content"]
        biz = random.choice(json.loads(prompt))

    caption = f"create a social media caption about {biz} in under 150 characters"
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": caption},
        ]
    )
    # Store Caption as CAP for use in the caption later
    caption = response["choices"][0]["message"]["content"]

    ## GENERATE HASHTAGS
    hashtags = "generate 1-3 relevent social-media hashtags related to this caption: " + caption
    # Query OpenAI to Generate Some Hashtags
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": hashtags},
        ]
    )
    # Remove the numbers from the hashtags
    hashtags = re.findall(r'#\w+', response["choices"][0]["message"]["content"])
    hashtags = ' '.join(hashtags)
    # Append to Create New Caption
    print("CAPTION:", caption)
    print("HASHTAGS:", hashtags)

    post = "clean up the following social media caption by removing numbers, quotations, mention of AI language model, and word counts: " + caption + " " + hashtags
    # Query OpenAI to Generate New Number-less prompt
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": post},
        ]
    )
    # Store New Value
    post = response["choices"][0]["message"]["content"]
    # Print
    print("POST:", post)

    # Generate IMG
    middle_text = f"create a 2-4 word wesbite call to action"
    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": middle_text},
        ]
    )
    # Store Caption as CAP for use in the caption later
    middle_text = response["choices"][0]["message"]["content"]

    

    return post

# create_post('roofing', 'starter_web_app_bucket', 'credentials.json')
# DONE :)

