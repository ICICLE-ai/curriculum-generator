"""
DigitalAgEdu Vector Index Seeding Module
========================================
Delegates to the ICICLE Qdrant Vector Cloud ingestion engine.
"""

from scripts.migrate_rag_to_qdrant import run_migration

def build_vector_index(endpoint: str = None, collection_name: str = None, api_key: str = None):
    """
    Seeds the ICICLE Qdrant Vector Database cloud pod with concept guides and reference notebooks.
    """
    return run_migration(
        endpoint=endpoint,
        collection_name=collection_name,
        api_key=api_key
    )
