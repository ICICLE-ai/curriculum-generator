"""
Live Connection & Health Check Test Script for ICICLE Qdrant Pod
Run with:
    python scripts/test_live_qdrant.py
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.llm.rag.qdrant_client import QdrantRAGClient

def run_live_test():
    # Accept from CLI argument or environment variables
    jwt = sys.argv[1] if len(sys.argv) > 1 else (os.getenv("TAPIS_JWT") or os.getenv("QDRANT_API_KEY") or "digital-age-edu-storage-key")
    endpoint = sys.argv[2] if len(sys.argv) > 2 else (os.getenv("QDRANT_ENDPOINT") or "https://digitalageduqdrant.pods.icicleai.tapis.io")

    print("==================================================")
    print("Connecting to ICICLE Qdrant Pod:")
    print(f"Endpoint: {endpoint}")
    print(f"Auth Key: {jwt[:4]}***{jwt[-4:] if len(jwt) > 8 else ''}")
    print("==================================================")

    # 1. Initialize Client
    client = QdrantRAGClient(
        endpoint=endpoint,
        collection_name="digitalagedu_rag_knowledge",
        api_key=jwt,
        exit_on_failure=False
    )

    # 2. Health Check
    print("[1/3] Running Health Check...")
    try:
        if client.check_health():
            print("  [SUCCESS] ICICLE Qdrant Pod is reachable & authenticated!")
    except Exception as e:
        print(f"  [FAILURE] Health check failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. List Existing Collections
    print("\n[2/3] Checking Collections...")
    try:
        collections = client.client.get_collections().collections
        col_names = [c.name for c in collections]
        print(f"  Found {len(col_names)} collection(s) on pod: {col_names}")
    except Exception as e:
        print(f"  [WARNING] Could not fetch collections: {e}")

    # 4. Ensure Target Collection Exists
    print("\n[3/3] Ensuring 'digitalagedu_rag_knowledge' Collection...")
    try:
        client.ensure_collection("digitalagedu_rag_knowledge", vector_size=384)
        print("  [SUCCESS] Collection 'digitalagedu_rag_knowledge' is ready!")
    except Exception as e:
        print(f"  [FAILURE] Could not ensure collection: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n==================================================")
    print("[SUCCESS] All Live Qdrant Tests Passed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_live_test()
