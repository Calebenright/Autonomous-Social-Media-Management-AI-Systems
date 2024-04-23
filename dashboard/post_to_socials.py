import requests
import json
import tempfile
from moviepy.editor import VideoFileClip
import os

# --------------------- GET --------------------------- #

def get_instagram_user_id(facebook_page_id, access_token):
    endpoint = f"https://graph.facebook.com/v17.0/{facebook_page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": access_token
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    if 'instagram_business_account' in data:
        return data['instagram_business_account']['id']
    else:
        return None

def get_facebook_pages_and_groups(access_token):
    combined_data = []
    pages_endpoint = f"https://graph.facebook.com/v18.0/me/accounts?access_token={access_token}"
    try:
        pages_response = requests.get(pages_endpoint).json()
    except:
        pass

    if 'data' in pages_response and len(pages_response['data']) > 0:
        for page in pages_response['data']:
            combined_data.append({'access_token': page['access_token'], 'id': page['id'], 'name': page['name'], 'type': 'page'})

    if combined_data:
        return combined_data, len(combined_data) > 1
    else:
        print("No page or group data found in the response")
        return None, False

def exchange_short_lived_token_for_long_lived(short_lived_access_token, app_id, app_secret):
    # Endpoint for exchanging tokens
    url = "https://graph.facebook.com/v17.0/oauth/access_token"
    
    # Parameters required for the exchange
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_access_token
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        long_lived_access_token = data.get("access_token")
        print(f"data: {data}")
        print(f"Long-lived access token: {long_lived_access_token}")
        return long_lived_access_token
    except requests.RequestException as e:
        return f"An error occurred: {e}"
    
def check_token_expiration(access_token, app_id, app_secret):
    url = f"https://graph.facebook.com/debug_token"
    params = {"input_token": access_token, "access_token": f"{app_id}|{app_secret}"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {})
    except requests.RequestException as e:
        return f"An error occurred: {e}"
    
def get_instagram_username(instagram_business_account_id, access_token):
    try:
        url = f'https://graph.facebook.com/v17.0/{instagram_business_account_id}?fields=username&access_token={access_token}'
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        return data.get('username')
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_linkedin_account_name(access_token):
    url = 'https://api.linkedin.com/v2/me'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        first_name = data.get('localizedFirstName', '')
        last_name = data.get('localizedLastName', '')
        return f"{first_name} {last_name}".strip()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
# --------------------- GET --------------------------- #

# ----------- LINKEDIN -------------- #

def upload_image_from_url_to_linkedin(image_url, access_token, access_id, access_type):
    
    owner_urn = f"urn:li:person:{access_id}" if access_type == 'personal' else f"urn:li:organization:{access_id}"

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
            "owner": owner_urn, 
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


def post_to_linkedin(caption, image_url, access_token, access_id, access_type):
    media_id = upload_image_from_url_to_linkedin(image_url, access_token, access_id, access_type)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-li-format": "json"
    }
    
    author = f"urn:li:person:{access_id}" if access_type == "personal" else f"urn:li:organization:{access_id}"
    
    payload = {
        "author": author,
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
                        "text": caption
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


def post_text_to_linkedin(access_token, user_id, message, access_type):
    url = 'https://api.linkedin.com/v2/ugcPosts'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }

    author = f"urn:li:person:{user_id}" if access_type == "personal" else f"urn:li:organization:{user_id}"

    post_data = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": message
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(url, headers=headers, json=post_data)
    return response.json()

# ----------- GOOGLE MY BUSINESS -------------- #

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

    endpoint = f"https://mybusiness.googleapis.com/v4/accounts/YOUR_ACCOUNT_NAME/locations/YOUR_LOCATION_ID/localPosts"

    response = requests.post(endpoint, headers=headers, json=payload).json()
    return response

# ----------- INSTAGRAM -------------- #
    
def post_to_instagram(access_token, image_url, caption, instagram_user_id):

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

def extract_first_frame(video_url):
    with VideoFileClip(video_url) as clip:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_img:
            clip.save_frame(temp_img.name, t=0)
            return temp_img.name

