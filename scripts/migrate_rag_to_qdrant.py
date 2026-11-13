"""
Migration & Ingestion Script for ICICLE Qdrant Vector Database
==============================================================
Populates the cloud Qdrant Vector Database with:
1. Pedagogical concept guides, formulas, algorithms & pitfalls from `concepts_registry.py`
2. Curated external documentation links from `RESOURCE_LINKS`
3. Explanations and code cells parsed from `reference_repos/deeplearning-models`
4. The Phase 1 pipeline's own DINOv2 / SAM / Grad-CAM stage code (`curriculum_resources/`)
5. Domain-agnostic concept sources (`CONCEPT_SOURCES`: scikit-image, scikit-learn, SAM, DINOv2, pytorch-grad-cam);
   files built around a specific application domain are skipped (`DOMAIN_TERMS`)

Each run is a full rebuild of the knowledge chunks; visual recipes (scripts/seed_visual_recipes.py) are kept.

Usage:
    python scripts/migrate_rag_to_qdrant.py [--endpoint <URL>] [--api-key <KEY>]
"""

import os
import re
import sys
import json
import uuid
import argparse
import subprocess
from typing import List, Dict, Any

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.concepts_registry import CONCEPT_GUIDES, RESOURCE_LINKS
from digitalagedu.core.llm.rag.qdrant_client import (
    QdrantRAGClient,
    DEFAULT_QDRANT_ENDPOINT,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_POD_API_KEY
)

try:
    from qdrant_client.http import models
except ImportError:
    models = None

try:
    from sentence_transformers import SentenceTransformer
except (ImportError, OSError):  # OSError: a broken torch/torchaudio build; parsers stay importable without it
    SentenceTransformer = None

REFERENCE_REPO_URL = "https://github.com/rasbt/deeplearning-models.git"
REFERENCE_REPO_DIR = os.path.join("reference_repos", "deeplearning-models")


def clone_reference_repo_if_needed():
    """Clones rasbt/deeplearning-models if not already present locally."""
    if not os.path.exists(REFERENCE_REPO_DIR):
        print(f"[INFO] Cloning {REFERENCE_REPO_URL} into '{REFERENCE_REPO_DIR}'...")
        os.makedirs("reference_repos", exist_ok=True)
        # Fails loudly: the migration rebuilds the collection, so a silent clone failure would drop these chunks
        subprocess.run(["git", "clone", "--depth", "1", REFERENCE_REPO_URL, REFERENCE_REPO_DIR], check=True)
        print("[INFO] Reference repository cloned successfully.")
    else:
        print(f"[INFO] Found local reference repository at '{REFERENCE_REPO_DIR}'.")


