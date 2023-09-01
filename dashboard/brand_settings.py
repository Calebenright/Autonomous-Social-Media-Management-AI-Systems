import openai
import requests

# FOR DEVELOPMENT
from decouple import config
openai.api_key = config('OPENAI_API_KEY')

def create_tags (business_description):
    prompt = f"Generate 5-10 tags that relate to the business description {business_description}. The response should be givin as only an array."
    # Query OpenAI for a prompt 
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": prompt},
        ]
    )
    prompt = response["choices"][0]["message"]["content"]
    return prompt