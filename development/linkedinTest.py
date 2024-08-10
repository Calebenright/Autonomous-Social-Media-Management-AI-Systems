import requests

LINKEDIN_CLIENT_ID = '86shcoarzrxc8l'
LINKEDIN_CLIENT_SECRET = 'g1V78YkSdDGmqMfA'
LINKEDIN_DEV_REDIRECT_URI = 'http://127.0.0.1:8000/callback/'
LINKEDIN_REDIRECT_URI = 'http://feadl.io/callback/'
SCOPES = 'r_organization_social w_organization_social'

# Step 1: Generate LinkedIn Authorization URL
def generate_auth_url():
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={LINKEDIN_CLIENT_ID}&redirect_uri={LINKEDIN_DEV_REDIRECT_URI}&scope={SCOPES.replace(' ', '%20')}"
    return auth_url

# Step 2: Exchange Code for Access Token
def get_access_token(code):
    token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'client_id': LINKEDIN_CLIENT_ID,
        'client_secret': LINKEDIN_CLIENT_SECRET
    }
    response = requests.post(token_url, data=token_data)
    return response.json().get('access_token')

# Step 3: Fetch User and Business Page Information
def get_user_info(access_token):
    user_info_url = 'https://api.linkedin.com/v2/me'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(user_info_url, headers=headers)
    return response.json()

def get_business_pages(access_token):
    pages_url = 'https://api.linkedin.com/v2/organizations'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(pages_url, headers=headers)
    return response.json()

# Main Execution
if __name__ == '__main__':
    auth_url = generate_auth_url()
    print("Please go to the following URL and authorize the app:")
    print(auth_url)

    code = input("Enter the authorization code: ")
    access_token = get_access_token(code)

    user_info = get_user_info(access_token)
    business_pages = get_business_pages(access_token)

    print(f"User Info: {user_info}")
    print(f"Business Pages: {business_pages}")
