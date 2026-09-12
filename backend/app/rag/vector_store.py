"""
ChromaDB vector store for AI Boardroom RAG.
"""

from pathlib import Path
from typing import Dict, List, Optional

import chromadb


class VectorStore:
    """Persistent ChromaDB vector store."""

    DEFAULT_COLLECTION = "boardroom_documents"

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = DEFAULT_COLLECTION,
    ):
        self.persist_directory = str(
            Path(persist_directory)
        )

        Path(self.persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.collection_name = collection_name

        print(
            f"Initializing ChromaDB: "
            f"{self.persist_directory}"
        )

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description":
                        "AI Boardroom document evidence"
                },
            )
        )

        print(
            f"ChromaDB collection ready: "
            f"{self.collection_name}"
        )

    def add_documents(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
    ) -> int:

        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match "
                "number of embeddings."
            )

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:

            ids.append(
                str(chunk["id"])
            )

            documents.append(
                chunk["text"]
            )

            metadatas.append(
                {
                    "source": str(
                        chunk.get("source", "")
                    ),
                    "page": (
                        chunk.get("page")
                        if chunk.get("page") is not None
                        else -1
                    ),
                    "chunk_index": int(
                        chunk.get("chunk_index", 0)
                    ),
                }
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source: Optional[str] = None,
    ) -> List[Dict]:

        if not query_embedding:
            return []

        if top_k <= 0:
            return []

        where = None

        if source:
            where = {
                "source": source
            }

        results = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k,
            where=where,
        )

        return self._format_results(
            results
        )

    @staticmethod
    def _format_results(
        results: Dict,
    ) -> List[Dict]:

        if not results:
            return []

        ids = results.get(
            "ids",
            [[]],
        )[0]

        documents = results.get(
            "documents",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        formatted = []

        for index, document in enumerate(
            documents
        ):

            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            formatted.append(
                {
                    "id": (
                        ids[index]
                        if index < len(ids)
                        else None
                    ),
                    "text": document,
                    "source": metadata.get(
                        "source"
                    ),
                    "page": metadata.get(
                        "page"
                    ),
                    "chunk_index": metadata.get(
                        "chunk_index"
                    ),
                    "distance": distance,
                }
            )

        return formatted

    def count(self) -> int:
        return self.collection.count()

    def delete_source(
        self,
        source: str,
    ) -> None:

        if not source:
            return

        self.collection.delete(
            where={
                "source": source
            }
        )

    def clear(self) -> None:

        self.client.delete_collection(
            self.collection_name
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description":
                        "AI Boardroom document evidence"
                },
            )
        )