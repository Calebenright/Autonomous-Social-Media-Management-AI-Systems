import requests
import json

def post_to_facebook_page_feed(caption, image_url, page_id, page_access_token):
    # Endpoint to post to the page's feed
    post_endpoint = f"https://graph.facebook.com/v13.0/{page_id}/feed"
    post_params = {
        "message": caption,
        "link": image_url,
        "access_token": page_access_token,
    }
    post_response = requests.post(post_endpoint, params=post_params).json()

    return post_response

def upload_image_from_url_to_linkedin(image_url, access_token, access_id):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    response = requests.get(image_url)
    image_content = response.content
    register_endpoint = "https://api.linkedin.com/v2/assets?action=registerUpload"
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{access_id}", 
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    register_response = requests.post(
        register_endpoint,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        },
        data=json.dumps(register_payload)
    ).json()
    upload_url = register_response.get("value", {}).get("uploadMechanism", {}).get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}).get("uploadUrl")
    if not upload_url:
        return None
    upload_response = requests.put(upload_url, headers=headers, data=image_content)
    if upload_response.status_code != 201:
        return None
    asset = register_response.get("value", {}).get("asset")
    return asset


def post_to_linkedin(caption, image_url, access_token, access_id):
    linkedin_id = access_id
    media_id = upload_image_from_url_to_linkedin(image_url, access_token, access_id)
    print(media_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-li-format": "json"
    }
    payload = {
        "author": f"urn:li:person:{linkedin_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": caption
                },
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "description": {
                        "text": caption
                    },
                    "media": media_id, 
                    "title": {
                        "text": "Title of your post"
                    }
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    ).json()
    return response

def get_instagram_user_id(facebook_page_id, access_token):
    endpoint = f"https://graph.facebook.com/v13.0/{facebook_page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": access_token
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    if 'instagram_business_account' in data:
        return data['instagram_business_account']['id']
    else:
        print("Error:", data.get('error', {}).get('message', 'Unknown error'))
        return None
    
def get_instagram_account_id_via_pages(access_token):
    endpoint = f"https://graph.facebook.com/v12.0/me/accounts?access_token={access_token}"
    response = requests.get(endpoint).json()
    
    for page in response.get('data', []):
        if 'instagram_business_account' in page:
            return page['instagram_business_account']['id']
    
    print("No associated Instagram Business Account found.")
    return None

def get_facebook_page_id(access_token):
    # Endpoint to get the list of Facebook Pages managed by the user
    endpoint = f"https://graph.facebook.com/v18.0/me/accounts?access_token={access_token}"
    response = requests.get(endpoint).json()
    print(response) 

    # Check if the user manages any pages
    if 'data' in response and len(response['data']) > 0:
        return response['data'][0]['id']
    else:
        print(response) 
        return None
    # return response['id']

def post_to_instagram(access_token, image_url, caption, instagram_user_id):
    # facebook_page_id = get_facebook_page_id(access_token)
    # instagram_user_id = get_instagram_user_id(facebook_page_id, access_token)
    # instagram_user_id = get_facebook_page_id(access_token)
    # print(instagram_user_id)

    endpoint = f"https://graph.facebook.com/{instagram_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    
    response = requests.post(endpoint, data=payload)
    result = response.json()

    if 'id' not in result:
        print("Failed to create media object:", result)
        return

    creation_id = result['id']
    publish_endpoint = f"https://graph.facebook.com/{instagram_user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    publish_response = requests.post(publish_endpoint, data=publish_payload)
    publish_result = publish_response.json()

    if 'id' in publish_result:
        print(f"Successfully posted to Instagram with ID: {publish_result['id']}")
    else:
        print("Failed to publish post to Instagram:", publish_result)

def post_to_google_mybusiness(caption, image_url, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Define the post payload
    payload = {
        "languageCode": "en-US",
        "summary": caption,
        "media": [
            {
                "mediaFormat": "PHOTO",
                "sourceUrl": image_url
            }
        ]
    }

    # Replace 'YOUR_ACCOUNT_NAME' and 'YOUR_LOCATION_ID' with appropriate values
    endpoint = f"https://mybusiness.googleapis.com/v4/accounts/YOUR_ACCOUNT_NAME/locations/YOUR_LOCATION_ID/localPosts"

    response = requests.post(endpoint, headers=headers, json=payload).json()
    return response

def post_to_socials(platform, caption, image_url, access_token, access_id):
    if platform == "facebook":
        return post_to_facebook_page_feed(caption, image_url, access_id, access_token)
    elif platform == "instagram":
        return post_to_instagram(access_token, image_url, caption)
    elif platform == "linkedin":
        return post_to_linkedin(caption, image_url, access_token, access_id)
    elif platform == "google_mybusiness":
        return post_to_google_mybusiness(caption, image_url, access_token)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

if __name__ == "__main__":
    instagram_token = 'EAADFIOXHRl4BO8Ya2HS8LWEA9dWhOWNznLg1d07NrWbxRZBDZAu5xwbURVN4COZAosgS85ihAZCmhpyk0cP9ZB0IP6Qk7Lpo0om513O2JXwn68pr17wZAQXAIInezf00OdOFqGa0i9MLwSYXdbhApdfJbM34N5y9GzGC9O1lxu2UEsBKw0OhwmOWZCjKoW9wRfRyZBDJJWJNceNHSI4ct5knnU1v6y8ZD'
    facebook_token = "EAADFIOXHRl4BOZBbxOJfeG7oHZBIOyClbji1elPm2olmNYJeXNB6MHydxROcWkJ4ZBDDKuRdI5PJ11iy85ZBfR21F5EL78ZBXUlMfgGZBsBeAxyHzPGvyY023ZC8VS9MgmSmSP5Bv9UyqhfnZA2asWKwxAswaULYOm0o3yychOWjybobzTd8wgDlzZBp9zgWvYanrdZAFS4t8ZCILTQzZAd6yp6sxPZAfSTMZD"
    facebook_id = '108830535605871'
    linkedin_token = 'AQWkp5YGkAF8YMEV6mamPNbOG22-LoUIYLBEZzXXmetr91pZwFa6yhPRDtiZhFNIHzvmMpdagQ3jGXPf0EnR4gznpm6_RwExYWlXevEMXLgI59G08edmKFokBboJoZtHWirewepn0ozKVhi-r-yJKgBbNg9p3eUZwh3mhMBgAudHeeTWn6bXolA9VLr_CyY1RgHBxUAOjs_8pgNaC8X19TkKkblzPGmdsfCSTqqGL7upQKz6h4CmCJu51ddQoyo-ovfiJ_kD70PKsvBrtEgPzqUQHAAtp8bhjr3ttzU-PcG1r9BcaA1hCdQinEq5sc8Zf2O0W7WX1A1cwUfqrvUbWSAdz3uxRg'
    linkedin_id = 'xFUUk10kPj'
    
    PLATFORM = "instagram"
    CAPTION = "Testing....."
    IMAGE_URL = "https://storage.googleapis.com/starter_web_app_bucket/user_folders/ai_image_library/04ec205c-03b1-48ae-9e3f-066c9c47d8da.jpg"
    ACCESS_ID = linkedin_id
    ACCESS_TOKEN = instagram_token
    response = post_to_socials(PLATFORM, CAPTION, IMAGE_URL, ACCESS_TOKEN, ACCESS_ID)
    print(response)
