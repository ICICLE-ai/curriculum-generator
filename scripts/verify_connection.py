"""
Quick verification script for Qdrant Cloud Pod connection
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.llm.rag.qdrant_client import QdrantRAGClient

def main():
    endpoint = "https://digitalageduvdb.pods.icicleai.tapis.io"
    # Exact 20-character key discovered inside pod
    api_key = "${:?service api key}"

    print(f"Connecting to {endpoint} with API key: {api_key}")
    client = QdrantRAGClient(
        endpoint=endpoint,
        api_key=api_key,
        exit_on_failure=False
    )

    is_healthy = client.check_health()
    print(f"Health Check Status: {is_healthy}")

    if is_healthy:
        collections = client.client.get_collections()
        print(f"Collections on Pod: {collections}")

if __name__ == "__main__":
    main()
