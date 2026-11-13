"""The one structured-call helper the evaluators share (instructor client, per-model settings and slots apply)."""
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from digitalagedu.core.llm.ai_setup import image_url, llm_kwargs

T = TypeVar("T", bound=BaseModel)


def user_content(text: str, images: Optional[List[str]] = None):
    """Plain text, or text followed by image parts (slide PNGs) for vision models."""
    if not images:
        return text
    return [{"type": "text", "text": text}] + [{"type": "image_url", "image_url": {"url": image_url(p)}} for p in images]


def structured(client, model: str, response_model: Type[T], system: str, content, max_tokens: int = 16384) -> T:
    return client.chat.completions.create(
        model=model, response_model=response_model, max_retries=2, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
        **llm_kwargs(model),
    )


def clip(text: str, limit: int = 15000) -> str:
    """Keeps long files inside the prompt budget; the cut is marked so the model doesn't judge it as missing."""
    return text if len(text) <= limit else text[:limit] + f"\n... [truncated {len(text) - limit} chars]"
