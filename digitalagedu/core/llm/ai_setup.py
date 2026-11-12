import ast
import base64
import contextlib
import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from typing import Any, Callable, Dict, Iterable, List, Optional, Union
from urllib.parse import urlparse
import instructor
import openai
import openai._base_client
from openai import OpenAI
from openai.lib.streaming.chat import ChatCompletionStreamState

from digitalagedu.core.llm.generation_trace import now_iso
from digitalagedu.core.llm.sandbox import clean_code_snippet

os.environ["CC"] = "gcc"
os.environ["CXX"] = "g++"

NRP_BASE_URL = "https://ellm.nrp-nautilus.io/v1"
# The project's nginx pod forwards LLM calls to NRP with the project's NRP key, which only the pod holds; callers
# authenticate with their own Tapis access token (scripts/setup_nginx_proxy.py)
LLM_PROXY_URL = "https://smartcurriculumdesigner.pods.icicleai.tapis.io/llm/v1"
TAPIS_TOKEN_RENEW_S = 600  # renew the proxy's Tapis access token this long before it expires (they last ~4 h)

# Reasoning settings per NRP model (https://nrp.ai/documentation/userdocs/ai/llm-managed/models); low because "high" made
# glm-5 calls take 30-55 min on the shared endpoint (run 3d1f2af2); qwen3-small (an optional slides model)
# runs without thinking for latency
MODEL_OPTIONS = {
    "deepseek-v4-flash": {"reasoning_effort": "low"},  # accepts low/high/xhigh/max or 1-100, not "medium" (400)
    "glm-5": {"reasoning_effort": "low"},
    "qwen3-small": {"enable_thinking": False},
}
# One salt per run keeps NRP's prefix cache private to us while still shared across this run's calls
_RUN_SALT = uuid.uuid4().hex
PROGRESS_EVERY_S = 60
STREAM_DROP_RETRIES = 2
STREAM_DROP_BACKOFF_S = 10
# Per-model request slots shared by every week worker process (passed in at start-up) and prefetch thread
MODEL_SLOTS: Dict[str, Any] = {}

def _sdk_transport_error(base_client) -> type:
    """TransportError of the SDK's own HTTP library: httpx2 in the container's openai, httpx in older ones
    (assuming httpx crashed Phase 2 on import in run 82400814)."""
    http = getattr(base_client, "httpx2", None) or getattr(base_client, "httpx", None)
    return getattr(http, "TransportError", openai.APIConnectionError)


# Connection errors while iterating a stream, raised by the SDK's HTTP library rather than wrapped by the SDK
_STREAM_DROPS = (openai.APIConnectionError, _sdk_transport_error(openai._base_client))

# The SDK logs "Retrying request to /chat/completions in N seconds" (timeouts, 429/5xx) at INFO, which is off by default
_sdk_log = logging.getLogger("openai")
if not _sdk_log.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[LLM %(asctime)s] openai: %(message)s", "%H:%M:%S"))
    _sdk_log.addHandler(_handler)
    _sdk_log.setLevel(logging.INFO)


def log_llm(message: str) -> None:
    line = f"[LLM {time.strftime('%H:%M:%S')}] {message}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:  # e.g. a model's "≈" on a cp1252 console; a log line must never break a call
        print(line.encode("ascii", "replace").decode(), flush=True)


def configure_model_slots(limits: Dict[str, int], ctx=None) -> None:
    """Caps concurrent requests per model, e.g. {"glm-5": 4} (NRP's per-user fair-use limit). Pass `ctx` matching the
    week workers' start method and hand MODEL_SLOTS to them at start-up, so one cap holds across processes and threads."""
    import multiprocessing
    ctx = ctx or multiprocessing.get_context()
    MODEL_SLOTS.clear()
    MODEL_SLOTS.update({model: ctx.BoundedSemaphore(n) for model, n in limits.items() if n and n > 0})


def _prompt_chars(messages) -> int:
    return sum(len(str(m.get("content", ""))) for m in messages or [])


def llm_kwargs(model: str) -> Dict:
    """Per-call extra request fields for `model` on the NRP endpoint."""
    return {"extra_body": {"chat_template_kwargs": MODEL_OPTIONS.get(model, {}), "cache_salt": _RUN_SALT}}


def nrp_api_key() -> str:
    """NRP_LLM_API env var: an NRP key, only for runs that call NRP directly (llm_base_url set to NRP_BASE_URL).
    Not a file: expanse-tapis-static runs every user's jobs as one shared account, so any file there is readable
    by all its users."""
    key = (os.getenv("NRP_LLM_API") or "").strip()
    if not key:
        raise RuntimeError("No NRP LLM API key: llm_base_url points at NRP directly, so export NRP_LLM_API, "
                           f"or remove llm_base_url to use the project's LLM proxy ({LLM_PROXY_URL}).")
    return key


