import requests
from decouple import config
from openai import OpenAI

def create_tags (business_description):
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    prompt = f"Generate 5-10 tags that relate to the business description {business_description}. The response should be givin as only an array."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    prompt = response["choices"][0]["message"]["content"]
    return prompt