from fastapi import UploadFile, File, HTTPException
from pathlib import Path
import shutil
import os

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


async def upload_file(file: UploadFile = File(...)):
    """
    Handle file upload and save to disk
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Create file path
        file_path = UPLOAD_DIR / file.filename

        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file_path.stat().st_size,
            "message": "File uploaded successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
