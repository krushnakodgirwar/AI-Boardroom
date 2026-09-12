"""
Embedding utilities for AI Boardroom RAG.

Uses Sentence Transformers to convert document chunks
and user questions into vector embeddings.
"""

from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Wrapper around SentenceTransformer.

    The model is loaded once and reused for document
    and query embeddings.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
    ):
        self.model_name = model_name

        print(
            f"Loading embedding model: {model_name}"
        )

        self.model = SentenceTransformer(
            model_name
        )

        print(
            "Embedding model loaded successfully."
        )

    # =========================================================
    # SINGLE TEXT
    # =========================================================

    def embed_text(
        self,
        text: str,
    ) -> List[float]:
        """
        Convert one piece of text into an embedding.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot embed empty text."
            )

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    # =========================================================
    # MULTIPLE TEXTS
    # =========================================================

    def embed_texts(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Convert multiple texts into embeddings.
        """

        if not texts:
            return []

        cleaned_texts = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not cleaned_texts:
            return []

        embeddings = self.model.encode(
            cleaned_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    # =========================================================
    # QUERY
    # =========================================================

    def embed_query(
        self,
        query: str,
    ) -> List[float]:
        """
        Embed a user question for similarity search.
        """

        return self.embed_text(query)