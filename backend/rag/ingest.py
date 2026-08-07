"""
RAG Document Ingestion Pipeline
Loads documents → chunks → embeds with the Gemini API → upserts to ChromaDB
"""

import asyncio
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
import structlog

# Reuse the cached Gemini embedder + Chroma client across ingestion and retrieval.
from rag.retriever import COLLECTION_NAME, _get_embed_model, _get_chroma_client

logger = structlog.get_logger()

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


def _get_chroma_collection():
    return _get_chroma_client().get_or_create_collection(COLLECTION_NAME)


async def ingest_document(file_path: str, filename: str) -> int:
    """
    Ingest a single document file into ChromaDB.
    Returns the number of chunks stored.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _ingest_sync, file_path, filename)


def _ingest_sync(file_path: str, filename: str) -> int:
    logger.info("ingest_start", filename=filename)

    # Load
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()

    # Chunk
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)
    logger.info("ingest_chunked", filename=filename, chunks=len(nodes))

    # Embed + store
    embed_model = _get_embed_model()
    chroma_collection = _get_chroma_collection()
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_ctx = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(
        nodes,
        storage_context=storage_ctx,
        embed_model=embed_model,
        show_progress=False,
    )
    logger.info("ingest_complete", filename=filename, chunks=len(nodes))
    return len(nodes)
