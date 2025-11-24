from fastapi import APIRouter, UploadFile, File
from server.methods.upload import upload_file

router = APIRouter(tags=["General"])


@router.get("/healthcheck", summary="Health check")
def read_root():
    """
    Healthcheck endpoint to verify that the application is running.

    Returns:
        str: "OK" if the service is running
    """
    return "OK"


@router.post("/upload", summary="Upload file")
async def upload_endpoint(file: UploadFile = File(...)):
    """
    Upload endpoint to handle file uploads.

    Args:
        file: The file to upload (multipart/form-data)

    Returns:
        dict: Upload result containing filename, content_type, size, and message
    """
    result = await upload_file(file)
    return result
