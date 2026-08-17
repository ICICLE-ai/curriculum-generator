import os
import re
import logging

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["CC"] = "gcc"
os.environ["CXX"] = "g++"
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

try:
    import torch
    torch.set_num_threads(2)
except Exception:
    pass

from typing import Dict, Any, Optional
from digitalagedu.core.llm.schemas import Module, ValidatedExerciseSchema, SlideDeckSchema
from digitalagedu.core.llm.rag.qdrant_client import QdrantRAGClient

_cached_qdrant_client = None

def _get_qdrant_client() -> Optional[QdrantRAGClient]:
    """Lazy-loads QdrantRAGClient singleton for vector retrieval."""
    global _cached_qdrant_client
    if _cached_qdrant_client is None:
        try:
            _cached_qdrant_client = QdrantRAGClient(
                endpoint=os.getenv("QDRANT_ENDPOINT"),
                collection_name=os.getenv("QDRANT_COLLECTION", "digitalagedu_rag_knowledge"),
                api_key=os.getenv("TAPIS_JWT") or os.getenv("QDRANT_API_KEY"),
                exit_on_failure=False,
                timeout=10.0
            )
        except Exception as e:
            logging.warning(f"Could not initialize QdrantRAGClient: {e}")
            _cached_qdrant_client = None
    return _cached_qdrant_client

STOP_WORDS = {
    "a", "an", "the", "in", "on", "of", "for", "to", "and", "or", "is", "are", "with", 
    "this", "that", "it", "by", "from", "at", "as", "be", "introduction", "basics", 
    "module", "week", "overview", "understanding", "creating", "building", "implementing"
}

def _extract_query_keywords(text: str) -> str:
    """Extracts dense technical keywords from titles and context strings for vector retrieval."""
    words = re.findall(r'\b[A-Za-z0-9_]+\b', text)
    keywords = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 1]
    return " ".join(keywords)

def get_rag_context(
    query_text: str,
    n_results: int = 2,
    topic: Optional[str] = None,
    chunk_type: Optional[str] = None,
    max_distance: float = 1.35,
    rerank: bool = False
) -> str:
    """
    Retrieves grounded context snippets from the ICICLE Qdrant Vector Cloud.
    """
    qdrant = _get_qdrant_client()
    if qdrant is None:
        return ""

    try:
        matches = qdrant.query_similar(
            query_text=query_text,
            top_k=n_results * 2 if rerank else n_results,
            topic=topic,
            chunk_type=chunk_type,
            rerank=rerank,
            top_n=n_results
        )
        if not matches:
            return ""

        formatted_snippets = []
        for m in matches:
            src = m.get("source_file", "knowledge_base")
            c_type = m.get("chunk_type", "snippet")
            score = m.get("score", 0.0)
            r_score = m.get("rerank_score")
            score_str = f"Score: {score:.2f}" if r_score is None else f"Rerank: {r_score:.2f}"
            formatted_snippets.append(
                f"[Reference: {src} | Type: {c_type} | {score_str}]\n{m.get('text', '')}"
            )
        res_str = "\n\n".join(formatted_snippets)
        if len(res_str) > 3000:
            res_str = res_str[:3000] + "\n...[truncated context]"
        return res_str
    except Exception as e:
        logging.warning(f"Qdrant vector retrieval failed: {e}")
        return ""

