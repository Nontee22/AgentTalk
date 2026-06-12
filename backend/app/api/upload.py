import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.config import PROJECT_ROOT
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["upload"])

UPLOAD_DIR = PROJECT_ROOT / "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    category: str = Query("covers", pattern="^(covers|avatars)$"),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB")

    save_dir = UPLOAD_DIR / category
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.{ext}"
    save_path = save_dir / filename
    save_path.write_bytes(content)

    relative_path = f"{category}/{filename}"
    return {"path": relative_path}