def parse_notebook(filepath: str) -> tuple[List[str], List[str]]:
    """Extracts Markdown text cells and Python code cells from a .ipynb file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            notebook = json.load(f)
    except Exception as e:
        print(f"[WARNING] Skipping unreadable notebook {filepath}: {e}")
        return [], []

    md_cells = []
    code_cells = []

    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", [])).strip()
        if not source:
            continue
        if cell_type == "markdown":
            md_cells.append(source)
        elif cell_type == "code":
            code_cells.append(source)

    return md_cells, code_cells


def map_notebook_path_to_topics(rel_path: str) -> tuple[str, List[str]]:
    """Maps a notebook file path to primary topic and relevant secondary topics."""
    rel_lower = rel_path.lower().replace("\\", "/")
    
    if "cnn" in rel_lower or "convolution" in rel_lower:
        return "custom_cnn", ["custom_cnn", "cnn_optimization", "pytorch_basics"]
    elif "transfer_learning" in rel_lower or "finetuning" in rel_lower or "resnet" in rel_lower:
        return "transfer_learning", ["transfer_learning", "custom_cnn", "image_datasets"]
    elif "segmentation" in rel_lower or "unet" in rel_lower:
        return "semantic_segmentation", ["semantic_segmentation", "interactive_segmentation"]
    elif "mlp" in rel_lower or "feedforward" in rel_lower or "linear" in rel_lower:
        return "pytorch_basics", ["pytorch_basics", "numpy_basics"]
    elif "autoencoder" in rel_lower or "embedding" in rel_lower or "cluster" in rel_lower:
        return "vector_embeddings", ["vector_embeddings", "pandas_analytics"]
    elif "regularization" in rel_lower or "optimization" in rel_lower:
        return "cnn_optimization", ["cnn_optimization", "custom_cnn"]
    elif "gradcam" in rel_lower or "xai" in rel_lower or "explain" in rel_lower:
        return "explainable_ai", ["explainable_ai", "custom_cnn"]
    elif "dataset" in rel_lower or "dataloader" in rel_lower:
        return "image_datasets", ["image_datasets", "pytorch_basics"]
    else:
        # Fallback to general deep learning / pytorch basics
        return "pytorch_basics", ["pytorch_basics"]


def collect_concept_registry_documents() -> List[Dict[str, Any]]:
    """Extracts high-value pedagogical chunks from concepts_registry.py."""
    documents = []

    for topic_id, guide_data in CONCEPT_GUIDES.items():
        # 1. Core Concepts
        for concept in guide_data.get("core_concepts", []):
            name = concept.get("name", "")
            desc = concept.get("description", "")
            text = f"### Concept: {name}\n\n{desc}"
            documents.append({
                "text": text,
                "metadata": {
                    "source_file": "digitalagedu/core/concepts_registry.py",
                    "primary_topic": topic_id,
                    "topics": [topic_id],
                    "chunk_type": "guide",
                    "title": name
                }
            })

        # 2. Math Formulas & Equations
        for formula in guide_data.get("math_formulas", []):
            name = formula.get("name", "")
            eq = formula.get("equation", "")
            vars_dict = formula.get("variables", {})
            purpose = formula.get("purpose", "")
            var_lines = "\n".join([f"- `{k}`: {v}" for k, v in vars_dict.items()])
            text = f"### Mathematical Formula: {name}\n**Equation:** $${eq}$$\n\n**Variables:**\n{var_lines}\n\n**Purpose:** {purpose}"
            documents.append({
                "text": text,
                "metadata": {
                    "source_file": "digitalagedu/core/concepts_registry.py",
                    "primary_topic": topic_id,
                    "topics": [topic_id],
                    "chunk_type": "math_formula",
                    "title": name
                }
            })

        # 3. Step-by-Step Implementation Guides
        for step_guide in guide_data.get("step_by_step", []):
            title = step_guide.get("title", "")
            steps = step_guide.get("steps", [])
            step_lines = "\n".join([f"{i+1}. **{s.get('step', '')}**: {s.get('details', '')}" for i, s in enumerate(steps)])
            text = f"### Algorithm / Step-by-Step: {title}\n\n{step_lines}"
            documents.append({
                "text": text,
                "metadata": {
                    "source_file": "digitalagedu/core/concepts_registry.py",
                    "primary_topic": topic_id,
                    "topics": [topic_id],
                    "chunk_type": "algorithm",
                    "title": title
                }
            })

        # 4. Common Pitfalls & Debugging Tips
        for pitfall in guide_data.get("common_pitfalls", []):
            issue = pitfall.get("issue", "")
            why = pitfall.get("why_it_happens", "")
            fix = pitfall.get("fix", "")
            text = f"### Debugging Pitfall: {issue}\n**Why it happens:** {why}\n\n**Fix:** {fix}"
            documents.append({
                "text": text,
                "metadata": {
                    "source_file": "digitalagedu/core/concepts_registry.py",
                    "primary_topic": topic_id,
                    "topics": [topic_id],
                    "chunk_type": "debugging_tip",
                    "title": issue
                }
            })

    # 5. Curated Documentation & Resource Links
    for topic_id, links in RESOURCE_LINKS.items():
        for link in links:
            name = link.get("name", "")
            url = link.get("url", "")
            desc = link.get("description", "")
            text = f"### Resource Reference: {name}\n**URL:** {url}\n**Description:** {desc}"
            documents.append({
                "text": text,
                "metadata": {
                    "source_file": "digitalagedu/core/concepts_registry.py",
                    "primary_topic": topic_id,
                    "topics": [topic_id],
                    "chunk_type": "resource_link",
                    "title": name,
                    "url": url
                }
            })

    return documents


PIPELINE_SOLUTION_TOPICS = {
    "classification": ("transfer_learning", ["transfer_learning", "vector_embeddings", "image_datasets"]),
    "segmentation": ("interactive_segmentation", ["interactive_segmentation", "semantic_segmentation"]),
    "xai": ("explainable_ai", ["explainable_ai", "transfer_learning"]),
}


def collect_pipeline_code_documents() -> List[Dict[str, Any]]:
    """One chunk per top-level function of the pipeline's own DINOv2 / SAM / Grad-CAM stage code."""
    import ast
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "curriculum_resources"))
    documents = []
    for stage, (primary_topic, topics) in PIPELINE_SOLUTION_TOPICS.items():
        rel_path = f"curriculum_resources/{stage}/solution.py"
        source = open(os.path.join(root, stage, "solution.py"), encoding="utf-8").read()
        for node in ast.parse(source).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                code = ast.get_source_segment(source, node)
                documents.append({
                    "text": f"# Phase 1 pipeline ({stage}): {node.name}\n```python\n{code}\n```",
                    "metadata": {
                        "source_file": rel_path,
                        "primary_topic": primary_topic,
                        "topics": topics,
                        "chunk_type": "code",
                        "title": f"Pipeline Code: {stage}.{node.name}"
                    }
                })
    return documents


