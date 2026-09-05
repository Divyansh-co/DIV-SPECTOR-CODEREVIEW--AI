import math
import re
from typing import List, Dict, Any, Tuple

class LocalVectorStore:
    """
    High-performance, zero-dependency local vector store supporting 
    tokenized subword n-gram vector embeddings, term-frequency weights, 
    and cosine similarity matching with symbol-boosted ranking.
    """
    def __init__(self, vector_dim: int = 256):
        self.vector_dim = vector_dim
        self.chunks: List[Dict[str, Any]] = []
        self.vectors: List[List[float]] = []

    def _tokenize(self, text: str) -> List[str]:
        # Split on whitespace, punctuation, camelCase, snake_case
        s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
        s2 = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1)
        tokens = re.findall(r"[a-zA-Z0-9_]{2,}", s2.lower())
        return tokens

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.vector_dim
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for token in tokens:
            # Deterministic hash projection into embedding dimensions
            h = abs(hash(token)) % self.vector_dim
            # n-gram hash for prefix/suffix capturing
            h2 = abs(hash(token[:4])) % self.vector_dim
            vec[h] += 1.0
            vec[h2] += 0.5

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        for chunk in chunks:
            text = f"{chunk.get('name', '')} {chunk.get('docstring') or ''} {chunk.get('content', '')}"
            vec = self._embed_text(text)
            self.chunks.append(chunk)
            self.vectors.append(vec)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []

        query_vec = self._embed_text(query)
        query_tokens = set(self._tokenize(query))
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for i, doc_vec in enumerate(self.vectors):
            # Cosine similarity
            cos_sim = sum(q * d for q, d in zip(query_vec, doc_vec))

            # Exact name or token match boost
            chunk = self.chunks[i]
            chunk_name = chunk.get("name", "").lower()
            boost = 0.0
            for t in query_tokens:
                if t == chunk_name:
                    boost += 0.3
                elif t in chunk_name:
                    boost += 0.15

            total_score = cos_sim + boost
            scored.append((total_score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            res = dict(chunk)
            res["similarity_score"] = round(float(score), 4)
            results.append(res)

        return results

    def clear(self):
        self.chunks.clear()
        self.vectors.clear()