class TapisAccessToken:
    """API key for the LLM proxy: a Tapis access token minted from a refresh token and renewed before it expires.
    The OpenAI SDK (>= 1.106) calls a callable api_key before every request, so long jobs never send a stale token."""

    def __init__(self, refresh_token: str):
        self._refresh_token = refresh_token
        self._token, self._renew_at = "", 0.0
        self._lock = threading.Lock()  # slide-code prefetch threads share one client

    def __call__(self) -> str:
        with self._lock:
            if time.time() >= self._renew_at:
                from digitalagedu.core.llm.rag.qdrant_client import decode_jwt_payload, exchange_tapis_refresh_token
                self._token = exchange_tapis_refresh_token(self._refresh_token)
                expires = decode_jwt_payload(self._token).get("exp") or time.time() + 3600
                self._renew_at = expires - TAPIS_TOKEN_RENEW_S
            return self._token


def calls_nrp_directly(base_url: Optional[str]) -> bool:
    return urlparse(base_url or LLM_PROXY_URL).hostname == urlparse(NRP_BASE_URL).hostname


def llm_api_key(base_url: str) -> Union[str, Callable[[], str]]:
    """Credential for `base_url`: the NRP key when calling NRP directly, otherwise a renewing Tapis access token
    for the LLM proxy, from the TAPIS_REFRESH_TOKEN every job submitted by the web app carries."""
    if calls_nrp_directly(base_url):
        return nrp_api_key()
    refresh_token = (os.getenv("TAPIS_REFRESH_TOKEN") or "").strip()
    if not refresh_token:
        raise RuntimeError("No TAPIS_REFRESH_TOKEN for the LLM proxy: submit the job from the web app, or export "
                           "TAPIS_REFRESH_TOKEN for local runs.")
    return TapisAccessToken(refresh_token)


def image_url(png_path: str) -> str:
    """Base64 data URL for an image content part ({"type": "image_url", "image_url": {"url": ...}}); NRP accepts
    these on vision models (deepseek-v4-flash, qwen3, gemma, kimi, minimax), not on glm-5."""
    with open(png_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def get_openai_client(base_url: Optional[str] = None, api_key: Optional[str] = None) -> OpenAI:
    """Plain OpenAI-compatible client for the LLM endpoint (used for free-text code replies): the project's LLM
    proxy by default, or NRP directly. Thinking calls run long; the SDK's retries back off on 429/5xx from fair-use
    throttling. `api_key` lets week workers build their own clients after NRP_LLM_API has been removed from the
    environment; without it the credential comes from llm_api_key."""
    base_url = base_url or LLM_PROXY_URL
    return OpenAI(base_url=base_url, api_key=api_key or llm_api_key(base_url), timeout=900, max_retries=5)

def get_instructor_client(base_url: Optional[str] = None, api_key: Optional[str] = None) -> instructor.Instructor:
    """Instructor client: JSON_SCHEMA sends the Pydantic schema as response_format, so the server enforces it,
    and instructor still re-asks with validation errors from our field validators."""
    openai_client = get_openai_client(base_url, api_key)
    # Instructor binds chat.completions.create once, in from_openai, so the swap must come first
    openai_client.chat.completions.create = _streamed_create(openai_client.chat.completions)
    client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON_SCHEMA)
    started = {}

    def on_kwargs(*args, **kwargs):
        started["t"] = time.monotonic()
        log_llm(f"{kwargs.get('model')} <- structured call ({_prompt_chars(kwargs.get('messages'))} prompt chars)")

    def on_response(response):
        usage = getattr(response, "usage", None)
        log_llm(f"structured call done in {time.monotonic() - started.get('t', time.monotonic()):.0f}s: "
                f"prompt={getattr(usage, 'prompt_tokens', None)} completion={getattr(usage, 'completion_tokens', None)} tokens")

    client.on("completion:kwargs", on_kwargs)
    client.on("completion:response", on_response)
    client.on("completion:error", lambda err: log_llm(f"structured call error: {err!r}"[:500]))
    client.on("parse:error", lambda err: log_llm(f"structured reply failed validation, re-asking: {err}"[:500]))
    return client


