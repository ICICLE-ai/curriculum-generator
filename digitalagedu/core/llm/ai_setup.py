import os
import re
from typing import Dict, List, Optional
import instructor
from openai import OpenAI

from digitalagedu.core.llm.sandbox import clean_code_snippet

os.environ["CC"] = "gcc"
os.environ["CXX"] = "g++"

def get_openai_client(base_url: Optional[str] = None) -> OpenAI:
    """Plain OpenAI-compatible client for local or remote vLLM endpoints (used for free-text code replies)."""
    if base_url is None:
        base_url = os.getenv("VLLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "http://localhost:8000/v1"
    return OpenAI(base_url=base_url, api_key="none")

def get_instructor_client(base_url: Optional[str] = None) -> instructor.Instructor:
    """Configures Instructor client targeting local or remote vLLM OpenAI-compatible endpoints."""
    return instructor.from_openai(get_openai_client(base_url), mode=instructor.Mode.JSON)


_CODE_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


def extract_code_block(text: str) -> str:
    """Longest fenced block of a plain-text reply; an unfenced (or unclosed) reply is taken whole."""
    blocks = _CODE_FENCE.findall(text or "")
    return max(blocks, key=len).strip() if blocks else clean_code_snippet(text or "")


def ask_code(code_client, model_name: str, messages: List[Dict[str, str]], what: str,
             max_retries: int = 2, max_tokens: int = 16384) -> str:
    """Plain-text LLM call returning one ```python block. Code never travels inside JSON, so quotes need
    no escaping; replies that are cut off or don't compile are re-asked with the error.
    Extends `messages` in place (ending with the accepted reply) so callers can continue the conversation."""
    messages[-1] = {**messages[-1], "content": (
        f"{messages[-1]['content']}\n\nOUTPUT FORMAT: Reply with the complete {what} as ONE ```python fenced code block and nothing else."
    )}
    for _ in range(1 + max_retries):
        choice = code_client.chat.completions.create(model=model_name, max_tokens=max_tokens, messages=messages).choices[0]
        code = extract_code_block(choice.message.content)
        messages.append({"role": "assistant", "content": choice.message.content or ""})
        if choice.finish_reason == "length":
            problem = "Your reply was cut off by the token limit; return shorter but complete code."
        else:
            try:
                compile(code, "<generated>", "exec")
                return code
            except SyntaxError as e:
                problem = f"The code does not compile (SyntaxError: {e.msg} at line {e.lineno}: {(e.text or '').strip()!r})."
        messages.append({"role": "user", "content": f"{problem} Reply again with the complete, corrected {what} in one ```python block."})
    raise RuntimeError(f"LLM did not return a compilable {what} after {1 + max_retries} attempts: {problem}")
