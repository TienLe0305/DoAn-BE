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

from openai import OpenAI
import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

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

async def save_chat_history(user_ask: str, assistant_answer: str, user_id: str, pdf_name: str = None):
    if pdf_name:
        document = {"user_id": user_id, "user_ask": f"<pdf>{pdf_name}</pdf>", "assistant_answer": assistant_answer}
    else:
        document = {"user_id": user_id, "user_ask": user_ask, "assistant_answer": assistant_answer}
    result = await collection.insert_one(document)
    return result.inserted_id


conversation_context = []
model = None
index = None
chunks = []

@app.post("/ext/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    global model, index, chunks
    try:
        pdf_contents = await file.read()
        model = SentenceTransformer('all-MiniLM-L6-v2')

        with fitz.open(stream=pdf_contents, filetype="pdf") as pdf_file:
            text = ""
            for page in pdf_file:
                text += page.get_text()

        # Split the text into chunks
        chunks = [text[i:i + 500] for i in range(0, len(text), 500)]  # Adjust chunk size as needed

        # Encode the chunks into vectors
        vectors1 = model.encode(chunks)

        # Create a FAISS index and add the vectors
        index = faiss.IndexFlatL2(model.get_sentence_embedding_dimension())
        index.add(np.array(vectors1).astype('float32'))

        return {"pdf_text": "PDF uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/ext/chat", response_class=StreamingResponse)
async def chat(query: str = Query(...), user_email: str = Query(...), pdf_name: str = None, prompt: str = None):
    global model, index, chunks
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    user = await db['users'].find_one({"email": user_email})
    if not user:
        return "User not found"

    user_id = user['id']

    def search_chunks(query):
        if model is not None and index is not None and chunks:
            query_vector = model.encode([query])
            scores, indices = index.search(np.array(query_vector).astype('float32'), 5)
            relevant_chunks = [chunks[i] for i in indices[0]]
            return relevant_chunks
        return []

    async def event_generator():
        try:
            relevant_chunks = search_chunks(query)
            context = "\n".join(relevant_chunks)

            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation_context + [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant created by TienLV and your name is nebula." + (prompt if prompt else "")
                    },
                    {
                        "role": "user",
                        "content": f"{query}\n\nContext:\n{context}"
                    }
                ],
                temperature=0.8,
                stream=True,
            )
            botResponse = ""
            for chunk in stream:
                print(chunk.choices[0].delta.content or "", end="")
                botResponse += chunk.choices[0].delta.content or ""
                data_to_send = f"event: response\ndata: {json.dumps({'text': chunk.choices[0].delta.content or ''})}\n\n"
                yield data_to_send
            query_text = query.split("- Finally")[0]
            botResponse_text = botResponse.split("Follow-up questions:")[0]

            if not botResponse_text.strip():
                botResponse_text = "How can I help you today?"

            if prompt:
                conversation_context.append({"role": "user", "content": prompt})
                conversation_context.append({"role": "system", "content": botResponse_text})

            conversation_context.append({"role": "user", "content": query_text})
            conversation_context.append({"role": "system", "content": botResponse_text})

            # if "Follow-up questions:" not in botResponse:
            if pdf_name:
                await save_chat_history(f"{ pdf_name}", botResponse_text, user_id, pdf_name)
            elif prompt:
                await save_chat_history(prompt, botResponse_text, user_id)
            else:
                await save_chat_history(query_text, botResponse_text, user_id)

            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            print("OpenAI Response (Streaming) Error: " + str(e))
            raise HTTPException(503, "OpenAI server is busy, try again later")

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
            return JSONResponse(status_code=400,
                                content={"error": "Failed to exchange authorization code for access token"})

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
