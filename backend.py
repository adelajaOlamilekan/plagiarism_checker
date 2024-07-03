from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from typing import List

import main

app = FastAPI()

origins = [
    "http://localhost:4006",
    "https://mol12.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KGRAM = 5

@app.get("/")
def home():
    return {"message": "Plagiarism Checker"}

@app.post("/uploadfile/")
async def create_upload_file(files: List[UploadFile] = File(...)):

    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload two files")
    
    try:
        result =  await main.check_plagiarism(files, KGRAM)

        return JSONResponse (content={"result" : result }, status_code=200)
    
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=9001)