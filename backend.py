from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List


import main
import os 
import fitz
from docx import Document
from io import BytesIO
app = FastAPI()

KGRAM = 5

async def read_pdf_from_memory(file: BytesIO):
    text = ""
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

def read_docx_from_memory(file:BytesIO):
    document = Document(file)
    text = []
    for paragraph in document.paragraphs:
        text.append(paragraph.text)
    return "\n".join(text)


@app.get("/")
def home():
    return {"message": "Plagiarism Checker"}

@app.post("/uploadfile/")
async def create_upload_file(files: List[UploadFile] = File(...)):

    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload two files")

    file_contents = {}

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()

        if ext == ".pdf":
            file_content_in_binary = await file.read()
            content = await read_pdf_from_memory(BytesIO(file_content_in_binary))
        elif ext in [".doc", ".docx"]:
            file_content_in_binary = await file.read()
            content = read_docx_from_memory(BytesIO(file_content_in_binary))
        
        file_contents[file.filename] = content

    return file_contents
    
    try:
        return JSONResponse (content={"result" : main.check_plagiarism(filenames, KGRAM)} , status_code=200)
    
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=9000)