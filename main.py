from fastapi import FastAPI, File, UploadFile, Form

from casparser import read_cas_pdf


app = FastAPI()

@app.post("/upload_cas/")
async def process_file(file: UploadFile = File(...), password: str = Form(...)):
    
    result = read_cas_pdf(file, password)
    return {"result": result}
