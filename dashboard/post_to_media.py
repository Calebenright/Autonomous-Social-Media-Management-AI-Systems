import requests

access_token = "AQU4PVX5TB-6unk4GhKPenm92sHDdFuWa4nqBktBJpFRT4sYBmICNFbaXnDGVdS0ELwoo8_rmhACPySZpZQdxIHbEgN-y9McEDCGu8sv2iCflxYhldk0sAwBbi_npZEcrsP_D4BjLkEi5aSt9n2D223CaMBrJ1BlERsyBHz4j_-IeO20bMse6eyCZ9ncnBlobuJGXMP3lAUynS5wrU3IpFYvH_mj-qPjyeraSSD1_XwNlscVqDVRaUdQCta-HJtIGmYAzhjol78z1bIOqAaPuu2UFvsVSx_GQS8ekufs6PLTAs2je0avXkbqgnl0gz5nsV_U3u3gU_c6R4DA0zf4iPtmvdcKBA"

# Define the API endpoint to get the authenticated user's profile
api_url = "https://api.linkedin.com/v2/me"

# Set headers, including the Authorization header with the access token
headers = {
    "Authorization": f"Bearer {access_token}"
}

# Make a GET request to get the authenticated user's profile
response = requests.get(api_url, headers=headers)

if response.status_code == 200:
    # Parse the JSON response to get the user's LinkedIn ID
    user_data = response.json()
    author_id = user_data["id"]
    print("AID", author_id)
else:
    print("Failed to get user profile. Status code:", response.status_code)
    print(response.text)
    author_id = None

# Define the URL of the image you want to upload
image_url = "https://farm8.staticflickr.com/7329/11461238585_97da4950e3_o.jpg"

# Define the API endpoint to register the image upload
upload_url = "https://api.linkedin.com/v2/assets?action=registerUpload"

# Define the payload for registering the image upload
upload_payload = {
    "registerUploadRequest": {
        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
        "owner": "urn:li:person:" + author_id,
        "serviceRelationships": [
            {
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }
        ]
    }
}

# Make a POST request to register the image upload
upload_response = requests.post(upload_url, json=upload_payload, headers=headers)

if upload_response.status_code == 201:
    # Parse the JSON response to get the media reference
    media_data = upload_response.json()
    media_reference = media_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    print(media_reference)
else:
    print("Failed to register image upload. Status code:", upload_response.status_code)
    print(upload_response.text)
    media_reference = None


# Define your LinkedIn API endpoint and access token
api_url = "https://api.linkedin.com/v2/ugcPosts"

# Define the content of your post, including the image URL
post_data = {
    "author": author_id,
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Hey LinkedIn! Just wanted to share a picture I took today. I also posted this with my new app I'm developing: www.feadl.io"
            },
            "shareMediaCategory": "IMAGE",
            "media": [
                {
                    "status": "READY",
                    "description": {
                        "text": "The Sunset Today!"
                    },
                    "media": media_reference,
                    "title": {
                        "text": "Dallas, TX."
                    }
                }
            ]
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}

# Set headers, including the Authorization header with the access token
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "x-li-format": "json"
}

# Make a POST request to create the post
response = requests.post(api_url, json=post_data, headers=headers)

# Check the response
if response.status_code == 201:
    print("Post successfully created on LinkedIn!")
else:
    print("Failed to create post on LinkedIn. Status code:", response.status_code)
    print(response.text)

