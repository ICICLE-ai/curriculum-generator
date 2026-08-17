import os
from typing import Optional
import instructor
from openai import OpenAI

os.environ["CC"] = "gcc"
os.environ["CXX"] = "g++"

def get_instructor_client(base_url: Optional[str] = None) -> instructor.Instructor:
    """Configures Instructor client targeting local or remote vLLM OpenAI-compatible endpoints."""
    if base_url is None:
        base_url = os.getenv("VLLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "http://localhost:8000/v1"

    raw_client = OpenAI(
        base_url=base_url,
        api_key="none"
    )

    return instructor.from_openai(raw_client, mode=instructor.Mode.JSON)