def build_system_prompt() -> str:
    return (
        "You are an expert deep learning educator.\n"
        "Generate curriculum content following Bloom's Taxonomy and ABET outcomes.\n"
        "CRITICAL CODE RULES:\n"
        "1. Every `solution_code` and `unit_test` string MUST be a fully self-contained, valid Python script.\n"
        "2. ALWAYS include all necessary module imports at the very top of `solution_code` and `unit_test` (e.g., `import torch`, `import torch.nn as nn`, `import torch.nn.functional as F`).\n"
        "3. All generated PyTorch code must execute cleanly without SyntaxError, NameError, or AttributeError.\n"
        "4. In `unit_test`, test the classes/functions defined in `solution_code` directly in memory. NEVER use placeholder imports (e.g. `from your_module import ...`) or load non-existent files (`torch.load('path...')`).\n"
        "5. In `unit_test`, pass a dummy tensor into the model and assert that the output tensor shape matches expectation.\n"
        "6. ONLY use standard PyTorch / torchvision model names (e.g., `resnet18`, `resnet50`, `vit_b_16`, `convnext_tiny`). DO NOT invent non-existent model names like `vit_base_patch16_224`.\n"
        "7. NEVER attempt to open or load non-existent disk files (e.g., `Image.open()`, `open()`, `cv2.imread()`). ALWAYS create synthetic in-memory dummy tensors in `unit_test`.\n"
        "8. DOMAIN-AGNOSTIC TENSOR DIMENSION CONTRACT: Match synthetic input tensor rank to the target model's input layer (e.g. 2D `[N, F]` for Linear/Tabular, 3D `[N, L, F]` for NLP/Transformers, 4D `[N, C, H, W]` for 2D Vision, 5D `[N, C, D, H, W]` for Video/3D Medical). ALWAYS set batch size N >= 2 (e.g. N=4) to ensure compatibility with BatchNorm layers, and ensure `unit_test` inputs already include the batch dimension so `forward()` never calls unnecessary `unsqueeze()` operations.\n"
        "9. PYTORCH ATTRIBUTION & HOOK CONTRACT: When implementing feature attribution or layer hooks (e.g. Grad-CAM, Attention maps, Activation extraction), ALWAYS: (1) set `input_tensor.requires_grad_(True)` before model forward pass if computing gradients, (2) define hook function `def backward_hook(module, grad_in, grad_out): self.gradients = grad_out[0]`, (3) register hook with `target_layer.register_full_backward_hook(backward_hook)`, and (4) verify `self.gradients is not None` before computing channel or spatial reductions.\n"
        "10. PROPERTY-BASED HARNESS RULE: In `unit_test`, write invariant test harnesses that test multi-shape batch resilience (`for batch_size in [2, 4]:`) and verify numerical invariants (`assert not torch.isnan(output).any()`). Avoid weak/trivial assertions.\n"
        "11. TORCHVISION IMPORT CONTRACT: Import torchvision models and weights directly from `torchvision.models` (e.g. `from torchvision.models import vit_b_16, ViT_B_16_Weights`). NEVER import from non-existent submodules like `torchvision.models.vit`.\n"
        "12. PYTORCH TENSOR MAX CONTRACT: `tensor.max()` does NOT accept a tuple for `dim` (e.g. `tensor.max(dim=(1, 2))` is invalid and raises TypeError). To find max/min over multiple dimensions, ALWAYS use `torch.amax(tensor, dim=(1, 2), keepdim=True)` or `torch.flatten(tensor, start_dim=1).max(dim=1, keepdim=True)[0]`.\n"
    )

def build_slide_prompt(module: Module, problem_formulation: Optional[Any] = None) -> str:
    keywords = _extract_query_keywords(f"{module.title} {module.context}")
    rag_context = get_rag_context(keywords, n_results=2, topic=module.id, chunk_type="explanation", max_distance=1.35, rerank=True)

    prompt = (
        f"Generate presentation slides for module '{module.title}' (Week {module.week}).\n"
        f"Context: {module.context}\n"
        f"Difficulty: {module.difficulty}\n"
    )
    if problem_formulation:
        prompt += (
            f"\n--- DOMAIN PROBLEM FORMULATION (AGENT 0) ---\n"
            f"Title: {problem_formulation.title}\n"
            f"Domain Context: {problem_formulation.domain_context}\n"
            f"Problem Statement: {problem_formulation.problem_statement}\n"
            f"Suggested Focus: {problem_formulation.suggested_focus}\n"
        )
    if rag_context:
        prompt += f"\n--- GROUNDED REFERENCE CONTEXT ---\n{rag_context}\n"

    prompt += (
        "\nCreate a slide deck with a title slide and 3-5 content slides. "
        "Each content slide must contain 3-4 bullet points explaining concepts and optional PyTorch code snippets."
    )
    return prompt

