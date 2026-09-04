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

from typing import Dict, Any, Optional, List
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
                api_key=os.getenv("TAPIS_REFRESH_TOKEN") or os.getenv("TAPIS_JWT") or os.getenv("TAPIS_TOKEN") or os.getenv("QDRANT_API_KEY"),
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
        "You are an expert AI & Computing Educator.\n"
        "Your task is to design robust, engaging, production-grade hands-on laboratory exercises and reference implementations.\n"
        "CORE PEDAGOGICAL & ARCHITECTURAL PRINCIPLES:\n"
        "1. DOMAIN & MODALITY IDIOMATIC: Select standard, idiomatic Python libraries and tools that naturally align with the problem domain, task modality, and student target level. Do not force deep learning architectures or neural networks unless the module learning objectives specifically call for them.\n"
        "2. SUBSYSTEM MILESTONE ENGINEERING: Implement the exercise as a multi-stage mini-project structured into 3 distinct, cohesive functional subsystems (each containing cooperating classes, functions, or data structures), unified by an overarching `run_pipeline(...)` orchestrator function.\n"
        "3. PRODUCTION QUALITY & SCALE: Deliver a complete, rich reference implementation of roughly 150-250 lines of Python code, complete with clear docstrings, realistic logic, and an end-to-end execution demonstration under `if __name__ == '__main__':`.\n"
        "4. DUAL-MODE DATA LOADING PATTERN: When accessing dataset files, use relative paths (e.g., `../../../images/dataset_sample`, `../../../results.csv`) wrapped in `if os.path.exists(...): ... else: ...` with a synthetic in-memory fallback. NEVER call unconditional disk-loading functions that crash if a path is absent.\n"
        "5. STRICT IMPORT HYGIENE: Explicitly declare all library and module imports at the very top of the script (e.g. if you call a submodule function or alias, you must explicitly import it at the top, such as `import math` or `from collections import defaultdict`).\n"
        "6. SYNTACTIC INTEGRITY: All Python code, string literals, and test assertions must be syntactically valid with properly closed quotes and brackets.\n"
        "7. RUNTIME ENVIRONMENT COMPATIBILITY: Do NOT import uninstalled deep learning frameworks such as `tensorflow`, `keras`, `jax`, or `mxnet`. Ensure all code only uses standard installed scientific computing packages. Avoid external network calls or blocking GUI popups (e.g., call `plt.close()` or `plt.savefig()` instead of `plt.show()`).\n"
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
        "Each content slide must contain 3-4 bullet points explaining concepts and optional code snippets."
    )
    return prompt

def build_qa_prompt(module: Module, problem_formulation: Any) -> str:
    """TDD Step 1: Generates property-based unit tests asserting the milestone subsystem contracts before solution code exists."""
    clean_id = module.id.replace("-", "_")
    solution_module_name = f"{clean_id}_solution"
    
    subsystems_text = ""
    if getattr(problem_formulation, "milestone_subsystems", None):
        subsystems_text = "--- SUBSYSTEM COMPONENT CONTRACTS TO TEST ---\n"
        for sub in problem_formulation.milestone_subsystems:
            subsystems_text += f"\n[Milestone {sub.milestone_num}: {sub.title}] - Objective: {sub.objective}\n"
            for comp in sub.components:
                subsystems_text += f"  * {comp.kind.upper()} `{comp.name}`:\n"
                subsystems_text += f"    Signature: `{comp.signature}`\n"
                subsystems_text += f"    Description: {comp.description}\n"
    
    orchestrator_sig = getattr(problem_formulation, "pipeline_orchestrator_signature", "def run_pipeline() -> dict:")
    orchestrator_call = orchestrator_sig.split("(")[0].replace("def ", "").strip()

    prompt = (
        f"You are an expert QA Software Test Engineer.\n"
        f"Write a comprehensive property-based unit test harness for the mini-project in module '{module.title}' (Week {module.week}).\n\n"
        f"Directives: {module.context}\n"
        f"Difficulty: {module.difficulty}\n\n"
        f"{subsystems_text}\n"
        f"Overarching Pipeline Orchestrator: `{orchestrator_sig}`\n\n"
        f"QA HARNESS REQUIREMENTS:\n"
        f"1. SOLUTION IMPORT: Include `from {solution_module_name} import *` at the very top of `unit_test`.\n"
        f"2. TEST EACH SUBSYSTEM: Write dedicated test functions verifying each milestone component defined in the contract above.\n"
        f"3. TEST OVERARCHING PIPELINE: Include a test function executing `{orchestrator_call}()` on synthetic in-memory test data to verify the entire pipeline runs end-to-end.\n"
        f"4. IN-MEMORY SYNTHETIC INPUTS: Generate realistic in-memory dummy inputs (synthetic arrays, sample dictionaries, or tensors) directly inside test functions. Never attempt to read files from disk.\n"
        f"5. PROPERTY-BASED ASSERTIONS: Assert structural, mathematical, and invariant properties:\n"
        f"   - Check return types, shapes, and dictionary keys.\n"
        f"   - Check that numerical outputs are finite (no NaN or Inf).\n"
        f"   - Fuzz across multiple inputs or batch sizes where applicable (e.g. `for batch_size in [2, 4]:`).\n"
        f"6. SYNTAX HYGIENE: Ensure all assertion error message f-strings have properly closed quotation marks.\n"
        f"7. SELF-CONTAINED EXECUTION: Call all test functions under `if __name__ == '__main__':` and print 'All tests passed!'.\n"
        f"8. RUNTIME ENVIRONMENT: The container execution environment has standard scientific Python libraries available (`scipy`, `scikit-learn`, `scikit-image`, `matplotlib`, and `torch` / `torchvision` when deep learning is required). Never import `tensorflow` or `keras`.\n"
    )
    return prompt

