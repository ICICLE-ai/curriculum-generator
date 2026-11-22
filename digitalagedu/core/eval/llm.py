"""The one structured-call helper the evaluators share (instructor client, per-model settings and slots apply)."""
from typing import List, Optional, Type, TypeVar

from instructor.exceptions import IncompleteOutputException
from pydantic import BaseModel

from digitalagedu.core.llm.ai_setup import image_url, llm_kwargs

T = TypeVar("T", bound=BaseModel)


def user_content(text: str, images: Optional[List[str]] = None):
    """Plain text, or text followed by image parts (slide PNGs) for vision models."""
    if not images:
        return text
    return [{"type": "text", "text": text}] + [{"type": "image_url", "image_url": {"url": image_url(p)}} for p in images]


RUNAWAY_RETRIES = 2  # fresh tries after a reply that hit max_tokens


def structured(client, model: str, response_model: Type[T], system: str, content, max_tokens: int = 16384) -> T:
    """One structured call. A reply cut off at max_tokens is asked again from scratch: kimi sometimes reasons until
    the limit on even a short task (Bloom classify: 16,384 tokens in 1,017 s for a 161-token prompt, run 2736
    damage test), and instructor's own retries don't cover a truncated reply."""
    for attempt in range(RUNAWAY_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=model, response_model=response_model, max_retries=2, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
                **llm_kwargs(model),
            )
        except IncompleteOutputException:
            if attempt == RUNAWAY_RETRIES:
                raise


def clip(text: str, limit: int = 40000) -> str:
    """Keeps long files inside the prompt budget; the cut is marked so the model doesn't judge it as missing.
    40,000 characters (~10k tokens) fits a whole week's starter or tests: at 15,000 the judge scored the SAM week's
    complete starter as "truncated mid-implementation" despite the marker (run 2736 evaluation)."""
    return text if len(text) <= limit else text[:limit] + f"\n... [truncated {len(text) - limit} chars]"
