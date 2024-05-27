from fastapi import APIRouter
from chat import chat, get_chat_history
from image import upload_image
from pdf import upload_file
from web import extract_from_url
from auth import login, auth, welcome

router = APIRouter()

router.get("/ext/chat")(chat)
router.get("/ext/chat_history")(get_chat_history)
router.get("/ext/auth/ext_google_login")(login)
router.get("/ext/auth/ext_google_auth")(auth)
router.get("/ext/who_am_i")(welcome)
router.post("/ext/upload_file")(upload_file)
router.post("/ext/upload_image")(upload_image)
router.post("/ext/extract_from_url")(extract_from_url)