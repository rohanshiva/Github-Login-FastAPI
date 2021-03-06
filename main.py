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
    return RedirectResponse(github_oauth_handler.login())


@app.get("/authenticate/github")
def github_authenticate(code:str):
    try:
        access_token = github_oauth_handler.get_access_token(code)

        user = github_oauth_handler.get_user_details(access_token)

        return users_db.put(user)
    except:
        raise HTTPException(status_code=401, detail='Failed to add user to users_db')
