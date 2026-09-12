"""
Document retriever for AI Boardroom RAG.

Embeds the user's question and retrieves the most relevant
document chunks from ChromaDB.
"""

from typing import Dict, List, Optional

from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.vector_store import VectorStore


class DocumentRetriever:
    """Retrieve relevant evidence from the document vector store."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        top_k: int = 5,
    ):
        self.embedding_model = (
            embedding_model
            or EmbeddingModel()
        )

        self.vector_store = (
            vector_store
            or VectorStore()
        )

        self.top_k = top_k

    # =========================================================
    # RETRIEVE
    # =========================================================

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        source: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve the most relevant document chunks.
        """

        if not query or not query.strip():
            return []

        k = (
            top_k
            if top_k is not None
            else self.top_k
        )

        if k <= 0:
            return []

        query_embedding = (
            self.embedding_model.embed_query(
                query
            )
        )

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k,
            source=source,
        )

    # =========================================================
    # BUILD CONTEXT
    # =========================================================

    def build_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        source: Optional[str] = None,
    ) -> str:
        """
        Convert retrieved chunks into context that can be
        supplied to the Boardroom agents.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

        if not results:
            return ""

        sections = [
            "RETRIEVED DOCUMENT EVIDENCE",
            "================================",
        ]

        for index, result in enumerate(
            results,
            start=1,
        ):

            source_name = (
                result.get("source")
                or "Unknown source"
            )

            page = result.get("page")

            if page is not None and page != -1:
                location = (
                    f"{source_name}, "
                    f"page {page}"
                )
            else:
                location = source_name

            sections.extend(
                [
                    "",
                    f"[Evidence {index}]",
                    f"Source: {location}",
                    f"Content: {result['text']}",
                ]
            )

        sections.extend(
            [
                "",
                "IMPORTANT:",
                "Use the retrieved document evidence "
                "as factual context.",
                "Do not invent facts that are not supported "
                "by the evidence.",
            ]
        )

        return "\n".join(sections)

    # =========================================================
    # DEBUG / INSPECTION
    # =========================================================

    def count_documents(self) -> int:
        """Return the number of stored chunks."""

        return self.vector_store.count()