# Github-Login-FastAPI

So you want to add GitHub login to your FastAPI applications? Let's do it!

GitHub Login essentially allows users to login using their GitHub account. Using the GitHub API we can access information such as username, email, profile picture, and user id. Compared to building a traditional login system with an email and password, using external login providers like GitHub makes it it easier for people building the apps as there is a lot less work, plus it makes it simpler for the users. In this article, we are going to use GitHub's OAuth provider to build a simple login system in a FastAPI application. We will also use Deta Base as our database to store user's information such as username, email, user id, and profile pic. 

## Agenda

- Setup
- GitHub OAuth Logic
- Implement the auth logic in a FastAPI app
- Deploy app to Deta Micros

## Setup
Here is a picture that sumarizes the general flow of our application.

![Flow](https://user-images.githubusercontent.com/20916697/115037395-0881ba00-9e94-11eb-987a-67d64644e7f7.png)

To get started, we need to first register our app on GitHub to access their API.

- Head over to this link, and login with your GitHub account.
- Click on the `New OAuth app` button on the top right.

![image](https://user-images.githubusercontent.com/20916697/115032368-d7eb5180-9e8e-11eb-8ca4-23b8fe57e097.png)

![image](https://user-images.githubusercontent.com/20916697/115032493-fd785b00-9e8e-11eb-9fb9-ac35e5e6d7f7.png)
- Name the application (I named it Login FastAPI + Deta Blog).

- For the application URL, I added `http://127.0.0.1:8000`, because that's where my FastAPI applications run locally. 
- Now for the callback URL, let's add `http://127.0.0.1:8000/authenticate/github`, this is important as GitHub routes the user back to this URL after they login. We need to implement this route in our FastAPI application

After you register the app, you will be redirected to the following screen, make sure to copy the `CLIENT_ID` and `CLIENT_SECRET`, and don't forget to save it somewhere safe! 
![image](https://user-images.githubusercontent.com/20916697/115034322-fe11f100-9e90-11eb-918a-a1a905b538b3.png)

We have everything we need from GitHub, and we also need to get a Deta project key to use with Deta Base. We are using Base to store user information such as username, email, avatar url, and user id. 

To do that, navigate to the [Deta Console ](https://web.deta.sh/)then click on the arrow on the top left.
If you don't already have a Deta account, [create one for free](https://web.deta.sh/). Once you confirm your email, Deta will automatically generate a Project Key, this is the one we need, copy it and  store it securely.

![](https://user-images.githubusercontent.com/20916697/114434048-2dbab380-9b88-11eb-8839-22bebae709ed.png)

Create a new project and make sure to save the key in a secure place!

![image](https://user-images.githubusercontent.com/20916697/114434122-40cd8380-9b88-11eb-8ddc-7045ce5756ba.png)

Add the following keys to your environment variables:
```
DETA_PROJECT_KEY="YOUR_COPIED_PROJECT_KEY"
CLIENT_ID="YOUR_COPIED_CLIENT_ID"
CLIENT_SECRET="YOUR_COPIED_CLIENT_SECRET"
```

Before we begin, we need to set up our environment by installing the libraries. 

Create a folder for this project `github-login-fastapi`, and add a `requirements.txt` file with the following lines.
```python
fastapi
deta
uvicorn
requests
```
Run the following command to install the libraries 

`pip install -r requirements.txt`


Here is how our folder structure will look like at the end:

```json

github-login-fastapi/
    ├── main.py
    ├── github.py
    └── requirements.txt
```

That is everything we need for this project. -phew! Let's get started!

## GitHub OAuth Logic

In `github.py`, add import all the tools and get all the environment variables.

```python
from urllib.parse import urlencode
import requests
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
import os

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/authenticate/github"
GITHUB_LOGIN_URL = 'https://github.com/login/oauth/authorize?'
ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token?'
```

Let's create a class to handle all the GitHub OAuth logic.

```python
class GithubOauth():
    
    def login(self):
        params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI, 'scope': 'user', 'allow_signup': 'true'}
        params = urlencode(params)
        return RedirectResponse(GITHUB_LOGIN_URL + params)
```

The `login` function simply builds the URL using the parameters, and redirects the user to the GitHub Login Page. [You can learn more about this here.](https://docs.github.com/en/developers/apps/authorizing-oauth-apps#1-request-a-users-github-identity)
We can use this function when the user clicks login. 


Once the user logins, they are redirected to our application with a special code. We can use this code to get an `access_token` to retrieve user information.

```python
    def get_access_token(self, code):
        try:
            params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI, 'client_secret': CLIENT_SECRET, 'code': code}
            headers = {"Accept": "application/json"}
            r = requests.post(ACCESS_TOKEN_URL, headers = headers, params=params)
            access_token = r.json()['access_token']
            return access_token
        except:
            raise HTTPException(status_code=401, detail="Error while trying to retrieve user access token")
```

`get_access_token` function takes in the code as an argument and makes a `POST` request to the `ACCESS_TOKEN_URL` endpoint with our environment variables. The request response contains the `access_token` for the user. If there is an error during this process, we can simply return an `HTTPException`. 

We can use the `access_token` to retrieve user information. 

```python
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
```

In this function, we are again making a `GET` request to the GitHub API. The request response contains a lot of information about the user, but we are only interested in id, email, username, and avatar url.
If there is an error while making the request, we return another `HTTPException`.

Here is what the file `github.py` looks like at the end:

```python
from urllib.parse import urlencode
import requests
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
import os

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/authenticate/github"
GITHUB_LOGIN_URL = 'https://github.com/login/oauth/authorize?'
ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token?'


class GithubOauth():
    
    def login(self):
        params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI, 'scope': 'user', 'allow_signup': 'true'}
        params = urlencode(params)
        return RedirectResponse(GITHUB_LOGIN_URL + params)
    
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
```

Now that we have our GitHub OAuth logic, we can implement this in our FastAPI application.

## Implement the auth logic in a FastAPI app

To get started, in `main.py` set up the FastAPI application and Deta Base.

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from deta import Deta
from github import GithubOauth

app = FastAPI()

deta = Deta()
users_db = deta.Base('users')

github_oauth_handler = GithubOauth()
```

We also created `github_oauth_handler` using the `GithubOauth` class to access all the logic. Make sure that you set `DETA_PROJECT_KEY` in your environment variables.

When a user clicks login on the frontend, we can simply route them to `/github/login`

```python
@app.get("/github/login")
def github_login():
    return github_oauth_handler.login()
```

As you can see we are not doing much here, we are simply using the `login` function from `github_oauth_handler`, which redirects the user to the GitHub login page. 

We also need another endpoint to where the user will be redirected after logging in `/authenticate/github`

As we learned earlier GitHub redirects the user to the application with a special code. We can use this special code to get an `access_token` for the user, and we can use the `access_token` to get user information.

```python
@app.get("/authenticate/github")
def github_authenticate(code:str):
    try:
        access_token = github_oauth_handler.get_access_token(code)

        user = github_oauth_handler.get_user_details(access_token)

        return users_db.put(user)
    except:
        raise HTTPException(status_code=401, detail='Failed to add user to users_db')
```
        

After we get the user information, we are storing it in our `users_db` Deta Base. If there is an error, we can just return another `HTTPException`

We are done! We now have a dead simple app that implements GitHub Login.

Here is a look at `main.py` at the end:

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from deta import Deta
from github import GithubOauth

app = FastAPI()

deta = Deta()
users_db = deta.Base('users')

github_oauth_handler = GithubOauth()

@app.get("/github/login")
def github_login():
    return github_oauth_handler.login()


@app.get("/authenticate/github")
def github_authenticate(code:str):
    try:
        access_token = github_oauth_handler.get_access_token(code)

        user = github_oauth_handler.get_user_details(access_token)

        return users_db.put(user)
    except:
        raise HTTPException(status_code=401, detail='Failed to add user to users_db')
```

![3099af58-cf5d-4b48-8176-adf625e2e0e5](https://user-images.githubusercontent.com/20916697/115048483-3a4c4e00-9e9f-11eb-8df2-44ff944cf814.gif)

## Deploy on Deta micros
[Install the Deta CLI](https://docs.deta.sh/docs/cli/install), and run the following commands in the same directory to deploy our app on Deta micros. 


```python
deta login
```

```python
deta new 
```

Thank you for reading! If you liked this article, [check out the other one which implements JWT Auth in a FastAPI application.](https://dev.to/deta/deta-fastapi-jwt-auth-part-1-4c82) 
