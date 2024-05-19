from fastapi import APIRouter, File, UploadFile
import fitz
from rag import process_text

router = APIRouter()

@router.post("/ext/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        pdf_contents = await file.read()

        with fitz.open(stream=pdf_contents, filetype="pdf") as pdf_file:
            text = ""
            for page in pdf_file:
                text += page.get_text()

        process_text(text)

        return {"pdf_text": "PDF uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}