def post_video_to_instagram(access_token, video_url, caption, instagram_user_id):
    endpoint = f"https://graph.facebook.com/{instagram_user_id}/media"
    payload = {
        "media_type": "VIDEO",
        "video_url": video_url,
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


# ----------- FACEBOOK -------------- #

def post_to_facebook_page_feed(caption, image_url, page_id, page_access_token):
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile() as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.flush()
            temp_file.seek(0)

            photo_endpoint = f"https://graph.facebook.com/v17.0/{page_id}/photos"
            photo_params = {
                "caption": caption,
                "access_token": page_access_token,
            }
            files = {'source': temp_file}

            photo_response = requests.post(photo_endpoint, params=photo_params, files=files).json()
            if 'error' in photo_response:
                error_code = photo_response['error'].get('code')
                error_message = photo_response['error'].get('message', 'Unknown error')
                
                if error_code == 190:
                    raise Exception(f"Access token error: {error_message}")
                else:
                    raise Exception(f"Error posting to Facebook: {error_message}")
            return photo_response
    else:
        error_msg = f"Failed to download the image. Status code: {response.status_code}"
        raise Exception(error_msg)

def post_text_to_facebook_page_feed(caption, page_id, page_access_token):
    post_endpoint = f"https://graph.facebook.com/{page_id}/feed"

    post_params = {
        "message": caption,
        "access_token": page_access_token,
    }

    try:
        post_response = requests.post(post_endpoint, data=post_params).json()

        if post_response.get("error"):
            error = post_response["error"]
            print("Error posting to Facebook:", error)

            if error.get("type") == "OAuthException":
                error_message = "The access token is invalid or expired."
                print(error_message)
                raise Exception(error_message)
                
        else:
            print("Post successful:", post_response)

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")

    return post_response

def post_video_to_facebook_page_feed(caption, video_url, page_id, page_access_token):
    # Step 1: Initialize An Upload Session
    def initialize_upload_session(file_size):
        params = {
            "upload_phase": "start",
            "file_size": file_size,
            "access_token": page_access_token
        }
        init_url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"
        response = requests.post(init_url, params=params).json()
        return response

    # Step 2: Upload Chunks Individually
    def upload_video_chunk(upload_session_id, start_offset, chunk):
        params = {
            "upload_phase": "transfer",
            "start_offset": start_offset,
            "upload_session_id": upload_session_id,
            "access_token": page_access_token
        }
        files = {
            "video_file_chunk": chunk
        }
        chunk_url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"
        response = requests.post(chunk_url, params=params, files=files).json()
        return response

    # Step 3: End The Upload Session
    def end_upload_session(upload_session_id):
        params = {
            "upload_phase": "finish",
            "upload_session_id": upload_session_id,
            "access_token": page_access_token
        }
        finish_url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"
        response = requests.post(finish_url, params=params).json()
        return response

    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        file_size = os.path.getsize(temp_file_path)
        init_response = initialize_upload_session(file_size)

        if "upload_session_id" in init_response:
            upload_session_id = init_response["upload_session_id"]
            start_offset = init_response["start_offset"]
            end_offset = init_response["end_offset"]

            with open(temp_file_path, "rb") as f:
                f.seek(int(start_offset))
                while int(start_offset) < int(end_offset):
                    chunk = f.read(min(8192, int(end_offset) - int(start_offset)))
                    chunk_response = upload_video_chunk(upload_session_id, start_offset, chunk)
                    start_offset = chunk_response["start_offset"]
                    end_offset = chunk_response["end_offset"]

            os.remove(temp_file_path)

            end_response = end_upload_session(upload_session_id)
            if end_response.get("success"):
                print("Video successfully uploaded.")
                return end_response
            else:
                print("Failed to end the upload session.")
                return end_response
        else:
            print("Failed to initialize the upload session.")
            return init_response
    else:
        print("Failed to download the video.")
        return {"error": "Failed to download the video."}


if __name__ == "__main__":
    access_token = "EAADFIOXHRl4BOxYm4ycXdXIPU5pPqqVCNUVUR0Tr7o2jFRDJ7SPoGzkWyuz3d46SZBlWPfvumKUdSiPZBr19dHNTDUvNBhNRl5dBZCYk3qfFfFBRBp4cRUHqrSgifGsqHrKCZBTwttHYZA06J4WPJZArkkWfl4J11TZCL3H0QZCTfh8Qp31ZAFDp3CPYHTzzy5r5g8vGE5220"
    id = '17841431479346652'
    CAPTION = "Testing....."
    IMAGE_URL = "https://storage.googleapis.com/starter_web_app_bucket/testing.png"
    FACEBOOK_APP_ID = '216745084667486'
    FACEBOOK_APP_SECRET = 'd96b709e954bb40082e95bc9fef4281b'
    FACEBOOK_PAGE_ID = 'd96b709e954bb40082e95bc9fef4281b'
    FACEBOOK_APP_SECRET = 'd96b709e954bb40082e95bc9fef4281b'
    print(get_instagram_user_id('108830535605871', access_token))