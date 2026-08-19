"""
DigitalAgEdu Phase 2 Autonomous LLM Curriculum Generation Subpackage
"""

from digitalagedu.core.llm.main import generate_llm_curriculum
from digitalagedu.core.llm.ai_setup import get_instructor_client
from digitalagedu.core.llm.telemetry import load_phase1_telemetry, formulate_problem_statement
from digitalagedu.core.llm.sandbox import run_in_sandbox
from digitalagedu.core.llm.presenton_client import PresentonClient, PresentonGenerationError
from digitalagedu.core.llm.context import get_rag_context, build_presenton_payload
from digitalagedu.core.llm.rag import QdrantRAGClient

__all__ = [
    "generate_llm_curriculum",
    "get_instructor_client",
    "load_phase1_telemetry",
    "formulate_problem_statement",
    "run_in_sandbox",
    "PresentonClient",
    "PresentonGenerationError",
    "build_presenton_payload",
    "get_rag_context",
    "QdrantRAGClient",
]

