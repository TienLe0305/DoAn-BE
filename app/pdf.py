from fastapi import APIRouter, File, UploadFile
import fitz
from rag import process_text, reset_memory
from docx import Document
import tempfile

router = APIRouter()

@router.post("/ext/upload_file")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_contents = await file.read()
        file_extension = file.filename.split(".")[-1]
        print(file_extension)
        print(file_extension.lower())

        if file_extension.lower() == "pdf":
            with fitz.open(stream=file_contents, filetype="pdf") as pdf_file:
                print(f"Number of pages: {len(pdf_file)}")
                if pdf_file.page_count > 0:
                    first_page = pdf_file.load_page(0)
                    print(f"First page text: {first_page.get_text()}")
                text = ""
                for page in pdf_file:
                    text += page.get_text()
            print(text)
        elif file_extension.lower() == "docx":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp:
                temp.write(file_contents)
            document = Document(temp.name)
            print(document)
            text = "\n".join([para.text for para in document.paragraphs])
        else:
            return {"error": "Unsupported file format"}

        reset_memory()
        process_text(text)
        return {"File uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}