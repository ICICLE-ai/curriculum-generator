import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from digitalagedu.core.llm.rag.qdrant_client import (
    QdrantRAGClient,
    QdrantConnectionError,
    DEFAULT_QDRANT_ENDPOINT,
    DEFAULT_COLLECTION_NAME,
)


class TestQdrantRAGClient(unittest.TestCase):

    def setUp(self):
        self.test_jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.dummy_payload.dummy_signature"

    def test_missing_tapis_jwt_raises_error(self):
        """Verify client enforces key requirement if both env and default are absent."""
        with patch("digitalagedu.core.llm.rag.qdrant_client.DEFAULT_POD_API_KEY", None):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises((ValueError, SystemExit)):
                    QdrantRAGClient(api_key=None, exit_on_failure=False)

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_init_with_valid_tapis_jwt(self, mock_qdrant_client):
        """Verify client initializes with TAPIS_JWT from environment."""
        with patch.dict(os.environ, {"TAPIS_JWT": self.test_jwt}):
            client = QdrantRAGClient()
            self.assertEqual(client.api_key, self.test_jwt)
            self.assertEqual(client.endpoint, DEFAULT_QDRANT_ENDPOINT)
            self.assertEqual(client.collection_name, DEFAULT_COLLECTION_NAME)
            mock_qdrant_client.assert_called_once_with(
                url=DEFAULT_QDRANT_ENDPOINT,
                port=443,
                https=True,
                prefer_grpc=False,
                api_key=self.test_jwt,
                headers={
                    "api-key": self.test_jwt,
                },
                timeout=10.0
            )

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_check_health_success(self, mock_qdrant_client):
        """Verify check_health returns True on successful response."""
        mock_instance = MagicMock()
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        mock_qdrant_client.return_value = mock_instance

        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)
        self.assertTrue(client.check_health())
        mock_instance.get_collections.assert_called_once()

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_check_health_fail_fast_after_3_retries(self, mock_qdrant_client):
        """Verify check_health retries 3 times then raises QdrantConnectionError."""
        mock_instance = MagicMock()
        mock_instance.get_collections.side_effect = Exception("Connection refused to pod")
        mock_qdrant_client.return_value = mock_instance

        client = QdrantRAGClient(
            api_key=self.test_jwt,
            max_retries=3,
            retry_delay=0.01,
            exit_on_failure=False
        )

        with self.assertRaises(QdrantConnectionError):
            client.check_health()

        self.assertEqual(mock_instance.get_collections.call_count, 3)

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_ensure_collection_creates_if_missing(self, mock_qdrant_client):
        """Verify collection is created if not found on pod."""
        mock_instance = MagicMock()
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        mock_qdrant_client.return_value = mock_instance

        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)
        client.ensure_collection(collection_name="test_col", vector_size=384)

        mock_instance.create_collection.assert_called_once()
        call_kwargs = mock_instance.create_collection.call_args[1]
        self.assertEqual(call_kwargs["collection_name"], "test_col")

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_ensure_collection_skips_if_already_exists(self, mock_qdrant_client):
        """Verify collection creation is skipped if collection exists."""
        mock_col = MagicMock()
        mock_col.name = "existing_col"
        mock_instance = MagicMock()
        mock_instance.get_collections.return_value = MagicMock(collections=[mock_col])
        mock_qdrant_client.return_value = mock_instance

        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)
        client.ensure_collection(collection_name="existing_col", vector_size=384)

        mock_instance.create_collection.assert_not_called()

    def test_build_query_filter_topic_and_type(self):
        """Verify query filter builds correct Must conditions for payload matching."""
        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)
        q_filter = client.build_query_filter(topic="custom_cnn", chunk_type="code")

        self.assertIsNotNone(q_filter)
        self.assertEqual(len(q_filter.must), 1)
        self.assertEqual(len(q_filter.should), 3)

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_query_similar_with_vector(self, mock_qdrant_client):
        """Verify query_similar executes search with pre-computed vector."""
        mock_instance = MagicMock()
        mock_hit = MagicMock()
        mock_hit.id = "doc_1"
        mock_hit.score = 0.92
        mock_hit.payload = {
            "text": "class ConvNet(nn.Module): pass",
            "topic": "custom_cnn",
            "chunk_type": "code",
            "source_file": "cnn_intro.ipynb"
        }
        mock_instance.query_points.return_value = MagicMock(points=[mock_hit])
        mock_qdrant_client.return_value = mock_instance

        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)
        results = client.query_similar(query_vector=[0.1] * 384, top_k=2, topic="custom_cnn")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "doc_1")
        self.assertEqual(results[0]["score"], 0.92)
        self.assertEqual(results[0]["chunk_type"], "code")

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_query_similar_lazy_loads_embedder(self, mock_qdrant_client):
        """Verify query_similar lazy-loads SentenceTransformer for string queries."""
        mock_instance = MagicMock()
        mock_instance.query_points.return_value = MagicMock(points=[])
        mock_qdrant_client.return_value = mock_instance

        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)

        mock_embedder = MagicMock()
        mock_embedder.encode.return_value = MagicMock(tolist=lambda: [0.2] * 384)
        client._get_embedder = MagicMock(return_value=mock_embedder)

        results = client.query_similar(query_text="convolutional layer architecture")

        client._get_embedder.assert_called_once()
        mock_embedder.encode.assert_called_once_with("convolutional layer architecture")
        mock_instance.query_points.assert_called_once()

    @patch("digitalagedu.core.llm.rag.qdrant_client.QdrantClient")
    def test_rerank_results_orders_by_cross_encoder_score(self, mock_qdrant_client):
        """Verify rerank_results sorts candidates by CrossEncoder score descending."""
        client = QdrantRAGClient(api_key=self.test_jwt, retry_delay=0.01)

        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = [0.15, 0.88, 0.42]
        client._get_reranker = MagicMock(return_value=mock_reranker)

        candidates = [
            {"id": "1", "text": "Low relevance passage", "score": 0.90},
            {"id": "2", "text": "Highest cross-encoder relevance passage", "score": 0.70},
            {"id": "3", "text": "Medium relevance passage", "score": 0.80},
        ]

        reranked = client.rerank_results("test query", candidates, top_k=2)

        self.assertEqual(len(reranked), 2)
        self.assertEqual(reranked[0]["id"], "2")
        self.assertEqual(reranked[1]["id"], "3")
        self.assertAlmostEqual(reranked[0]["rerank_score"], 0.88)
        self.assertAlmostEqual(reranked[1]["rerank_score"], 0.42)


if __name__ == "__main__":
    unittest.main()
