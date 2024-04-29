# from fastapi import FastAPI, APIRouter,Query
# from starlette.requests import Request
# from starlette.middleware.sessions import SessionMiddleware
# from authlib.integrations.starlette_client import OAuth
# from fastapi.responses import JSONResponse
# from fastapi import HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import requests
# from starlette.responses import StreamingResponse
# import asyncio
# import json
# import aiohttp
# import motor.motor_asyncio
# from bson import json_util
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
#
# app = FastAPI()
# router = APIRouter()
# session = aiohttp.ClientSession()
#
# origins = [
#     "http://localhost:3000",
#     "http://localhost:8000",
#     "http://localhost:8080",
#     "https://www.google.com",
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))
# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
# db = client['DoAn']
# collection = db['chat_history']
#
# oauth = OAuth()
# oauth.register(
#     name='google',
#     server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
#     client_id=CLIENT_ID,
#     client_secret=CLIENT_SECRET,
#     client_kwargs={
#         'scope': 'openid email profile',
#         'response_type': 'code',
#         'redirect_uri': 'http://127.0.0.1:8002/ext/auth/code'
#     }
# )
#
# async def save_chat_history(user_ask: str, assistant_answer: str):
#     document = {"user_ask": user_ask, "assistant_answer": assistant_answer}
#     result = await collection.insert_one(document)
#     return result.inserted_id
#
# @app.get("/ext/chat", response_class=StreamingResponse)
# async def chat(query: str = Query(...)):
#     headers = {
#          'Authorization': os.getenv("GPT_AUTHORIZATION")
#     }
#     data = {
#         'model': 'gpt-3.5-turbo',
#         'messages': [
#             {'role': 'system', 'content': 'You are a helpful assistant.'},
#             {'role': 'user', 'content': query}
#         ]
#     }
#
#     async def event_generator():
#         for attempt in range(2):
#             try:
#                 async with aiohttp.ClientSession() as session:
#                     async with session.post('https://api.openai.com/v1/chat/completions', headers=headers,
#                                             json=data) as response:
#                         if response.status == 200:
#                             openai_response = await response.json()
#
#                             for part in openai_response['choices']:
#                                 text = part['message']['content'] or ""
#                                 botResponse = ""
#
#                                 for char in text:
#                                     botResponse += char
#                                     print(botResponse)
#                                     data_to_send = f"event: response\ndata: {json.dumps({'text': char})}\n\n"
#                                     yield data_to_send
#                                 await save_chat_history(query, botResponse)
#                                 yield "event: done\ndata: {}\n\n"
#                                 return
#                             else:
#                                 error_message = await response.text()
#                                 print(f"OpenAI API request failed with status {response.status}: {error_message}")
#             except aiohttp.ClientError as e:
#                 print(f"Error occurred while making the request: {e}")
#                 await asyncio.sleep(1)
#
#         yield "event: done\ndata: {}\n\n"
#     return StreamingResponse(event_generator(), media_type="text/event-stream")
#
# class JSONEncoder(json.JSONEncoder):
#     def default(self, o):
#         return json_util.default(o)
# @app.get("/ext/chat_history")
# async def get_chat_history():
#     cursor = collection.find({})
#     chat_history = []
#     async for document in cursor:
#         chat_history.append(document)
#     return JSONResponse(status_code=200, content=json.loads(JSONEncoder().encode(chat_history)))
#
# @app.get("/ext/auth/ext_google_login")
# async def login(request: Request):
#     redirect_uri = oauth.google.client_kwargs['redirect_uri']
#     authorization_url = await oauth.google.create_authorization_url(redirect_uri)
#     return {"details": authorization_url, "scope": oauth.google.client_kwargs['scope'], "status": 200}
#
# @app.get("/ext/auth/ext_google_auth")
# async def auth(request: Request):
#     try:
#         code = request.query_params.get('code')
#         if not code:
#             raise HTTPException(status_code=400, detail="Authorization code not found")
#
#         data = {
#             "code": code,
#             "client_id": CLIENT_ID,
#             "client_secret": CLIENT_SECRET,
#             "redirect_uri": "http://127.0.0.1:8002/ext/auth/code",
#             "grant_type": "authorization_code"
#         }
#
#         response = requests.post("https://oauth2.googleapis.com/token", data=data)
#
#         if response.status_code != 200:
#             return JSONResponse(status_code=400, content={"error": "Failed to exchange authorization code for access token"})
#
#         token_response = response.json()
#         access_token = token_response.get('access_token')
#         auth_token = token_response.get('id_token')
#         if not access_token or not auth_token:
#             return JSONResponse(status_code=400, content={"error": "Access token or Auth token not found"})
#
#         user_info_response = requests.get(f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}')
#         user_info = user_info_response.json()
#
#         request.session['user'] = user_info
#
#         return {"access_token": access_token, "auth_token": auth_token, "user": user_info}
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": str(e)})
#
# @app.get("/ext/who_am_i")
# async def welcome(request: Request):
#     user = request.session.get('user')
#     if not user:
#         return JSONResponse(status_code=400, content={"error": "User not found"})
#     return {"details": user}
#
# if __name__ == "__main__":
#     import uvicorn
#     # uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, APIRouter,Query
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from starlette.responses import StreamingResponse
import asyncio
import json
import aiohttp
import motor.motor_asyncio
from bson import json_util
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
router = APIRouter()
session = aiohttp.ClientSession()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "https://www.google.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client['DoAn']
collection = db['chat_history']



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