def collect_notebook_documents() -> List[Dict[str, Any]]:
    """Walks the cloned repository and extracts explanation and code chunks."""
    if not os.path.exists(REFERENCE_REPO_DIR):
        return []

    documents = []

    for root, _, files in os.walk(REFERENCE_REPO_DIR):
        for file in files:
            if file.endswith(".ipynb") and not file.startswith("."):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, REFERENCE_REPO_DIR)
                primary_topic, topics = map_notebook_path_to_topics(rel_path)

                md_cells, code_cells = parse_notebook(filepath)
                if len(DOMAIN_TERMS.findall("\n".join(md_cells + code_cells))) > MAX_DOMAIN_HITS:
                    continue

                # Explanations
                for md in md_cells:
                    if len(md.strip()) < 30:  # Skip trivial cells
                        continue
                    documents.append({
                        "text": md,
                        "metadata": {
                            "source_file": rel_path,
                            "primary_topic": primary_topic,
                            "topics": topics,
                            "chunk_type": "explanation",
                            "title": f"Notebook Explanation: {os.path.basename(rel_path)}"
                        }
                    })

                # Code Blocks
                for code in code_cells:
                    if len(code.strip()) < 20:  # Skip trivial code cells
                        continue
                    documents.append({
                        "text": f"```python\n{code}\n```",
                        "metadata": {
                            "source_file": rel_path,
                            "primary_topic": primary_topic,
                            "topics": topics,
                            "chunk_type": "code",
                            "title": f"PyTorch Code: {os.path.basename(rel_path)}"
                        }
                    })

    return documents


