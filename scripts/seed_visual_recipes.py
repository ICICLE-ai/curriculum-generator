#!/usr/bin/env python3
"""
Seed Visual Recipes into ICICLE Qdrant Vector Cloud.
Upserts atomic presentation and visual micro-patterns into the
'digitalagedu_rag_knowledge' collection with chunk_type='presentation_recipe'.
"""

import os
import sys
import uuid
import json
import logging
import urllib.request
import urllib.error

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.llm.visuals.visual_recipes import VISUAL_RECIPES
from digitalagedu.core.llm.rag.qdrant_client import (
    DEFAULT_QDRANT_ENDPOINT,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_POD_API_KEY,
    DEFAULT_EMBEDDING_MODEL,
    resolve_tapis_access_token
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_visual_recipes")


def seed_recipes(
    endpoint: str = DEFAULT_QDRANT_ENDPOINT,
    collection: str = DEFAULT_COLLECTION_NAME,
    api_key: str = None
):
    key = api_key or os.getenv("QDRANT_API_KEY") or os.getenv("TAPIS_JWT") or DEFAULT_POD_API_KEY
    resolved_key = resolve_tapis_access_token(key)

    logger.info("==================================================================")
    logger.info("       DigitalAgEdu Qdrant Visual Recipe Seeding Engine          ")
    logger.info("==================================================================")
    logger.info(f"Target Pod:     {endpoint}")
    logger.info(f"Collection:     {collection}")
    logger.info(f"Total Recipes:  {len(VISUAL_RECIPES)}")
    logger.info("==================================================================")

    # 1. Initialize Embedder
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model '{DEFAULT_EMBEDDING_MODEL}'...")
        embedder = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
    except ImportError:
        logger.error(
            "sentence-transformers is required to generate 384d vector embeddings. "
            "Install with `pip install sentence-transformers` or run inside the container."
        )
        sys.exit(1)

    # 2. Generate Embeddings & Build Point Payloads
    points = []
    logger.info(f"Vectorizing {len(VISUAL_RECIPES)} visual recipes...")
    for recipe in VISUAL_RECIPES:
        embed_input = f"{recipe['title']}. {recipe['description']} Keywords: {', '.join(recipe['topics'])}"
        vec = embedder.encode(embed_input).tolist()
        
        # Deterministic UUID from recipe id
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"digitalagedu.recipe.{recipe['id']}"))

        payload = {
            "title": recipe["title"],
            "primary_topic": recipe["primary_topic"],
            "topics": recipe["topics"],
            "chunk_type": recipe["chunk_type"],
            "description": recipe["description"],
            "text": recipe["text"],
            "source_file": "digitalagedu/core/llm/visuals/visual_recipes.py"
        }

        points.append({
            "id": point_id,
            "vector": vec,
            "payload": payload
        })

    # 3. Upsert via Qdrant REST API
    upsert_url = f"{endpoint.rstrip('/')}/collections/{collection}/points?wait=true"
    headers = {
        "Content-Type": "application/json",
        "api-key": resolved_key,
        "X-Tapis-Token": resolved_key
    }
    body = json.dumps({"points": points}).encode("utf-8")

    logger.info(f"Uploading {len(points)} vector points to Qdrant pod via REST API...")
    req = urllib.request.Request(upsert_url, data=body, headers=headers, method="PUT")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            if resp_data.get("status") == "ok":
                logger.info(f"[SUCCESS] Successfully seeded {len(points)} visual recipes into '{collection}'!")
                logger.info(f"Response: {resp_data}")
            else:
                logger.warning(f"[WARNING] Unexpected response from Qdrant: {resp_data}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        logger.error(f"[FAILURE] HTTP {e.code} uploading to Qdrant: {err_msg}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[FAILURE] Could not connect to Qdrant pod: {e}")
        sys.exit(1)


if __name__ == "__main__":
    seed_recipes()
