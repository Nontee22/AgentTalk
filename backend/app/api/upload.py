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

# Magic bytes for image type validation
_MAGIC_BYTES = {
    b"\xff\xd8\xff": {"jpg", "jpeg"},
    b"\x89PNG\r\n\x1a\n": {"png"},
    b"GIF87a": {"gif"},
    b"GIF89a": {"gif"},
    b"RIFF": {"webp"},  # WebP starts with RIFF....WEBP
}


def _validate_image_content(content: bytes, ext: str) -> bool:
    """Check if file content matches its claimed extension via magic bytes."""
    for magic, exts in _MAGIC_BYTES.items():
        if content[:len(magic)] == magic:
            if ext in exts:
                return True
            # WebP needs additional check: RIFF....WEBP
            if ext == "webp" and content[8:12] == b"WEBP":
                return True
    return False


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

    if not _validate_image_content(content, ext):
        raise HTTPException(
            status_code=400,
            detail="文件内容与扩展名不匹配，请上传真实的图片文件",
        )

    save_dir = UPLOAD_DIR / category
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.{ext}"
    save_path = save_dir / filename
    save_path.write_bytes(content)

    relative_path = f"{category}/{filename}"
    return {"path": relative_path}