# Domain-agnostic concept sources: general CV / ML / foundation-model docs and examples.
# `checkout` = sparse-checkout folders (repo-root files like README.md are always present);
# `include` = files or folders to ingest. Folders holding domain applications are left out.
CONCEPT_SOURCES = [
    {
        "name": "scikit-image", "url": "https://github.com/scikit-image/scikit-image.git", "license": "BSD-3-Clause",
        "checkout": ["doc/examples"],
        "include": [f"doc/examples/{d}" for d in ("color_exposure", "features_detection", "segmentation", "filters", "edges")],
        "primary_topic": "image_analysis", "topics": ["image_analysis", "image_datasets", "numpy_basics"],
    },
    {
        "name": "scikit-learn", "url": "https://github.com/scikit-learn/scikit-learn.git", "license": "BSD-3-Clause",
        "checkout": ["examples"],
        "include": [f"examples/{d}" for d in (
            "classification", "svm", "ensemble", "model_selection", "manifold", "decomposition", "preprocessing", "inspection"
        )],
        "primary_topic": "classical_ml", "topics": ["classical_ml", "vector_embeddings", "pandas_analytics"],
    },
    {
        "name": "segment-anything", "url": "https://github.com/facebookresearch/segment-anything.git", "license": "Apache-2.0",
        "checkout": ["notebooks"],
        "include": ["README.md", "notebooks/predictor_example.ipynb", "notebooks/automatic_mask_generator_example.ipynb"],
        "primary_topic": "interactive_segmentation", "topics": ["interactive_segmentation", "semantic_segmentation"],
    },
    {
        "name": "dinov2", "url": "https://github.com/facebookresearch/dinov2.git", "license": "Apache-2.0",
        "checkout": ["notebooks"],
        "include": ["README.md", "MODEL_CARD.md", "notebooks/semantic_segmentation.ipynb", "notebooks/depth_estimation.ipynb"],
        "primary_topic": "transfer_learning", "topics": ["transfer_learning", "vector_embeddings"],
    },
    {
        "name": "pytorch-grad-cam", "url": "https://github.com/jacobgil/pytorch-grad-cam.git", "license": "MIT",
        "checkout": ["tutorials"],
        "include": ["README.md", "tutorials"],
        "primary_topic": "explainable_ai", "topics": ["explainable_ai"],
    },
]

# Files built around a specific application domain (medical, socio-economic, ...) are skipped so the
# knowledge base stays domain agnostic. A couple of incidental mentions are tolerated.
DOMAIN_TERMS = re.compile(
    r"breast_cancer|load_diabetes|cancer|tumou?r|patient|histolog|immunohisto|microscop|"
    r"fetch_california|titanic|covtype|wages|bike",
    re.IGNORECASE,
)
MAX_DOMAIN_HITS = 2
MAX_CHUNK_CHARS = 1500


