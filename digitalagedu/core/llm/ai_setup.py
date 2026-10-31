import ast
import json
import os
import re
import uuid
from typing import Dict, Iterable, List, Optional
import instructor
from openai import OpenAI

from digitalagedu.core.llm.generation_trace import now_iso
from digitalagedu.core.llm.sandbox import clean_code_snippet

os.environ["CC"] = "gcc"
os.environ["CXX"] = "g++"

NRP_BASE_URL = "https://ellm.nrp-nautilus.io/v1"

# Reasoning settings per NRP model (https://nrp.ai/documentation/userdocs/ai/llm-managed/models); the default "max"
# effort is token-heavy, and qwen3-small renders slides, where thinking only adds latency
MODEL_OPTIONS = {
    "deepseek-v4-flash": {"reasoning_effort": "high"},
    "glm-5": {"reasoning_effort": "high"},
    "qwen3-small": {"enable_thinking": False},
}
# One salt per run keeps NRP's prefix cache private to us while still shared across this run's calls
_RUN_SALT = uuid.uuid4().hex


def llm_kwargs(model: str) -> Dict:
    """Per-call extra request fields for `model` on the NRP endpoint."""
    return {"extra_body": {"chat_template_kwargs": MODEL_OPTIONS.get(model, {}), "cache_salt": _RUN_SALT}}


def nrp_api_key() -> str:
    """NRP_LLM_API env var, sent per job by the web app's submit form. Not a file: expanse-tapis-static runs every
    user's jobs as one shared account, so any file there is readable by all its users."""
    key = (os.getenv("NRP_LLM_API") or "").strip()
    if not key:
        raise RuntimeError("No NRP LLM API key: enter it in the web app's submit form, or export NRP_LLM_API for local runs.")
    return key


def get_openai_client(base_url: Optional[str] = None) -> OpenAI:
    """Plain OpenAI-compatible client for the NRP managed LLM endpoint (used for free-text code replies).
    Thinking calls run long; the SDK's retries back off on 429/5xx from fair-use throttling."""
    return OpenAI(base_url=base_url or NRP_BASE_URL, api_key=nrp_api_key(), timeout=900, max_retries=5)

def get_instructor_client(base_url: Optional[str] = None) -> instructor.Instructor:
    """Instructor client: JSON_SCHEMA sends the Pydantic schema as response_format, so the server enforces it,
    and instructor still re-asks with validation errors from our field validators."""
    return instructor.from_openai(get_openai_client(base_url), mode=instructor.Mode.JSON_SCHEMA)


_CODE_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


def extract_code_block(text: str) -> str:
    """Longest fenced block of a plain-text reply; an unfenced (or unclosed) reply is taken whole."""
    blocks = _CODE_FENCE.findall(text or "")
    return max(blocks, key=len).strip() if blocks else clean_code_snippet(text or "")


# Annotation-only typing names (aliases like typing.Counter are excluded: they can't be instantiated)
_TYPING_HINTS = {
    "Any", "Union", "Optional", "List", "Dict", "Tuple", "Set", "FrozenSet", "Callable", "Iterable", "Iterator",
    "Sequence", "Mapping", "Generator", "Type", "TypeVar", "Literal", "Protocol", "NamedTuple", "TypedDict",
    "Annotated", "ClassVar", "Final", "cast",
}


def add_missing_typing_imports(code: str) -> str:
    """Prepends `from typing import ...` for typing hints used but never bound, a frequent LLM omission
    that otherwise costs a whole sandbox round (NameError: name 'Any' is not defined)."""
    tree = ast.parse(code)
    used, bound = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            (used if isinstance(node.ctx, ast.Load) else bound).add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            bound |= {(alias.asname or alias.name).split(".")[0] for alias in node.names}
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
    missing = sorted((used - bound) & _TYPING_HINTS)
    if not missing or "*" in bound or "from __future__" in code:
        return code
    return f"from typing import {', '.join(missing)}\n{code}"


def ask_code(code_client, model_name: str, messages: List[Dict[str, str]], what: str,
             max_retries: int = 2, max_tokens: int = 32768,
             trace=None, agent: Optional[str] = None, artifact: Optional[str] = None,
             purpose: str = "generate", used: Iterable[str] = (), informed_by: Optional[str] = None) -> str:
    """Plain-text LLM call returning one ```python block. Code never travels inside JSON, so quotes need
    no escaping; replies that are cut off or don't compile are re-asked with the error.
    Extends `messages` in place (ending with the accepted reply) so callers can continue the conversation.
    With a GenerationTrace, every attempt is recorded as a PROV activity producing a versioned `artifact`
    entity derived from the previous version and from the `used` entities (e.g. the sandbox log behind a repair)."""
    messages[-1] = {**messages[-1], "content": (
        f"{messages[-1]['content']}\n\nOUTPUT FORMAT: Reply with the complete {what} as ONE ```python fenced code block and nothing else."
    )}
    for attempt in range(1, 2 + max_retries):
        start, prompt_snapshot = now_iso(), json.dumps(messages, indent=2)
        completion = code_client.chat.completions.create(model=model_name, max_tokens=max_tokens, messages=messages,
                                                         **llm_kwargs(model_name))
        choice = completion.choices[0]
        code = extract_code_block(choice.message.content)
        messages.append({"role": "assistant", "content": choice.message.content or ""})
        problem = None
        if choice.finish_reason == "length":
            problem = "Your reply was cut off by the token limit; return shorter but complete code."
        else:
            try:
                compile(code, "<generated>", "exec")
                code = add_missing_typing_imports(code)
            except SyntaxError as e:
                problem = f"The code does not compile (SyntaxError: {e.msg} at line {e.lineno}: {(e.text or '').strip()!r})."
        if trace is not None:
            usage = getattr(completion, "usage", None)
            act = trace.add_activity(
                "llm_call", agent, start=start, model=model_name, max_tokens=max_tokens, attempt=attempt,
                purpose=purpose if attempt == 1 else "compile_retry", finish_reason=choice.finish_reason,
                prompt_tokens=getattr(usage, "prompt_tokens", None), completion_tokens=getattr(usage, "completion_tokens", None),
            )
            if informed_by and attempt == 1:
                trace.relate("wasInformedBy", informed=act, informant=informed_by)
            prompt_e = trace.add_entity("prompt", prompt_snapshot, ext="json")
            reply_e = trace.add_entity("reply", choice.message.content or "", ext="md")
            # A fresh generation (e.g. after a contract revision) is not derived from the old code; retries/repairs are
            previous = trace.latest.get(artifact) if attempt > 1 or purpose != "generate" else None
            code_e = trace.add_entity(artifact, code, ext="py", versioned=True, compiles=problem is None, compile_error=problem)
            trace.relate("used", activity=act, entity=prompt_e)
            trace.relate("wasGeneratedBy", entity=reply_e, activity=act)
            trace.relate("wasGeneratedBy", entity=code_e, activity=act)
            trace.relate("wasDerivedFrom", generatedEntity=code_e, usedEntity=reply_e)
            for source in ([previous] if previous else []) + list(used):
                trace.relate("used", activity=act, entity=source)
                trace.relate("wasDerivedFrom", generatedEntity=code_e, usedEntity=source)
        if problem is None:
            return code
        messages.append({"role": "user", "content": f"{problem} Reply again with the complete, corrected {what} in one ```python block."})
    raise RuntimeError(f"LLM did not return a compilable {what} after {1 + max_retries} attempts: {problem}")