def build_exercise_prompt(module: Module, slide_deck: Optional[SlideDeckSchema] = None, problem_formulation: Optional[Any] = None) -> str:
    keywords = _extract_query_keywords(f"{module.title} {module.context}")
    rag_context = get_rag_context(keywords, n_results=2, topic=module.id, chunk_type="code", max_distance=1.35, rerank=True)

    prompt = (
        f"Generate a PyTorch exercise for module '{module.title}' (Week {module.week}).\n"
        f"Context: {module.context}\n"
        f"Difficulty: {module.difficulty}\n"
    )
    if problem_formulation:
        prompt += (
            f"\n--- AGENT 0 DOMAIN PROBLEM DIRECTIVE ---\n"
            f"Title: {problem_formulation.title}\n"
            f"Domain Context: {problem_formulation.domain_context}\n"
            f"Problem Directive: {problem_formulation.problem_statement}\n"
            f"Target Input Shape: {problem_formulation.target_input_shape}\n"
            f"Target Output Shape: {problem_formulation.target_output_shape}\n"
            f"Suggested Focus: {problem_formulation.suggested_focus}\n"
        )
    if rag_context:
        prompt += f"\n--- GROUNDED PYTORCH CODE TEMPLATES ---\n{rag_context}\n"
    if slide_deck:
        prompt += f"\n--- SLIDE DECK TOPICS ---\nTitle: {slide_deck.deck_title}\nSlides: {[s.title for s in slide_deck.slides]}\n"

    return prompt

def build_qa_prompt(module: Module, solution_code: str, problem_formulation: Optional[Any] = None) -> str:
    clean_id = module.id.replace("-", "_")
    solution_module_name = f"{clean_id}_solution"
    prompt = (
        f"You are an expert QA Software Test Engineer.\n"
        f"Generate a property-based testing harness for the following PyTorch reference solution in module '{module.title}'.\n\n"
    )
    if problem_formulation:
        prompt += (
            f"--- DOMAIN CONTRACTS ---\n"
            f"Target Input Shape: {problem_formulation.target_input_shape}\n"
            f"Target Output Shape: {problem_formulation.target_output_shape}\n\n"
        )
    prompt += (
        f"--- REFERENCE SOLUTION CODE ---\n{solution_code}\n\n"
        f"QA HARNESS REQUIREMENTS:\n"
        f"1. SOLUTION IMPORT: Include `from {solution_module_name} import *` at the top of `unit_test` so tests can import solution classes/functions when executed standalone.\n"
        f"2. PROGRAMMATIC MULTI-SHAPE FUZZING: In `unit_test`, iterate over a small loop of varying batch sizes (e.g. `for batch_size in [2, 4]:`) to verify model output shapes remain dynamically resilient.\n"
        f"3. PROPERTY-BASED INVARIANT HARNESSING: Do NOT rely solely on trivial assertions. Assert mathematical invariants:\n"
        f"   a. Shape Contracts: Assert exact output tensor shapes across varying batch sizes.\n"
        f"   b. Numerical & Gradient Integrity: Assert no `NaN` or `Inf` values exist in output or gradients (`assert not torch.isnan(output).any()`).\n"
        f"   c. Value Bounds: Assert output ranges match mathematical expectations (e.g. Softmax sums to 1.0, Sigmoid in [0, 1]).\n"
        f"4. SELF-CONTAINED EXECUTION: Include all required top-level imports (`import torch`, `import torch.nn as nn`, `import torch.nn.functional as F`).\n"
    )
    return prompt
