"""Checks the knowledge-base parsers in scripts/migrate_rag_to_qdrant.py (pure text parsing, no network)."""
from scripts.migrate_rag_to_qdrant import (
    DOMAIN_TERMS, MAX_DOMAIN_HITS, parse_gallery_script, split_long, split_markdown,
)

GALLERY = '''"""
=============
GLCM Texture
=============
Grey level co-occurrence matrices describe texture.
"""

# Authors: The scikit-image team
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

# %%
# Compute the matrix
# for each patch.
glcm = graycomatrix(patch, [5], [0])
'''


def test_gallery_script_splits_prose_and_code():
    prose, code = parse_gallery_script(GALLERY)
    assert "Grey level co-occurrence" in prose[0]
    assert "Compute the matrix\nfor each patch." in prose
    assert not any("SPDX" in p or "Authors:" in p for p in prose)
    assert code == ["import numpy as np", "glcm = graycomatrix(patch, [5], [0])"]


def test_markdown_split_ignores_hash_lines_in_code_fences():
    md = "# Title\nintro\n```python\n# a comment, not a heading\nx = 1\n```\n## Usage\nrun it"
    chunks = split_markdown(md)
    assert len(chunks) == 2
    assert "# a comment, not a heading" in chunks[0] and chunks[1].startswith("## Usage")


def test_split_long_caps_chunk_size():
    text = "\n\n".join(["word " * 60] * 20)
    assert all(len(c) <= 1500 for c in split_long(text))
    assert "".join(split_long(text)).replace(" ", "").replace("\n", "") == text.replace(" ", "").replace("\n", "")


def test_domain_filter_threshold():
    assert len(DOMAIN_TERMS.findall("load_breast_cancer() ... tumor ... patient")) > MAX_DOMAIN_HITS
    assert len(DOMAIN_TERMS.findall("A generic SVM on the iris dataset")) <= MAX_DOMAIN_HITS
