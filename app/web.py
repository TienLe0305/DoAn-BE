from fastapi import APIRouter
from models import URLRequest
import requests
from bs4 import BeautifulSoup
from rag import process_text, reset_memory

router = APIRouter()

@router.post("/ext/extract_from_url")
async def extract_from_url(request: URLRequest):
    url = request.url
    print(url)
    try:
        response = requests.get(url)
        html_content = response.content

        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()

        reset_memory()
        process_text(text)

        return {"message": "Content extracted successfully from URL"}
    except Exception as e:
        return {"error": str(e)}