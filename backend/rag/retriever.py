"""
RAG Retriever — queries ChromaDB and returns top-k relevant chunks.
"""

import asyncio
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
import chromadb
from core.config import settings

COLLECTION_NAME = "dialo_knowledge"
# Embeddings via the free Gemini API — no local model, no PyTorch, ~0 local RAM.
# Ingestion and retrieval MUST use the same model. (gemini-embedding-001 is the
# model this API key exposes; text-embedding-004 is not available on this endpoint.)
EMBED_MODEL_NAME = "gemini-embedding-001"
TOP_K = 5

# Lazy singletons — one embedder client + one Chroma client per process.
_embed_model: GoogleGenAIEmbedding | None = None
_chroma_client = None


def _get_embed_model() -> GoogleGenAIEmbedding:
    global _embed_model
    if _embed_model is None:
        _embed_model = GoogleGenAIEmbedding(
            model_name=EMBED_MODEL_NAME, api_key=settings.gemini_api_key
        )
    return _embed_model


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.chroma_host, port=settings.chroma_port
        )
    return _chroma_client


def _get_index():
    client = _get_chroma_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_ctx = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_ctx, embed_model=_get_embed_model()
    )


async def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Returns list of {text, source} dicts for the top-k relevant chunks.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _retrieve_sync, query, top_k)


def _retrieve_sync(query: str, top_k: int) -> list[dict]:
    index = _get_index()
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    return [
        {
            "text": n.node.get_content(),
            "source": n.node.metadata.get("file_name", "unknown"),
            "score": n.score,
        }
        for n in nodes
    ]
