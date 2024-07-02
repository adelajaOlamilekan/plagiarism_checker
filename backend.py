from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List

import main

app = FastAPI()

KGRAM = 5

@app.get("/")
def home():
    return {"message": "Plagiarism Checker"}

@app.post("/uploadfile/")
async def create_upload_file(files: List[UploadFile] = File(...)):

    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload two files")

    filenames = [file.filename for file in files]

    return {"filenames": filenames}
    
    try:
        return JSONResponse (content={"result" : main.check_plagiarism(filenames, KGRAM)} , status_code=200)
    
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)