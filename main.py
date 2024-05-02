import asyncio
import json
import os

import aiohttp
import fitz
import motor.motor_asyncio
import requests
from authlib.integrations.starlette_client import OAuth
from bson import json_util
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

load_dotenv()

app = FastAPI()
router = APIRouter()
session = aiohttp.ClientSession()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

conversation_context = [
    {"role": "system", "content": "You are a helpful assistant."}
]

async def save_chat_history(user_ask: str, assistant_answer: str, user_id: str, pdf_name: str = None):
    if pdf_name:
        document = {"user_id": user_id, "user_ask": f"<pdf>{pdf_name}</pdf>", "assistant_answer": assistant_answer}
    else:
        document = {"user_id": user_id, "user_ask": user_ask, "assistant_answer": assistant_answer}
    result = await collection.insert_one(document)
    return result.inserted_id

@app.post("/ext/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        pdf_contents = await file.read()

        with fitz.open(stream=pdf_contents, filetype="pdf") as pdf_file:
            text = ""
            for page in pdf_file:
                text += page.get_text()

        return {"pdf_text": text}
    except Exception as e:
        return {"error": str(e)}

@app.get("/ext/chat", response_class=StreamingResponse)
async def chat(query: str = Query(...), user_email: str = Query(...), pdf_name: str = None):
    headers = {
         'Authorization': os.getenv("GPT_AUTHORIZATION")
    }

    if pdf_name:
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': conversation_context + [{'role': 'user', 'content': f"<pdf>{pdf_name}</pdf>"}],
        }
    else:
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': conversation_context + [{'role': 'user', 'content': query}],
        }

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

                                for char in text:
                                    botResponse += char
                                    data_to_send = f"event: response\ndata: {json.dumps({'text': char})}\n\n"
                                    yield data_to_send

                                conversation_context.append({"role": "user", "content": query})
                                conversation_context.append({"role": "assistant", "content": botResponse})

                                if "Follow-up questions:" not in botResponse:
                                    if pdf_name:
                                        await save_chat_history(f"<pdf>{pdf_name}</pdf>", botResponse, user_id,
                                                                pdf_name)
                                    else:
                                        await save_chat_history(query, botResponse, user_id)

                                yield "event: done\ndata: {}\n\n"
                                return
                            else:
                                error_message = await response.text()
            except aiohttp.ClientError as e:
                await asyncio.sleep(1)

        yield "event: done\ndata: {}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        return json_util.default(o)

@app.get("/ext/chat_history")
async def get_chat_history(user_email: str):
    user = await db['users'].find_one({"email": user_email})
    if not user:
        return JSONResponse(status_code=400, content={"error": "User not found"})

    user_id = user['id']

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