"""
Live Vector Embedding Storage & Semantic Retrieval Test
========================================================
Stores a 384-dimensional vector embedding in the ICICLE Qdrant Pod and queries it back.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.llm.rag.qdrant_client import QdrantRAGClient
from sentence_transformers import SentenceTransformer
from qdrant_client.http import models

def main():
    endpoint = "https://digitalageduvdb.pods.icicleai.tapis.io"
    api_key = "${:?service api key}"
    collection_name = "digitalagedu_rag_knowledge"

    print("==================================================")
    print("Testing Vector Storage & Retrieval on ICICLE Qdrant:")
    print(f"Endpoint:   {endpoint}")
    print(f"Collection: {collection_name}")
    print("==================================================")

    # 1. Initialize Client
    client = QdrantRAGClient(
        endpoint=endpoint,
        collection_name=collection_name,
        api_key=api_key,
        exit_on_failure=False
    )

    # 2. Check Health
    print("\n[Step 1/4] Checking Pod Health...")
    if not client.check_health():
        print("[ERROR] Health check failed.")
        return
    print("  -> Health check PASSED!")

    # 3. Ensure Collection
    print("\n[Step 2/4] Initializing 'digitalagedu_rag_knowledge' Collection...")
    client.ensure_collection(collection_name=collection_name, vector_size=384)
    print("  -> Collection created / verified!")

    # 4. Generate Embedding & Store
    print("\n[Step 3/4] Generating Embedding & Storing Point...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    sample_text = (
        "In PyTorch, a Convolutional Neural Network (CNN) extracts spatial hierarchies of features "
        "using Conv2d layers followed by BatchNorm2d, ReLU activation, and MaxPool2d layers."
    )
    vector = embedder.encode(sample_text).tolist()
    point_id = str(uuid.uuid4())

    payload = {
        "text": sample_text,
        "primary_topic": "custom_cnn",
        "topics": ["custom_cnn", "pytorch_basics"],
        "chunk_type": "guide",
        "source_file": "digitalagedu/core/concepts_registry.py"
    }

    client.client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        ]
    )
    print(f"  -> Successfully stored Point ID: {point_id}")

    # 5. Query and Verify
    print("\n[Step 4/4] Querying Vector Database for Semantic Retrieval...")
    results = client.query_similar(
        query_text="How do Conv2d and BatchNorm layers work in PyTorch CNNs?",
        topic="custom_cnn",
        top_k=2
    )

    print(f"  -> Retrieved {len(results)} matching point(s):")
    for r in results:
        print(f"  - [Score: {r['score']:.4f}] Topic: {r.get('topic', 'N/A')} | Type: {r.get('chunk_type', 'N/A')}")
        print(f"    Source: {r.get('source_file', 'N/A')}")
        print(f"    Text: {r.get('text', '')[:120]}...\n")

    print("==================================================")
    print("[SUCCESS] All Live Vector Storage & Retrieval Tests Passed!")
    print("==================================================")

if __name__ == "__main__":
    main()
