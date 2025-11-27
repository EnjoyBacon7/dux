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
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file extension (security check)
    allowed_extensions = {".pdf", ".doc", ".docx", ".txt"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Create safe filename to prevent directory traversal
    safe_filename = Path(file.filename).name
    file_path = UPLOAD_DIR / safe_filename

    try:
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": safe_filename,
            "content_type": file.content_type,
            "size": file_path.stat().st_size,
            "message": "File uploaded successfully"
        }

    except Exception as e:
        # Clean up partial file if upload fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
