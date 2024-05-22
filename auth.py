from fastapi import APIRouter, Request, HTTPException, responses
import requests
from config import CLIENT_ID, CLIENT_SECRET
from database import get_db
from authlib.integrations.starlette_client import OAuth

router = APIRouter()
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

@router.get("/ext/auth/ext_google_login")
async def login(request: Request):
    redirect_uri = oauth.google.client_kwargs['redirect_uri']
    authorization_url = await oauth.google.create_authorization_url(redirect_uri)
    return {"details": authorization_url, "scope": oauth.google.client_kwargs['scope'], "status": 200}

@router.get("/ext/auth/ext_google_auth")
async def auth(request: Request):
    try:
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")

        data = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": "http://127.0.0.1:8002/ext/auth/code",
            "grant_type": "authorization_code"
        }

        response = requests.post("https://oauth2.googleapis.com/token", data=data)

        if response.status_code != 200:
            return responses.JSONResponse(status_code=400,
                                content={"error": "Failed to exchange authorization code for access token"})

        token_response = response.json()
        access_token = token_response.get('access_token')
        auth_token = token_response.get('id_token')
        if not access_token or not auth_token:
            return responses.JSONResponse(status_code=400, content={"error": "Access token or Auth token not found"})

        user_info_response = requests.get(f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}')
        user_info = user_info_response.json()

        db = await get_db()
        users_collection = db['users']
        existing_user = await users_collection.find_one({"id": user_info["id"]})
        if existing_user:
            await users_collection.update_one({"id": user_info["id"]}, {"$set": {"email": user_info["email"]}})
        else:
            user_document = {
                "id": user_info["id"],
                "email": user_info["email"]
            }
            await users_collection.insert_one(user_document)

        request.session['user'] = user_info

        return {"access_token": access_token, "auth_token": auth_token, "user": user_info}
    except Exception as e:
        return responses.JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/ext/who_am_i")
async def welcome(request: Request):
    user = request.session.get('user')
    if not user:
        return responses.JSONResponse(status_code=400, content={"error": "User not found"})
    return {"details": user}