def build_exercise_prompt(
    module: Module,
    problem_formulation: Any,
    unit_test_code: Optional[str] = None,
    curriculum_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """TDD Step 2: Generates reference solution targeted directly at passing the unit tests and implementing the subsystems."""
    keywords = _extract_query_keywords(f"{module.title} {module.context}")
    rag_context = get_rag_context(keywords, n_results=2, topic=module.id, chunk_type="code", max_distance=1.35, rerank=True)

    history_text = ""
    if curriculum_history:
        history_text = "\n--- PRECEDING COURSE CONTEXT (WHAT STUDENTS ALREADY BUILT) ---\n"
        for item in curriculum_history:
            history_text += f"* Week {item.get('week')}: {item.get('title')} - Implemented: {', '.join(item.get('components', []))}\n"
        history_text += "DIRECTIVE: Build naturally upon the students' foundation without repeating basics.\n\n"

    subsystems_text = ""
    if getattr(problem_formulation, "milestone_subsystems", None):
        subsystems_text = "\n--- SUBSYSTEM SPECIFICATIONS TO IMPLEMENT ---\n"
        for sub in problem_formulation.milestone_subsystems:
            subsystems_text += f"\n[Milestone {sub.milestone_num}: {sub.title}]\n"
            for comp in sub.components:
                subsystems_text += f"  - {comp.kind} `{comp.name}`: `{comp.signature}`\n    {comp.description}\n"

    orchestrator_sig = getattr(problem_formulation, "pipeline_orchestrator_signature", "def run_pipeline() -> dict:")

    test_context = ""
    if unit_test_code:
        test_context = (
            f"\n--- QA UNIT TESTS YOUR SOLUTION MUST PASS (TEST-DRIVEN DEVELOPMENT) ---\n"
            f"```python\n{unit_test_code}\n```\n\n"
            f"TDD DIRECTIVE: Your reference solution MUST define all classes and functions imported and asserted in the unit tests above, matching their exact signatures and behavior.\n"
        )

    prompt = (
        f"Generate a substantive, complete Python reference solution for the mini-project in module '{module.title}' (Week {module.week}).\n"
        f"Context: {module.context}\n"
        f"Difficulty: {module.difficulty}\n"
        f"{history_text}"
        f"\n--- DOMAIN PROBLEM DIRECTIVE ---\n"
        f"Title: {problem_formulation.title}\n"
        f"Domain Context: {problem_formulation.domain_context}\n"
        f"Problem Directive: {problem_formulation.problem_statement}\n"
        f"Suggested Focus: {problem_formulation.suggested_focus}\n"
        f"{subsystems_text}\n"
        f"Overarching Pipeline Function: `{orchestrator_sig}`\n"
        f"{test_context}"
    )
    if rag_context:
        prompt += f"\n--- GROUNDED REFERENCE CODE TEMPLATES ---\n{rag_context}\n"

    prompt += (
        "\nIMPLEMENTATION REQUIREMENTS:\n"
        "1. Complete Reference Solution (150-250 lines): Implement all 3 milestone subsystems and the overarching pipeline orchestrator function.\n"
        "2. Exact Signature Alignment: The solution must define all component classes and functions specified in the subsystems contract and required by the unit tests.\n"
        "3. Top-Level Execution Demo: Under `if __name__ == '__main__':`, create synthetic in-memory data or load local sample data, execute the pipeline, and print a formatted execution summary.\n"
        "4. Dual-Mode Data Access Pattern: When accessing lab assets (`../../../images/dataset_sample`, `../../../results.csv`), wrap disk loading in `if os.path.exists(path): ...` and provide a synthetic in-memory fallback (`else: ...`) so code runs seamlessly both with real assets and in isolated test runners.\n"
        "5. Explicit Imports: Put all needed imports at the very top of the script.\n"
        "6. Runtime Environment: The container execution environment has standard scientific Python libraries available (`scipy`, `scikit-learn`, `scikit-image`, `matplotlib`, and `torch` / `torchvision` when deep learning is required). Never import `tensorflow` or `keras`.\n"
    )
    return prompt

def build_scaffold_prompt(module: Module, problem_formulation: Any, solution_code: str) -> str:
    """TDD Step 3: Derives student starter skeleton with multi-step TODO guidance directly from verified working solution."""
    prompt = (
        f"You are an expert computing educator designing a student starter exercise for module '{module.title}' (Week {module.week}).\n"
        f"Problem Directive: {problem_formulation.problem_statement}\n\n"
        f"--- VERIFIED REFERENCE SOLUTION CODE ---\n```python\n{solution_code}\n```\n\n"
        f"SCAFFOLDING DIRECTIVES:\n"
        f"1. Create the student starter code (`starter_code`) based directly on the verified reference solution above.\n"
        f"2. Keep all imports, class skeletons, method headers, type hints, docstrings, and the `if __name__ == '__main__':` demo intact.\n"
        f"3. In each milestone subsystem, replace the internal algorithmic logic with structured `# Step 1`, `# Step 2` TODO comments guiding students on what to implement (requiring approximately 70-120 lines of student implementation work).\n"
        f"4. Ensure the starter code runs without syntax errors (use `pass` or raise `NotImplementedError('TODO: Student implementation')` inside skeleton functions/methods).\n"
    )
    return prompt

def build_presentation_payload(
    module: Module,
    problem_formulation: Any,
    solution_code: Optional[str] = None,
    telemetry: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Constructs a rich, domain-grounded payload for native 16:9 presentation generation.
    Bridges domain problems with computing concepts, real telemetry, and modular software architecture.
    """
    title = getattr(problem_formulation, "title", None) or module.title
    domain_ctx = getattr(problem_formulation, "domain_context", None) or module.context
    problem_stmt = getattr(problem_formulation, "problem_statement", None) or ""
    objectives = getattr(problem_formulation, "learning_objectives", []) or []
    target_in = getattr(problem_formulation, "target_input_shape", None) or "Dataset / Input Features"
    target_out = getattr(problem_formulation, "target_output_shape", None) or "Evaluation / Diagnostic Report"
    focus = getattr(problem_formulation, "suggested_focus", None) or "Data Analysis & Computing Foundations"

    # 1. Format Telemetry Metrics & Contrastive Cases
    telemetry_summary = ""
    contrastive_summary = ""
    if telemetry:
        run_sum = telemetry.get("run_summary", {})
        acc = run_sum.get("overall_accuracy") or run_sum.get("accuracy")
        total_imgs = run_sum.get("total_images") or run_sum.get("total_samples")
        classes = telemetry.get("class_mapping", {})
        if classes:
            class_str = ", ".join(list(classes.values())[:6])
            telemetry_summary += f"- **Dataset Classes:** {class_str}\n"
        if total_imgs is not None:
            telemetry_summary += f"- **Dataset Size:** {total_imgs} authentic images\n"
        if acc is not None:
            telemetry_summary += f"- **Phase 1 Baseline Accuracy:** {acc}%\n"

        contrastive = telemetry.get("contrastive_samples", {})
        if contrastive:
            top_succ = contrastive.get("top_success")
            hard_fail = contrastive.get("hard_failure")
            if top_succ:
                contrastive_summary += f"- **High-Confidence Match:** `{top_succ.get('image_path', 'sample.jpg')}` (Classified correctly as {top_succ.get('ground_truth', 'Target')})\n"
            if hard_fail:
                contrastive_summary += f"- **Diagnostic Failure Mode:** `{hard_fail.get('image_path', 'failure.jpg')}` (True: {hard_fail.get('ground_truth')}, Predicted: {hard_fail.get('predicted_class')})\n"

    # 2. Grounded RAG References
    keywords = _extract_query_keywords(f"{module.title} {module.context}")
    rag_context = get_rag_context(keywords, n_results=2, topic=module.id, chunk_type="code", max_distance=1.35, rerank=True)

    # 3. Clean Reference Solution Snippet
    clean_code = ""
    if solution_code:
        code_lines = [l for l in solution_code.strip().split("\n") if not l.startswith('"""') and not l.startswith("'''")]
        clean_code = "\n".join(code_lines[:25])

    # 4. Synthesize Full Content Field
    content = (
        f"# {title} (Week {module.week})\n\n"
        f"## Domain Context & Background\n"
        f"{domain_ctx}\n\n"
        f"## Real-World Problem Directive\n"
        f"{problem_stmt}\n\n"
        f"## Computational Principles & Subsystem Design\n"
        f"- Target Input Contract: `{target_in}`\n"
        f"- Target Output Contract: `{target_out}`\n"
        f"- Core Focus: {focus}\n"
        f"- Learning Objectives: {', '.join(objectives) if objectives else 'Practical computing literacy'}\n\n"
    )
    if telemetry_summary:
        content += f"## Pipeline Execution Telemetry\n{telemetry_summary}\n"
    if contrastive_summary:
        content += f"## Case Studies & Error Analysis\n{contrastive_summary}\n"
    if rag_context:
        content += f"## Technical Knowledge Grounding\n{rag_context}\n"

    # 5. Synthesize Structured Slide Markdown
    slides_md = [
        (
            f"# {title}\n"
            f"- **Course Module:** DigitalAgEdu Educational Suite (Week {module.week})\n"
            f"- **Domain Application:** {domain_ctx}\n"
            f"- **Difficulty Level:** {module.difficulty.title()}"
        ),
        (
            f"# Real-World Domain Challenge: {title}\n"
            f"- **Problem Directive:** {problem_stmt}\n"
            f"{telemetry_summary.strip() if telemetry_summary else '- **Data Context:** Authentic domain dataset processing'}\n"
            f"- **Goal:** Apply computational techniques to analyze data and address core domain challenges"
        ),
        (
            f"# Computational Principles & Subsystem Design\n"
            f"- **Input/Output Contract:** `{target_in}` → `{target_out}`\n"
            f"- **Core Technique:** {focus}\n"
            f"- **Learning Outcomes:**\n" + "\n".join([f"  * {obj}" for obj in objectives[:3]])
        )
    ]

    if clean_code:
        slides_md.append(
            f"# Reference Solution Architecture & Implementation\n"
            f"```python\n{clean_code}\n```\n"
            f"- Clean modular implementation adhering to subsystem contracts\n"
            f"- Structured for end-to-end execution and reproducibility"
        )

    if contrastive_summary:
        slides_md.append(
            f"# Model Evaluation & Diagnostic Case Studies\n"
            f"- **Error Distribution & Real-World Impact:**\n"
            f"{contrastive_summary.strip()}\n"
            f"- **Mitigation Strategy:** Addressing false negatives and subtle decision boundary shifts"
        )
    else:
        slides_md.append(
            f"# Performance Evaluation & Practical Trade-offs\n"
            f"- Evaluating precision, recall, and loss convergence across training epochs\n"
            f"- Balancing model complexity against inference latency in production environments"
        )

    return {
        "metadata": {
            "title": title,
            "week": module.week,
            "difficulty": module.difficulty,
            "domain_context": domain_ctx,
            "problem_statement": problem_stmt,
            "learning_objectives": objectives,
            "target_input_shape": target_in,
            "target_output_shape": target_out,
            "suggested_focus": focus,
        },
        "solution_code": clean_code or solution_code or "",
        "telemetry": telemetry or {},
        "content": content,
        "slides_markdown": slides_md,
        "n_slides": len(slides_md)
    }

# Backward compatibility alias
build_presenton_payload = build_presentation_payload


