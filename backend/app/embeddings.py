#!/usr/bin/env python3
"""Shared embedding module for the kuku legal retrieval system.

Responsibilities:
- Lazily initialize sentence-transformers/all-MiniLM-L6-v2.
- Maintain one controlled model instance per process.
- Expose embed_text(text) -> List[float].
- Expose batch embedding if useful for indexing.
- Validate input and embedding dimensions.
- Use consistent preprocessing and normalization for documents and queries.
- Fail explicitly when the model is unavailable.
- Do NOT load model on ordinary import.
"""

from pathlib import Path
from typing import List, Optional, Dict

# Module-level model instance (lazy initialization)
_embed_model: Optional["SentenceTransformer"] = None
_embed_dimension: Optional[int] = None

# Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # Fixed by MiniLM-L6-v2 architecture
CHROMA_PERSIST_DIR = Path("/home/smit-bafna/Projects/kuku/backend/persistent_chroma")
COLLECTION_NAME = "uttarakhand_provisions"


def _get_model() -> "SentenceTransformer":
    """Lazily load and return the sentence-transformers model.

    Ensures only one model instance is created per process.
    Loads on first call, not on import.
    """
    global _embed_model, _embed_dimension
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        _embed_dimension = _embed_model.get_sentence_embedding_dimension()
    return _embed_model, _embed_dimension


def embed_text(text: str) -> List[float]:
    """Generate an embedding for a single text using the shared model.

    Uses sentence-transformers/all-MiniLM-L6-v2 as specified.
    Model loads on first call; subsequent calls reuse the cached instance.
    Normalized embeddings (L2 norm = 1) are returned.

    Args:
        text: The input text to embed.

    Returns:
        Normalized embedding vector as a list of floats.

    Raises:
        ImportError: If sentence-transformers is not installed.
        ValueError: If text is empty or invalid.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty or whitespace-only text")

    try:
        model, dim = _get_model()
    except ImportError as e:
        raise ImportError(
            "sentence-transformers package is required. "
            "Install with: pip install sentence-transformers"
        ) from e

    # Generate embedding with normalization (L2 norm = 1)
    embedding = model.encode(text.strip(), normalize_embeddings=True)

    # Validate dimension
    if embedding.shape[0] != _embed_dimension:
        raise ValueError(
            f"Embedding dimension {embedding.shape[0]} does not "
            f"expected dimension {_embed_dimension}"
        )

    # Convert to list and return
    return embedding.tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts.

    More efficient than calling embed_text() in a loop for large batches.

    Args:
        texts: List of input texts to embed. Each must be non-empty.

    Returns:
        List of normalized embedding vectors as lists of floats.

    Raises:
        ValueError: If any text is empty or invalid.
    """
    if not texts:
        return []

    # Validate all texts
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(f"Text at index {i} is empty or whitespace-only")

    model, dim = _get_model()
    embeddings = model.encode([t.strip() for t in texts], normalize_embeddings=True)

    # Validate all dimensions and convert to lists
    results = []
    for i, embedding in enumerate(embeddings):
        if embedding.shape[0] != dim:
            raise ValueError(
                f"Embedding at index {i} has dimension "
                f"{embedding.shape[0]}, expected {dim}"
            )
        results.append(embedding.tolist())

    return results


def get_embedding_dimension() -> int:
    """Return the expected embedding dimension (384 for MiniLM-L6-v2).

    Useful for validation before indexing.
    """
    return EMBEDDING_DIM


def verify_embedding(embedding: List[float], expected_dim: int = None) -> bool:
    """Verify that an embedding vector has the expected dimensions.

    Args:
        embedding: The embedding vector to verify.
        expected_dim: Expected dimension. Defaults to EMBEDDING_DIM.

    Returns:
        True if valid, False otherwise.
    """
    if expected_dim is None:
        expected_dim = EMBEDDING_DIM
    if not embedding or not isinstance(embedding, list):
        return False
    if len(embedding) != expected_dim:
        return False
    # Check all elements are numeric
    try:
        [float(x) for x in embedding]
        return True
    except (ValueError, TypeError):
        return False