"""
DigitalAgEdu Vector Index Seeding Module
========================================
Delegates to the ICICLE Qdrant Vector Cloud ingestion engine.
"""

def build_vector_index(endpoint: str = None, collection_name: str = None, api_key: str = None):
    """
    Seeds the ICICLE Qdrant Vector Database cloud pod with concept guides and reference notebooks.
    """
    try:
        from scripts.migrate_rag_to_qdrant import run_migration
        return run_migration(
            endpoint=endpoint,
            collection_name=collection_name,
            api_key=api_key
        )
    except ImportError:
        raise ImportError("Migration script 'scripts.migrate_rag_to_qdrant' is only available in development environments.")
