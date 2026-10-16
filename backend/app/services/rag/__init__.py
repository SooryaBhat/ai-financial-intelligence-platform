"""
ALLADIN RAG (Retrieval-Augmented Generation) Service Package.
Provides document ingestion, chunking, embedding generation, vector retrieval, and citation formatting.
"""
from app.services.rag.embeddings import BaseEmbeddingService, get_embedding_service
from app.services.rag.retriever import RAGRetriever
from app.services.rag.ingestion import ingest_prototype_documents

__all__ = [
    "BaseEmbeddingService",
    "get_embedding_service",
    "RAGRetriever",
    "ingest_prototype_documents",
]
