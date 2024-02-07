import os
from google.cloud import firestore
from google.oauth2 import service_account
import re
import json
from openai import OpenAI
from decouple import config
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file located in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

key_path = "firebase-adminsdk.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

db = firestore.Client(credentials=credentials, project=credentials.project_id)

def create_title():
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    client = OpenAI()
    prompt = "I need a title for a blog post for my website. Our site is about social media marketing, service-based businesses, ai-driven marketing, large language social media model, image generator for social media. The title should be about 10-15 words long."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": 'you are a helpful assistant.'},
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        max_tokens=100
    )
    original_string = response.choices[0].message.content.strip()
    return original_string

def create_article(title):
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    client = OpenAI()
    prompt = "Write a blog post about the following title: " + title
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": 'Generate it in <h6> and <p> HTML tag format.'},
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        max_tokens=500
    )
    original_string = response.choices[0].message.content.strip()
    return original_string

def generate_slug(title):
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug

def read_article_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("The file was not found.")
        return ""

def add_document_auto_id(collection_name, data):
    try:
        db.collection(collection_name).add(data)
        print(f"Document added to {collection_name} with an auto-generated ID.")
    except Exception as e:
        print(f"An error occurred: {e}")

def set_document_custom_id(collection_name, document_id, data):
    try:
        db.collection(collection_name).document(document_id).set(data)
        print(f"Document added/updated in {collection_name} with custom ID: {document_id}")
    except Exception as e:
        print(f"An error occurred: {e}")

def pull_stock(key):
    unsplash_api_key = os.getenv('UNSPLASH_API_KEY')
    base_url = 'https://api.unsplash.com/'
    headers = {
        'Authorization': f'Client-ID {unsplash_api_key}',
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

    return image_url

if __name__ == "__main__":
    collection_name = 'articles'

    title = create_title()

    content = create_article(title)

    key = 'Social Media'
    img = pull_stock(key)

    article_data = {
        'title': title,
        'content': content,
        'publishedDate': firestore.SERVER_TIMESTAMP,
        'slug': generate_slug(title),
        'image': img
    }

    add_document_auto_id(collection_name, article_data)

    print(content)

    # Add or update a document with a custom ID
    # custom_document_id = 'custom_article_id'
    # set_document_custom_id(collection_name, custom_document_id, article_data)
