from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            client = chromadb.Client()
            self._collection = client.create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = doc.metadata.copy() if doc.metadata else {}
        metadata['doc_id'] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        results = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            results.append({
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma and self._collection is not None:
            ids = [doc.id for doc in docs]
            documents = [doc.content for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]
            metadatas = []
            for doc in docs:
                meta = doc.metadata.copy() if doc.metadata else {}
                meta['doc_id'] = doc.id
                metadatas.append(meta)
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            chroma_results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            results = []
            if chroma_results and 'ids' in chroma_results and chroma_results['ids']:
                for i in range(len(chroma_results['ids'][0])):
                    results.append({
                        "id": chroma_results['ids'][0][i],
                        "content": chroma_results['documents'][0][i],
                        "metadata": chroma_results['metadatas'][0][i],
                        "score": 1.0 - chroma_results['distances'][0][i] if 'distances' in chroma_results and chroma_results['distances'] else 0.0
                    })
            return results
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            chroma_results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter
            )
            results = []
            if chroma_results and 'ids' in chroma_results and chroma_results['ids']:
                for i in range(len(chroma_results['ids'][0])):
                    results.append({
                        "id": chroma_results['ids'][0][i],
                        "content": chroma_results['documents'][0][i],
                        "metadata": chroma_results['metadatas'][0][i],
                        "score": 1.0 - chroma_results['distances'][0][i] if 'distances' in chroma_results and chroma_results['distances'] else 0.0
                    })
            return results
        else:
            if not metadata_filter:
                filtered_records = self._store
            else:
                filtered_records = []
                for record in self._store:
                    match = True
                    for k, v in metadata_filter.items():
                        if record['metadata'].get(k) != v:
                            match = False
                            break
                    if match:
                        filtered_records.append(record)
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            before = self._collection.count()
            self._collection.delete(where={"doc_id": doc_id})
            after = self._collection.count()
            return before > after
        else:
            initial_len = len(self._store)
            self._store = [record for record in self._store if record['metadata'].get('doc_id') != doc_id]
            return len(self._store) < initial_len
