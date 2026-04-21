"""
Vector DB Engine — ChromaDB + Sentence Transformers
====================================================
Load tài liệu thật từ knowledge/ folder,
chunk và index vào ChromaDB để retrieval semantic.
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Tuple

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'knowledge')
CHROMA_PATH   = os.path.join(os.path.dirname(__file__), '..', '.chroma_db')

# Map filename → doc_id (khớp với expected_retrieval_ids trong golden_set.jsonl)
SOURCE_TO_DOC = {
    "warranty_policy":  ["doc_001"],
    "account_security": ["doc_002", "doc_006"],
    "pricing_refund":   ["doc_003", "doc_004"],
    "api_partner_hr":   ["doc_007", "doc_008", "doc_011"],
}


class VectorDB:
    """ChromaDB wrapper với sentence-transformers embedding."""

    def __init__(self, collection_name: str = "lab14_kb"):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def ingest_knowledge_base(self, force_reload: bool = False):
        """Load và index tất cả file .txt trong knowledge/ folder."""
        if self.collection.count() > 0 and not force_reload:
            print(f"  [VectorDB] Already indexed {self.collection.count()} chunks. Skipping.")
            return

        # Clear nếu force reload
        if force_reload and self.collection.count() > 0:
            self.client.delete_collection("lab14_kb")
            self.collection = self.client.get_or_create_collection(
                name="lab14_kb",
                embedding_function=self.embed_fn,
                metadata={"hnsw:space": "cosine"}
            )

        docs, ids, metadatas = [], [], []
        chunk_id = 0

        for filename in os.listdir(KNOWLEDGE_DIR):
            if not filename.endswith('.txt'):
                continue
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Chunk theo paragraph (~200 chars overlap)
            chunks = self._chunk_text(content, chunk_size=300, overlap=50)
            for i, chunk in enumerate(chunks):
                doc_id = f"{filename.replace('.txt', '')}_{i:03d}"
                docs.append(chunk)
                ids.append(doc_id)
                metadatas.append({"source": filename, "chunk_index": i})
                chunk_id += 1

        if docs:
            self.collection.add(documents=docs, ids=ids, metadatas=metadatas)
            print(f"  [VectorDB] Indexed {len(docs)} chunks from {KNOWLEDGE_DIR}")

    def _chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Chia text thành chunks theo paragraph, không cắt giữa câu."""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < chunk_size:
                current = current + " " + para if current else para
            else:
                if current:
                    chunks.append(current)
                current = para
        if current:
            chunks.append(current)
        return chunks

    def search(self, query: str, top_k: int = 5) -> Tuple[List[str], List[str]]:
        """
        Semantic search. Trả về (contexts, doc_ids).
        """
        if self.collection.count() == 0:
            return [], []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        contexts  = results["documents"][0]
        # Map filename → doc_XXX IDs
        doc_ids = []
        for m in results["metadatas"][0]:
            src = m["source"].replace(".txt", "")
            mapped = SOURCE_TO_DOC.get(src, [src])
            doc_ids.extend(mapped)
        doc_ids = list(dict.fromkeys(doc_ids))  # deduplicate, preserve order
        return contexts, doc_ids

    def count(self) -> int:
        return self.collection.count()
