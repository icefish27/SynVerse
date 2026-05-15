from minio import Minio
from app.core.config import settings

minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,
)


def ensure_bucket():
    bucket = settings.minio_bucket
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
    return bucket
