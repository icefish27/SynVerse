from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.core.config import settings
from app.core.minio import minio_client, ensure_bucket

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import novels, chapters, outlines, style_examples, knowledge, writing, kg, rhythm

app.include_router(novels.router)
app.include_router(chapters.router)
app.include_router(outlines.router)
app.include_router(style_examples.router)
app.include_router(knowledge.router)
app.include_router(writing.router)
app.include_router(kg.router)
app.include_router(rhythm.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/files/{path:path}")
async def serve_file(path: str):
    bucket = ensure_bucket()
    try:
        obj = minio_client.get_object(bucket, path)
        return StreamingResponse(obj.stream(), media_type=obj.headers.get("Content-Type", "application/octet-stream"))
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "File not found"}, status_code=404)