def sparse_clone(source: Dict[str, Any]) -> str:
    """Shallow, blob-filtered sparse clone into reference_repos/<name>. Files are only parsed as text, never run."""
    repo_dir = os.path.join("reference_repos", source["name"])
    if not os.path.exists(repo_dir):
        print(f"[INFO] Cloning {source['url']} ({', '.join(source['checkout'])})...")
        os.makedirs("reference_repos", exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", source["url"], repo_dir], check=True)
    subprocess.run(["git", "-C", repo_dir, "sparse-checkout", "set", *source["checkout"]], check=True)
    return repo_dir


def split_long(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """Splits text at paragraph boundaries so no chunk exceeds max_chars."""
    chunks = []
    text = text.strip()
    while len(text) > max_chars:
        cut = text.rfind("\n\n", 0, max_chars)
        cut = cut if cut > 200 else max_chars
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    return chunks + ([text] if text else [])


def split_markdown(text: str) -> List[str]:
    """Splits Markdown at #, ## and ### headings (ignoring '#' lines inside code fences), then caps chunk size."""
    sections, current, in_fence = [], [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and re.match(r"#{1,3} ", line) and current:
            sections.append("\n".join(current))
            current = []
        current.append(line)
    sections.append("\n".join(current))
    return [c for s in sections for c in split_long(s)]


def parse_gallery_script(text: str) -> tuple[List[str], List[str]]:
    """Splits a sphinx-gallery example (.py) into prose (module docstring + comment blocks) and code cells."""
    prose, code = [], []
    doc = re.match(r'\s*[rR]?("""|\'\'\')(.*?)\1', text, re.S)
    if doc:
        prose.append(doc.group(2).strip())
        text = text[doc.end():]
    for block in re.split(r"^# ?%%.*$|^#{20,}\s*$", text, flags=re.M):
        lines = block.strip("\n").split("\n")
        i, comments = 0, []
        while i < len(lines) and (lines[i].startswith("#") or not lines[i].strip()):
            comments.append(lines[i].lstrip("#").strip())
            i += 1
        comment_text = "\n".join(c for c in comments if not c.startswith(("Authors:", "SPDX-License"))).strip()
        if comment_text:
            prose.append(comment_text)
        if "\n".join(lines[i:]).strip():
            code.append("\n".join(lines[i:]).strip())
    return prose, code


def collect_concept_source_documents() -> List[Dict[str, Any]]:
    """Clones each CONCEPT_SOURCES repo and turns its examples / docs into explanation and code chunks."""
    documents, skipped = [], []
    for source in CONCEPT_SOURCES:
        repo_dir = sparse_clone(source)
        files = []
        for inc in source["include"]:
            path = os.path.join(repo_dir, inc)
            if os.path.isdir(path):
                files += sorted(os.path.join(r, f) for r, _, fs in os.walk(path) for f in fs)
            elif os.path.isfile(path):
                files.append(path)
            else:
                raise FileNotFoundError(f"{source['name']}: configured path '{inc}' not found in the repository")

        for filepath in files:
            rel_path = os.path.relpath(filepath, repo_dir).replace("\\", "/")
            if filepath.endswith(".ipynb"):
                prose, code = parse_notebook(filepath)
            elif filepath.endswith(".py"):
                prose, code = parse_gallery_script(open(filepath, encoding="utf-8").read())
            elif filepath.endswith(".md"):
                prose, code = split_markdown(open(filepath, encoding="utf-8").read()), []
            else:
                continue
            if len(DOMAIN_TERMS.findall("\n".join(prose + code))) > MAX_DOMAIN_HITS:
                skipped.append(f"{source['name']}/{rel_path}")
                continue

            base = {
                "source_file": f"{source['name']}/{rel_path}",
                "source_url": source["url"].removesuffix(".git"),
                "license": source["license"],
                "primary_topic": source["primary_topic"],
                "topics": source["topics"],
            }
            for text in (c for p in prose for c in split_long(p)):
                if len(text) >= 30:
                    documents.append({"text": text, "metadata": {**base, "chunk_type": "explanation",
                                                                 "title": f"{source['name']}: {rel_path}"}})
            for text in code:
                if len(text) >= 20:
                    documents.append({"text": f"```python\n{text}\n```", "metadata": {**base, "chunk_type": "code",
                                                                                     "title": f"{source['name']} code: {rel_path}"}})
    if skipped:
        print(f"  -> Skipped {len(skipped)} domain-specific files: {', '.join(skipped)}")
    return documents


def run_migration(
    endpoint: str = DEFAULT_QDRANT_ENDPOINT,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    api_key: str = None,
    batch_size: int = 64
):
    """Executes end-to-end extraction, vectorization, and Qdrant batch upsert."""
    api_key = api_key or os.getenv("TAPIS_JWT") or os.getenv("QDRANT_API_KEY") or DEFAULT_POD_API_KEY

    print("=================================================================")
    print("      DigitalAgEdu ICICLE Qdrant Ingestion & Seeding Engine      ")
    print("=================================================================")
    print(f"Target Pod Endpoint: {endpoint}")
    print(f"Collection Name:     {collection_name}")
    print(f"Embedding Model:     {DEFAULT_EMBEDDING_MODEL} (384 dimensions)")
    print(f"Batch Size:          {batch_size}")
    print("=================================================================\n")

    # 1. Connect to Qdrant Pod
    client = QdrantRAGClient(
        endpoint=endpoint,
        collection_name=collection_name,
        api_key=api_key,
        exit_on_failure=True
    )

    print("[Step 1/5] Checking Qdrant Pod Health...")
    client.check_health()
    print("  -> Pod is online and responsive.")

    print("[Step 2/5] Initializing Target Collection...")
    client.ensure_collection(collection_name=collection_name, vector_size=384)
    print(f"  -> Collection '{collection_name}' ready.")

    print("[Step 3/5] Gathering Knowledge Base Chunks...")
    clone_reference_repo_if_needed()
    concept_docs = collect_concept_registry_documents()
    print(f"  -> Extracted {len(concept_docs)} chunks from Concept Registry.")
    notebook_docs = collect_notebook_documents()
    print(f"  -> Extracted {len(notebook_docs)} chunks from Reference Notebooks.")
    pipeline_docs = collect_pipeline_code_documents()
    print(f"  -> Extracted {len(pipeline_docs)} chunks from Phase 1 pipeline code.")
    source_docs = collect_concept_source_documents()
    print(f"  -> Extracted {len(source_docs)} chunks from domain-agnostic concept sources.")

    all_docs = concept_docs + notebook_docs + pipeline_docs + source_docs
    print(f"  -> Total Chunks to Ingest: {len(all_docs)}")

    if not all_docs:
        print("[ERROR] No chunks collected. Aborting ingestion.")
        return

    # Full rebuild: drop every knowledge chunk (visual recipes are seeded separately and kept) so that
    # edited or newly filtered-out content does not linger under stale ids. Runs only after collection succeeded.
    client.client.delete(
        collection_name=collection_name,
        points_selector=models.FilterSelector(filter=models.Filter(must_not=[
            models.FieldCondition(key="chunk_type", match=models.MatchValue(value="presentation_recipe"))
        ])),
        wait=True,
    )
    print("  -> Cleared previous knowledge chunks (visual recipes kept).")

    print("[Step 4/5] Loading SentenceTransformer Embedding Model...")
    embedder = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
    print("  -> Embedding model loaded.")

    print("[Step 5/5] Generating Dense Embeddings and Upserting in Batches...")
    total_upserted = 0

    for i in range(0, len(all_docs), batch_size):
        batch = all_docs[i : i + batch_size]
        texts = [doc["text"] for doc in batch]

        # Generate 384d vector embeddings
        embeddings = embedder.encode(texts, convert_to_numpy=True).tolist()

        # Build Qdrant PointStruct items
        points = []
        for doc, emb in zip(batch, embeddings):
            # Deterministic id so re-running the migration overwrites instead of duplicating
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc['metadata']['source_file']}::{doc['text']}"))
            payload = {
                "text": doc["text"],
                **doc["metadata"]
            }
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload
                )
            )

        # Upsert into Qdrant Pod
        client.client.upsert(
            collection_name=collection_name,
            points=points
        )

        total_upserted += len(points)
        print(f"  -> Upserted {total_upserted}/{len(all_docs)} points ({(total_upserted/len(all_docs))*100:.1f}%)")

    print("\n=================================================================")
    print(f"[SUCCESS] Ingestion Complete! Successfully seeded {total_upserted} vector points.")
    print("=================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest curriculum knowledge into ICICLE Qdrant Pod")
    parser.add_argument("--endpoint", type=str, default=DEFAULT_QDRANT_ENDPOINT, help="Qdrant pod endpoint URL")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION_NAME, help="Qdrant collection name")
    parser.add_argument("--api-key", type=str, default=None, help="Tapis JWT or Qdrant Pod API Key")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for embedding and upserting")
    args = parser.parse_args()

    run_migration(
        endpoint=args.endpoint,
        collection_name=args.collection,
        api_key=args.api_key,
        batch_size=args.batch_size
    )
