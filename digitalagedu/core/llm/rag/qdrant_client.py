from __future__ import annotations

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional, Union

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    QdrantClient = None
    models = None

logger = logging.getLogger(__name__)

DEFAULT_QDRANT_ENDPOINT = "https://digitalageduvdb.pods.icicleai.tapis.io"
DEFAULT_COLLECTION_NAME = "digitalagedu_rag_knowledge"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_POD_API_KEY = "${:?service api key}"


class QdrantConnectionError(Exception):
    """Raised when communication with ICICLE Qdrant service fails after maximum retries."""
    pass


class QdrantRAGClient:
    """
    Client for querying and managing vector embeddings on the ICICLE Qdrant Cloud Pod.
    Enforces a 3-retry fail-fast policy and supports dense embeddings & Cross-Encoder reranking.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        collection_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        exit_on_failure: bool = True,
    ):
        if QdrantClient is None:
            raise ImportError(
                "qdrant-client package is required. Install it with `pip install qdrant-client`."
            )

        self.endpoint = endpoint or os.getenv("QDRANT_ENDPOINT") or DEFAULT_QDRANT_ENDPOINT
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION") or DEFAULT_COLLECTION_NAME
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exit_on_failure = exit_on_failure

        # 1. Enforce TAPIS_JWT / QDRANT_API_KEY requirement with pod default fallback
        self.api_key = api_key or os.getenv("TAPIS_JWT") or os.getenv("QDRANT_API_KEY") or DEFAULT_POD_API_KEY
        if not self.api_key:
            msg = (
                "[FATAL] TAPIS_JWT environment variable is required to authenticate with the "
                "ICICLE Qdrant Vector Database. Please set TAPIS_JWT in your environment or job submission."
            )
            print(msg, file=sys.stderr)
            if self.exit_on_failure:
                sys.exit(1)
            raise ValueError(msg)

        # 2. Initialize Qdrant Client with HTTPS ingress headers (port 443, no gRPC)
        is_https = self.endpoint.startswith("https://")
        headers = {
            "api-key": self.api_key,
        }

        self.client = QdrantClient(
            url=self.endpoint,
            port=443 if is_https else None,
            https=is_https,
            prefer_grpc=False,
            api_key=self.api_key,
            headers=headers,
            timeout=self.timeout
        )

        self._embedder = None
        self._reranker = None

    def _get_embedder(self):
        """Lazy loads SentenceTransformer for query embedding generation."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model '{DEFAULT_EMBEDDING_MODEL}' into memory...")
            self._embedder = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
        return self._embedder

    def _get_reranker(self):
        """Lazy loads CrossEncoder for semantic candidate reranking."""
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading CrossEncoder model '{DEFAULT_RERANKER_MODEL}' into memory...")
            self._reranker = CrossEncoder(DEFAULT_RERANKER_MODEL)
        return self._reranker

    def _handle_fatal_error(self, operation: str, error: Exception):
        """Logs fatal error and terminates process according to fail-fast policy."""
        msg = (
            f"\n[FATAL ERROR] ICICLE Qdrant operation '{operation}' failed after {self.max_retries} attempts.\n"
            f"Endpoint: {self.endpoint}\n"
            f"Collection: {self.collection_name}\n"
            f"Details: {error}\n"
            f"Terminating pipeline execution (fail-fast policy enabled, no fallback)."
        )
        print(msg, file=sys.stderr)
        if self.exit_on_failure:
            sys.exit(1)
        raise QdrantConnectionError(msg) from error

    def check_health(self) -> bool:
        """
        Verifies connectivity and authentication with the ICICLE Qdrant pod.
        Retries up to max_retries times with timeout; exits if unreachable.
        """
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Query collections to verify network connectivity and token validity
                _ = self.client.get_collections()
                return True
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Health check attempt {attempt}/{self.max_retries} failed for {self.endpoint}: {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        self._handle_fatal_error("check_health", last_exception)
        return False

    def ensure_collection(
        self,
        collection_name: Optional[str] = None,
        vector_size: int = 384,
        distance: str = "Cosine"
    ) -> bool:
        """
        Verifies whether the target collection exists on the pod; creates it if missing.
        """
        target_name = collection_name or self.collection_name
        dist_enum = getattr(models.Distance, distance.upper(), models.Distance.COSINE)

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                collections = self.client.get_collections().collections
                exists = any(c.name == target_name for c in collections)

                if not exists:
                    logger.info(f"Collection '{target_name}' not found. Creating with vector_size={vector_size}, distance={distance}...")
                    self.client.create_collection(
                        collection_name=target_name,
                        vectors_config=models.VectorParams(
                            size=vector_size,
                            distance=dist_enum
                        )
                    )
                    logger.info(f"Successfully created collection '{target_name}'.")
                return True
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"ensure_collection attempt {attempt}/{self.max_retries} failed for '{target_name}': {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        self._handle_fatal_error("ensure_collection", last_exception)
        return False

    def build_query_filter(
        self,
        topic: Optional[str] = None,
        chunk_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Optional[models.Filter]:
        """
        Builds a structured Qdrant Filter supporting topic arrays, primary topic, and chunk types.
        """
        must_conditions = []
        should_conditions = []

        if topic:
            should_conditions.append(
                models.FieldCondition(
                    key="topics",
                    match=models.MatchValue(value=topic)
                )
            )
            should_conditions.append(
                models.FieldCondition(
                    key="primary_topic",
                    match=models.MatchValue(value=topic)
                )
            )
            should_conditions.append(
                models.FieldCondition(
                    key="topic",
                    match=models.MatchValue(value=topic)
                )
            )

        if chunk_type:
            must_conditions.append(
                models.FieldCondition(
                    key="chunk_type",
                    match=models.MatchValue(value=chunk_type)
                )
            )

        if filter_dict:
            for k, v in filter_dict.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=k,
                        match=models.MatchValue(value=v)
                    )
                )

        if not must_conditions and not should_conditions:
            return None

        return models.Filter(
            must=must_conditions if must_conditions else None,
            should=should_conditions if should_conditions else None
        )

    def query_similar(
        self,
        query_text: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        topic: Optional[str] = None,
        chunk_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        rerank: bool = False,
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Executes vector similarity search against the ICICLE Qdrant pod with 3-attempt fail-fast retry.
        Supports automatic embedding of query_text and optional Cross-Encoder reranking.
        """
        if query_vector is None:
            if not query_text:
                raise ValueError("Either `query_text` or `query_vector` must be provided.")
            embedder = self._get_embedder()
            query_vector = embedder.encode(query_text).tolist()

        query_filter = self.build_query_filter(
            topic=topic,
            chunk_type=chunk_type,
            filter_dict=filter_dict
        )

        last_exception = None
        hits = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if hasattr(self.client, "query_points"):
                    response = self.client.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        query_filter=query_filter,
                        limit=top_k
                    )
                    hits = response.points
                else:
                    hits = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        query_filter=query_filter,
                        limit=top_k
                    )
                break
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Query search attempt {attempt}/{self.max_retries} failed for collection '{self.collection_name}': {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        if hits is None:
            self._handle_fatal_error("query_similar", last_exception)
            return []

        # Format retrieved points into uniform candidate dictionaries
        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append({
                "id": str(hit.id),
                "score": float(hit.score),
                "text": payload.get("text", ""),
                "topic": payload.get("topic", payload.get("primary_topic", "")),
                "topics": payload.get("topics", []),
                "chunk_type": payload.get("chunk_type", ""),
                "source_file": payload.get("source_file", payload.get("file", "")),
                "payload": payload
            })

        # Apply Cross-Encoder reranking if requested
        if rerank and query_text and results:
            results = self.rerank_results(query=query_text, results=results, top_n=top_n)

        return results

    def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank retrieved candidates using cross-encoder/ms-marco-MiniLM-L-6-v2.
        """
        limit = top_k if top_k is not None else (top_n if top_n is not None else 5)
        if not results:
            return []

        reranker = self._get_reranker()
        pairs = [[query, r.get("text", "")] for r in results]
        scores = reranker.predict(pairs)

        for r, score in zip(results, scores):
            r["rerank_score"] = float(score)
            r["score"] = float(score)

        results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return results[:limit]
