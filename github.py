from urllib.parse import urlencode
import requests
from fastapi import HTTPException
import os

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "https://7zdvec.deta.dev/authenticate/github"
GITHUB_LOGIN_URL = 'https://github.com/login/oauth/authorize?'
ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token?'


class GithubOauth():
    
    def login(self):
        params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI, 'scope': 'read:user', 'allow_signup': 'true'}
        params = urlencode(params)
        return GITHUB_LOGIN_URL + params
    
    def get_access_token(self, code):
        try:
            params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI, 'client_secret': CLIENT_SECRET, 'code': code}
            headers = {"Accept": "application/json"}
            r = requests.post(ACCESS_TOKEN_URL, headers = headers, params=params)
            access_token = r.json()['access_token']
            return access_token
        except:
            raise HTTPException(status_code=401, detail="Error while trying to retrieve user access token")

    def get_user_details(self, access_token):
        try:
            r = requests.get('https://api.github.com/user', headers={'Authorization': 'token ' + access_token})
            key = str(r.json()['id'])
            email = r.json()['email']
            username = r.json()['login']
            avatar_url = r.json()['avatar_url']
            return {'key':key, 'email': email, 'username': username, 'avatar_url': avatar_url}
        except:
            raise HTTPException(status_code=401, detail="Failed to fetch user details")
