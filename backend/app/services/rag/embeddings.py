"""
Configurable Embedding Provider Abstraction for ALLADIN RAG.

Supports provider pluggability:
- Google GenAI (default: gemini-embedding-001 with 768-dim output)
- MockEmbeddingService (deterministic unit-normalized vectors for testing & offline mode)
- Future: OpenAI (text-embedding-3-small), HuggingFace, local Ollama / TEI
"""
import hashlib
import math
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class BaseEmbeddingService(ABC):
    """Abstract Base Class for text embedding services."""

    def __init__(self, model_name: str, dimension: int = 768) -> None:
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a dense vector embedding for a single text query or document chunk."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts in batch."""
        pass


class GoogleGenAIEmbeddingService(BaseEmbeddingService):
    """
    Google GenAI Embedding Provider.
    Uses the official google.genai Client with Matryoshka Representation Learning (MRL)
    output_dimensionality truncation to the configured dimension (e.g. 768).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        dimension: Optional[int] = None,
    ) -> None:
        super().__init__(
            model_name=model_name or settings.rag_embedding_model,
            dimension=dimension or settings.rag_embedding_dimensions,
        )
        self.api_key = (
            api_key
            or settings.gemini_api_key
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", "")
        )
        if not GENAI_AVAILABLE:
            raise RuntimeError("google-genai package is not installed in the environment.")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings or environment.")

        self.client = genai.Client(api_key=self.api_key)

    def embed_text(self, text: str) -> List[float]:
        """Generate a 768-dim embedding for a single text string."""
        if not text.strip():
            return [0.0] * self.dimension

        try:
            config = types.EmbedContentConfig(output_dimensionality=self.dimension)
            res = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=config,
            )
            emb = res.embeddings[0] if (hasattr(res, "embeddings") and res.embeddings) else getattr(res, "embedding", None)
            vals = emb.values if hasattr(emb, "values") else emb
            return list(vals)
        except Exception as e:
            logger.error("Failed to generate Google embedding for text: {}", e)
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batches of up to 32 items."""
        results: List[List[float]] = []
        batch_size = 32

        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            for text in chunk:
                # Sequential fallback if batch embed is provider-limited
                results.append(self.embed_text(text))

        return results


class MockEmbeddingService(BaseEmbeddingService):
    """
    Deterministic Mock Embedding Provider for isolated unit testing.
    Generates reproducible, L2-normalized 768-dim float vectors using SHA-256.
    Does not make any network calls or consume API quotas.
    """

    def __init__(self, dimension: int = 768) -> None:
        super().__init__(model_name="mock-hash-embedding", dimension=dimension)

    def embed_text(self, text: str) -> List[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand seed deterministically to requested dimension
        raw_values = []
        for i in range(self.dimension):
            byte_idx = i % len(seed)
            factor = (seed[byte_idx] / 255.0) - 0.5
            raw_values.append(factor)

        # L2-normalize
        norm = math.sqrt(sum(v * v for v in raw_values)) or 1.0
        return [v / norm for v in raw_values]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def get_embedding_service(provider: Optional[str] = None) -> BaseEmbeddingService:
    """
    Factory function returning the configured embedding service instance.
    Provider resolution order:
    1. Explicit provider argument
    2. settings.rag_embedding_provider ("google", "mock")
    3. Fallback to mock if API key is absent
    """
    selected_provider = (provider or settings.rag_embedding_provider or "google").lower()

    if selected_provider == "mock":
        logger.info("Using MockEmbeddingService (deterministic offline embeddings)")
        return MockEmbeddingService(dimension=settings.rag_embedding_dimensions)

    if selected_provider == "google":
        try:
            return GoogleGenAIEmbeddingService(
                model_name=settings.rag_embedding_model,
                dimension=settings.rag_embedding_dimensions,
            )
        except Exception as e:
            logger.warning("Could not initialize GoogleGenAIEmbeddingService: {}. Falling back to Mock.", e)
            return MockEmbeddingService(dimension=settings.rag_embedding_dimensions)

    raise ValueError(f"Unsupported RAG embedding provider: '{selected_provider}'. Supported: 'google', 'mock'")
