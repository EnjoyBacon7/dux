from fastapi import APIRouter, UploadFile, File
from server.methods.upload import upload_file

router = APIRouter()

"""
Healthcheck endpoint to verify that the application is running.
"""
@router.get("/healthcheck")
def read_root():
    return "OK"

"""
Upload endpoint to handle CVs and files"""
@router.post("/upload")
async def upload_endpoint(file: UploadFile = File(...)):
    result = await upload_file(file)
    return result