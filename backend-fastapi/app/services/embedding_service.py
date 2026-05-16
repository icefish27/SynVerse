import os
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# 离线模式：跳过 HuggingFace 在线检查，直接从本地缓存加载
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model, local_files_only=True)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """生成嵌入向量，返回 384 维 float 列表"""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    return embed([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个归一化向量的余弦相似度"""
    return float(np.dot(a, b))
