from fastapi import APIRouter, Query, HTTPException
from openai import OpenAI
from config import OPENAI_API_KEY
from database import get_db
from utils import save_chat_history, keep_recent_context
import json
from models import JSONEncoder
from fastapi.responses import JSONResponse, StreamingResponse
from rag import search_chunks

router = APIRouter()
conversation_context = []

@router.get("/ext/chat", response_class=StreamingResponse)
async def chat(query: str = Query(...), user_email: str = Query(...), file_name: str = None, prompt: str = None):
    client = OpenAI(
        api_key=OPENAI_API_KEY,
    )

    db = await get_db()
    user = await db['users'].find_one({"email": user_email})
    if not user:
        return "User not found"

    user_id = user['id']

    async def event_generator():
        try:
            relevant_chunks = search_chunks(query)
            context = "\n".join(relevant_chunks)

            recent_context = keep_recent_context(conversation_context, 5)

            system_prompt = "You are a helpful assistant created by TienLV, and your name is Nebula. You are designed to assist users with various tasks and provide information based on the given context. Please respond in a clear, concise, and informative manner."
            if prompt:
                system_prompt += prompt

            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=recent_context + [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"{query}\n\nContext:\n{context}"
                    }
                ],
                temperature= 0.8,
                stream=True,
            )
            botResponse = ""
            for chunk in stream:
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

            if file_name:
                await save_chat_history(f"<file>{file_name}</file>", botResponse_text, user_id, file_name)
            elif prompt:
                await save_chat_history(prompt, botResponse_text, user_id)
            else:
                await save_chat_history(query_text, botResponse_text, user_id)

            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            print("OpenAI Response (Streaming) Error: " + str(e))
            raise HTTPException(503, "OpenAI server is busy, try again later")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/ext/chat_history")
async def get_chat_history(user_email: str):
    db = await get_db()
    user = await db['users'].find_one({"email": user_email})
    if not user:
        return JSONResponse(status_code=400, content={"error": "User not found"})

        user_id = user['id']

        cursor = collection.find({"user_id": user_id})
        chat_history = []
        async for document in cursor:
            chat_history.append(document)
        return JSONResponse(status_code=200, content=json.loads(JSONEncoder().encode(chat_history)))