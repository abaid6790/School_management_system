"""
Two layers of validation, because a filename extension is just a label the
client chose and proves nothing on its own:
  1. Extension must be in the caller's allowed set.
  2. The file's actual bytes must match that type — a PDF must start with the
     %PDF magic number; an image must be openable/verifiable by Pillow. A file
     renamed from .exe to .pdf fails at this layer even though it passes #1.

Saved filenames are always a fresh random uuid4 — the client's original name
is preserved separately (in original_filename) for display/download, but is
never used to build a path on disk, so there's no path-traversal or
filename-collision surface from user input.
"""
import os
import uuid

try:
    from PIL import Image
except ImportError:  # Pillow not installed — extension check still applies, deep check just skipped
    Image = None

from flask import current_app


class UploadError(ValueError):
    pass


def _validate_content(file_storage, ext: str) -> None:
    file_storage.stream.seek(0)
    if ext == "pdf":
        header = file_storage.stream.read(5)
        file_storage.stream.seek(0)
        if not header.startswith(b"%PDF-"):
            raise UploadError("That file doesn't look like a valid PDF.")
    elif ext in ("jpg", "jpeg", "png"):
        if Image is None:
            return
        try:
            Image.open(file_storage.stream).verify()
        except Exception:
            raise UploadError("That file doesn't look like a valid image.")
        finally:
            file_storage.stream.seek(0)


def save_upload(file_storage, subfolder: str, allowed_extensions: set) -> tuple[str, str]:
    """Validates and saves an uploaded file under UPLOAD_FOLDER/<subfolder>/.
    Returns (relative_path, original_filename). Raises UploadError on any
    validation failure — callers should catch this and flash it, not let it
    propagate as a 500."""
    if not file_storage or not file_storage.filename:
        raise UploadError("No file was selected.")

    original_filename = file_storage.filename
    if "." not in original_filename:
        raise UploadError("File has no extension.")

    ext = original_filename.rsplit(".", 1)[1].lower()
    if ext not in allowed_extensions:
        raise UploadError(f"File type not allowed. Allowed types: {', '.join(sorted(allowed_extensions))}.")

    _validate_content(file_storage, ext)

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    target_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(target_dir, exist_ok=True)
    file_storage.save(os.path.join(target_dir, safe_name))

    relative_path = os.path.join(subfolder, safe_name).replace(os.sep, "/")
    return relative_path, original_filename
