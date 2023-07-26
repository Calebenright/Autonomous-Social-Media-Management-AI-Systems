import openai
from decouple import config

openai.api_key = config('OPENAI_API_KEY')

def generate_comment(recent_comment):
    comment_query = f"pretend you are the social media manager and a person commented the following: {recent_comment}. Give me a good response back in under 150 characters."

    # Query OpenAI for a caption
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": comment_query},
        ]
    )
    # Store Caption as CAP for use in the caption later
    comment = response["choices"][0]["message"]["content"]

    return comment
