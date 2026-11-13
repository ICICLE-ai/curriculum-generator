"""Structured (instructor) calls stream under the hood, so long replies never sit on a silent connection."""
from openai.types.chat import ChatCompletionChunk

from digitalagedu.core.llm import ai_setup


def chunk(content=None, finish_reason=None, usage=None, choices=True):
    return ChatCompletionChunk.model_validate({
        "id": "c1", "object": "chat.completion.chunk", "created": 0, "model": "m",
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": finish_reason}] if choices else [],
        "usage": usage,
    })


REPLY = [chunk('{"a": '), chunk("1}", finish_reason="stop"),
         chunk(choices=False, usage={"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7})]


class FakeCompletions:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return iter(reply)


def test_structured_call_streams_and_returns_one_completion():
    fake = FakeCompletions([REPLY])
    completion = ai_setup._streamed_create(fake)(model="m", messages=[], stream=False)
    assert fake.calls[0]["stream"] is True and fake.calls[0]["stream_options"] == {"include_usage": True}
    assert completion.choices[0].message.content == '{"a": 1}'
    assert completion.choices[0].finish_reason == "stop"
    assert completion.usage.completion_tokens == 2


def test_a_dropped_stream_is_retried(monkeypatch):
    monkeypatch.setattr(ai_setup.time, "sleep", lambda s: None)
    drop = ai_setup._STREAM_DROPS[1]("peer closed connection")  # the SDK's HTTP library's TransportError
    fake = FakeCompletions([drop, REPLY])
    completion = ai_setup._streamed_create(fake)(model="m", messages=[])
    assert len(fake.calls) == 2
    assert completion.choices[0].message.content == '{"a": 1}'
