import os
import json
import subprocess
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

import chromadb
from chromadb.utils import embedding_functions

# Directories & Settings
REPO_URL = "https://github.com/rasbt/deeplearning-models.git"
REPO_DIR = os.path.join("reference_repos", "deeplearning-models")
DB_DIR = "./chroma_db"

def clone_reference_repo():
    """Clones rasbt/deeplearning-models if not already downloaded locally."""
    if not os.path.exists(REPO_DIR):
        print(f"Cloning {REPO_URL} into '{REPO_DIR}'...")
        os.makedirs("reference_repos", exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, REPO_DIR], check=True)
    else:
        print(f"Reference repository found at '{REPO_DIR}'.")

def parse_notebook_cells(filepath: str):
    """Extracts Markdown text cells and Python code cells from a .ipynb file."""
    with open(filepath, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    markdown_cells = []
    code_cells = []

    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", [])).strip()

        if not source:
            continue

        if cell_type == "markdown":
            markdown_cells.append(source)
        elif cell_type == "code":
            code_cells.append(source)

    return markdown_cells, code_cells

def build_vector_index():
    """Reads all notebooks and stores embeddings in a local persistent ChromaDB."""
    clone_reference_repo()

    # 1. Initialize persistent local disk database
    client = chromadb.PersistentClient(path=DB_DIR)

    # 2. Use local sentence-transformers CPU embedding model
    embedding_fn = cast(
        Any,
        embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    )

    # 3. Create or fetch collection
    collection = client.get_or_create_collection(
        name="rasbt_models_rag",
        embedding_function=embedding_fn
    )

    documents = []
    metadatas = []
    ids = []

    doc_counter = 0

    # 4. Walk through all .ipynb notebook files
    for root, _, files in os.walk(REPO_DIR):
        for file in files:
            if file.endswith(".ipynb") and not file.startswith("."):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, REPO_DIR)
                
                md_cells, code_cells = parse_notebook_cells(filepath)

                # Add Markdown explanation cells
                for idx, text in enumerate(md_cells):
                    doc_counter += 1
                    documents.append(text)
                    metadatas.append({"file": rel_path, "type": "explanation"})
                    ids.append(f"doc_{doc_counter}")

                # Add Python code cells
                for idx, code in enumerate(code_cells):
                    doc_counter += 1
                    documents.append(f"```python\n{code}\n```")
                    metadatas.append({"file": rel_path, "type": "code"})
                    ids.append(f"doc_{doc_counter}")

    # 5. Batch add to ChromaDB
    print(f"Indexing {len(documents)} total notebook chunks into ChromaDB...")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Done! Persistent vector database saved to '{DB_DIR}'.")

if __name__ == "__main__":
    build_vector_index()