def _streamed_create(completions) -> Callable:
    """chat.completions.create that always streams and returns the assembled ChatCompletion. Non-streamed structured
    calls sat silent for minutes while the model thought; NRP answered (pod log: 200) but the job got
    APIConnectionError every time, because something on the route drops silent connections (runs 8edbd8ea, e741c71c)."""
    create = completions.create

    def streamed(*args, **kwargs):
        if kwargs.pop("stream", False):
            return create(*args, stream=True, **kwargs)
        model = kwargs.get("model")
        for drop in range(STREAM_DROP_RETRIES + 1):
            try:
                with MODEL_SLOTS.get(model) or contextlib.nullcontext():
                    state = ChatCompletionStreamState()
                    for chunk in create(*args, **kwargs, stream=True, stream_options={"include_usage": True}):
                        state.handle_chunk(chunk)
                    # The snapshot, not get_final_completion(): that raises on finish_reason="length", which instructor handles itself
                    return state.current_completion_snapshot
            except _STREAM_DROPS as err:
                # Instructor treats connection errors as final, so a stream cut mid-reply is retried here
                if drop == STREAM_DROP_RETRIES:
                    raise
                log_llm(f"{model} structured call: stream dropped ({type(err).__name__}: {err}); retry {drop + 1}/{STREAM_DROP_RETRIES}")
                time.sleep(STREAM_DROP_BACKOFF_S * (drop + 1))

    return streamed


def _stream_reply(code_client, model_name: str, messages: List[Dict[str, str]], max_tokens: int, what: str):
    """One streamed chat completion -> (content, finish_reason, usage). Streaming keeps bytes flowing during long
    thinking, so the 900 s read timeout no longer cuts a call the SDK then restarts from scratch; logs progress."""
    slot = MODEL_SLOTS.get(model_name) or contextlib.nullcontext()
    with slot:
        return _stream_reply_unlimited(code_client, model_name, messages, max_tokens, what)


def _stream_reply_unlimited(code_client, model_name: str, messages: List[Dict[str, str]], max_tokens: int, what: str):
    log_llm(f"{model_name} <- {what} ({_prompt_chars(messages)} prompt chars)")
    started = last = time.monotonic()
    parts, finish, usage, tokens, thinking = [], None, None, 0, 0
    stream = code_client.chat.completions.create(
        model=model_name, max_tokens=max_tokens, messages=messages, stream=True,
        stream_options={"include_usage": True}, **llm_kwargs(model_name),
    )
    for chunk in stream:
        usage = getattr(chunk, "usage", None) or usage
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        parts.append(choice.delta.content or "")
        finish = choice.finish_reason or finish
        tokens += 1  # vLLM streams about one token per chunk; thinking arrives in delta.reasoning
        thinking += bool(getattr(choice.delta, "reasoning", None) or getattr(choice.delta, "reasoning_content", None))
        if time.monotonic() - last >= PROGRESS_EVERY_S:
            last = time.monotonic()
            log_llm(f"{model_name} {what}: {last - started:.0f}s, ~{tokens} tokens, {thinking} of them reasoning ({tokens / (last - started):.1f} tok/s)")
    log_llm(f"{model_name} -> {what} in {time.monotonic() - started:.0f}s: finish={finish}, "
            f"prompt={getattr(usage, 'prompt_tokens', None)} completion={getattr(usage, 'completion_tokens', None)} tokens")
    return "".join(parts), finish, usage


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
        for drop in range(STREAM_DROP_RETRIES + 1):
            try:
                content, finish_reason, usage = _stream_reply(code_client, model_name, messages, max_tokens, what)
                break
            except _STREAM_DROPS as err:
                # The SDK retries only before a reply starts; a stream cut mid-reply (run 49088b7e) failed the week
                if drop == STREAM_DROP_RETRIES:
                    raise
                log_llm(f"{model_name} {what}: stream dropped ({type(err).__name__}: {err}); retry {drop + 1}/{STREAM_DROP_RETRIES}")
                time.sleep(STREAM_DROP_BACKOFF_S * (drop + 1))
        code = extract_code_block(content)
        messages.append({"role": "assistant", "content": content})
        problem = None
        if finish_reason == "length":
            problem = "Your reply was cut off by the token limit; return shorter but complete code."
        else:
            try:
                compile(code, "<generated>", "exec")
                code = add_missing_typing_imports(code)
            except SyntaxError as e:
                problem = f"The code does not compile (SyntaxError: {e.msg} at line {e.lineno}: {(e.text or '').strip()!r})."
        if trace is not None:
            act = trace.add_activity(
                "llm_call", agent, start=start, model=model_name, max_tokens=max_tokens, attempt=attempt,
                purpose=purpose if attempt == 1 else "compile_retry", finish_reason=finish_reason,
                prompt_tokens=getattr(usage, "prompt_tokens", None), completion_tokens=getattr(usage, "completion_tokens", None),
            )
            if informed_by and attempt == 1:
                trace.relate("wasInformedBy", informed=act, informant=informed_by)
            prompt_e = trace.add_entity("prompt", prompt_snapshot, ext="json")
            reply_e = trace.add_entity("reply", content, ext="md")
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
        log_llm(f"{model_name} {what} re-asked: {problem}")
        messages.append({"role": "user", "content": f"{problem} Reply again with the complete, corrected {what} in one ```python block."})
    raise RuntimeError(f"LLM did not return a compilable {what} after {1 + max_retries} attempts: {problem}")
