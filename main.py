from fastapi import FastAPI, Query
from starlette.requests import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests


app = FastAPI()

origins = [
    "http://localhost:3000",  # React
    "http://localhost:8000",  # Angular
    "http://localhost:8080",  # Vue.js
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=" secret")
CLIENT_ID = "1080662676746-s5ps31peevt9jns27u8r92l106phn80a.apps.googleusercontent.com"
CLIENT_SECRET = "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"

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid email profile',
        'response_type': 'code',
        'redirect_uri': 'http://127.0.0.1:8002/ext/auth/code'
    }
)

@app.get("/ext/auth/ext_google_login")
async def login(request: Request):
    redirect_uri = oauth.google.client_kwargs['redirect_uri']
    authorization_url = await oauth.google.create_authorization_url(redirect_uri)
    return {"details": authorization_url, "scope": oauth.google.client_kwargs['scope'], "status": 200}

@app.get("/ext/auth/ext_google_auth")
async def auth(request: Request):
    try:
        # Get the authorization code from the redirect URL
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")

        # Prepare the data for the token request
        data = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": "http://127.0.0.1:8002/ext/auth/code",
            "grant_type": "authorization_code"
        }

        # Send a POST request to the Google token endpoint
        response = requests.post("https://oauth2.googleapis.com/token", data=data)

        # Check the response
        if response.status_code != 200:
            return JSONResponse(status_code=400, content={"error": "Failed to exchange authorization code for access token"})

        # Parse the access token and auth token from the response
        token_response = response.json()
        access_token = token_response.get('access_token')
        auth_token = token_response.get('id_token')
        if not access_token or not auth_token:
            return JSONResponse(status_code=400, content={"error": "Access token or Auth token not found"})

        # Get user info from the id_token
        user_info_response = requests.get(f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}')
        user_info = user_info_response.json()

        # Store user info in session
        request.session['user'] = user_info

        return {"access_token": access_token, "auth_token": auth_token, "user": user_info}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def hello_world():
    return 'Hello World!'


@app.get("/ext/who_am_i")
async def welcome(request: Request):
    user = request.session.get('user')
    if not user:
        return JSONResponse(status_code=400, content={"error": "User not found"})
    return {"details": user}

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)