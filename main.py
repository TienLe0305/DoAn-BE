from fastapi import FastAPI
from config import SESSION_SECRET, MONGODB_URI
from routes import router
from database import connect_db
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.include_router(router)

app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

@app.on_event("startup")
async def startup_event():
   await connect_db(MONGODB_URI)

if __name__ == "__main__":
   pass
   # uvicorn.run(app, host="0.0.0.0", port=8000)