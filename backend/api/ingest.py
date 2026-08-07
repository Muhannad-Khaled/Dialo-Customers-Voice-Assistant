from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from rag.ingest import ingest_document
import tempfile, os, structlog

router = APIRouter()
logger = structlog.get_logger()

ALLOWED_EXTS = {".txt", ".pdf", ".md", ".docx"}


@router.post("/ingest")
async def ingest(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    background_tasks.add_task(_ingest_and_cleanup, tmp_path, file.filename)
    return {"message": f"Ingestion started for '{file.filename}'"}


async def _ingest_and_cleanup(path: str, filename: str):
    try:
        count = await ingest_document(path, filename)
        logger.info("ingest_complete", filename=filename, chunks=count)
    except Exception as e:
        logger.error("ingest_error", filename=filename, error=str(e))
    finally:
        os.unlink(path)