async def save_chat_history(user_ask: str, assistant_answer: str, user_id: str):
    # Add the user_id to the chat document
    document = {"user_id": user_id, "user_ask": user_ask, "assistant_answer": assistant_answer}
    result = await collection.insert_one(document)
    return result.inserted_id

@app.get("/ext/chat", response_class=StreamingResponse)
async def chat(query: str = Query(...), user_email: str = Query(...)):
    headers = {
         'Authorization': os.getenv("GPT_AUTHORIZATION")
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': query}
        ]
    }

    # Query the users collection to get the user's id
    user = await db['users'].find_one({"email": user_email})
    if not user:
        return "User not found"

    user_id = user['id']

    async def event_generator():
        for attempt in range(2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post('https://api.openai.com/v1/chat/completions', headers=headers,
                                            json=data) as response:
                        if response.status == 200:
                            openai_response = await response.json()

                            for part in openai_response['choices']:
                                text = part['message']['content'] or ""
                                botResponse = ""
                                print(botResponse)
                                for char in text:
                                    botResponse += char
                                    data_to_send = f"event: response\ndata: {json.dumps({'text': char})}\n\n"
                                    yield data_to_send
                                if "Follow-up questions:" not in botResponse:
                                    await save_chat_history(query, botResponse, user_id)
                                yield "event: done\ndata: {}\n\n"
                                return
                            else:
                                error_message = await response.text()
                                print(f"OpenAI API request failed with status {response.status}: {error_message}")
            except aiohttp.ClientError as e:
                print(f"Error occurred while making the request: {e}")
                await asyncio.sleep(1)

        yield "event: done\ndata: {}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        return json_util.default(o)
@app.get("/ext/chat_history")
async def get_chat_history(user_email: str):
    # Query the users collection to get the user's id
    user = await db['users'].find_one({"email": user_email})
    if not user:
        return JSONResponse(status_code=400, content={"error": "User not found"})

    user_id = user['id']

    # Query the chat_history collection using the user's id
    cursor = collection.find({"user_id": user_id})
    chat_history = []
    async for document in cursor:
        chat_history.append(document)
    return JSONResponse(status_code=200, content=json.loads(JSONEncoder().encode(chat_history)))

@app.get("/ext/auth/ext_google_login")
async def login(request: Request):
    redirect_uri = oauth.google.client_kwargs['redirect_uri']
    authorization_url = await oauth.google.create_authorization_url(redirect_uri)
    return {"details": authorization_url, "scope": oauth.google.client_kwargs['scope'], "status": 200}

@app.get("/ext/auth/ext_google_auth")
async def auth(request: Request):
    print(CLIENT_ID)
    print(CLIENT_SECRET)
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
            return JSONResponse(status_code=400, content={"error": "Failed to exchange authorization code for access token"})

        token_response = response.json()
        access_token = token_response.get('access_token')
        auth_token = token_response.get('id_token')
        if not access_token or not auth_token:
            return JSONResponse(status_code=400, content={"error": "Access token or Auth token not found"})

        user_info_response = requests.get(f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}')
        user_info = user_info_response.json()

        # Save user info to MongoDB
        users_collection = db['users']
        user_document = {"id": user_info["id"], "email": user_info["email"]}
        await users_collection.insert_one(user_document)

        request.session['user'] = user_info

        return {"access_token": access_token, "auth_token": auth_token, "user": user_info}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/ext/who_am_i")
async def welcome(request: Request):
    user = request.session.get('user')
    if not user:
        return JSONResponse(status_code=400, content={"error": "User not found"})
    return {"details": user}

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)