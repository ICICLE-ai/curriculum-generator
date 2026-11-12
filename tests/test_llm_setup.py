import pytest

from digitalagedu.core.config import ExecutionModel
from digitalagedu.core.llm.ai_setup import llm_kwargs, nrp_api_key
from digitalagedu.core.llm.sandbox import run_in_sandbox


def _execution(**overrides):
    return ExecutionModel(device="cpu", batch_size=1, image_size=64, **overrides)


def test_llm_models_default_per_role_and_override_one_role():
    assert _execution().llm_models.model_dump() == {
        "planner": "deepseek-v4-flash", "coder": "glm-5", "arbiter": "deepseek-v4-flash", "slide_reviewer": "deepseek-v4-flash", "slides": "glm-5",
    }
    models = _execution(llm_models={"coder": "kimi"}).llm_models
    assert (models.coder, models.planner, models.slides) == ("kimi", "deepseek-v4-flash", "glm-5")


def test_llm_kwargs_sets_reasoning_per_model_and_one_cache_salt():
    slides, coder = llm_kwargs("qwen3-small")["extra_body"], llm_kwargs("glm-5")["extra_body"]
    assert slides["chat_template_kwargs"] == {"enable_thinking": False}
    assert coder["chat_template_kwargs"] == {"reasoning_effort": "low"}
    assert llm_kwargs("unknown-model")["extra_body"]["chat_template_kwargs"] == {}
    assert slides["cache_salt"] == coder["cache_salt"]


def test_sandboxed_code_cannot_see_credentials(monkeypatch):
    monkeypatch.setenv("NRP_LLM_API", "secret-key")
    monkeypatch.setenv("TAPIS_REFRESH_TOKEN", "secret-token")
    test = "import os\ndef test_env():\n    assert 'NRP_LLM_API' not in os.environ and 'TAPIS_REFRESH_TOKEN' not in os.environ\n"
    ok, log = run_in_sandbox("x = 1\n", test, module_id="m")
    assert ok, log


def test_nrp_api_key_from_env_else_clear_error(monkeypatch):
    monkeypatch.setenv("NRP_LLM_API", " from-env\n")
    assert nrp_api_key() == "from-env"
    monkeypatch.delenv("NRP_LLM_API")
    with pytest.raises(RuntimeError, match="NRP_LLM_API"):
        nrp_api_key()


def test_llm_credential_is_nrp_key_for_nrp_else_tapis_token_for_the_proxy(monkeypatch):
    from digitalagedu.core.llm.ai_setup import LLM_PROXY_URL, NRP_BASE_URL, TapisAccessToken, llm_api_key
    monkeypatch.setenv("NRP_LLM_API", "nrp-key")
    monkeypatch.setenv("TAPIS_REFRESH_TOKEN", " refresh-token\n")
    assert llm_api_key(NRP_BASE_URL) == "nrp-key"
    # The proxy never gets the NRP key, even when one is set: it only accepts Tapis tokens
    assert isinstance(llm_api_key(LLM_PROXY_URL), TapisAccessToken)
    monkeypatch.delenv("TAPIS_REFRESH_TOKEN")
    with pytest.raises(RuntimeError, match="TAPIS_REFRESH_TOKEN"):
        llm_api_key(LLM_PROXY_URL)


def test_proxy_client_sends_a_tapis_token_renewed_before_it_expires(monkeypatch):
    """Jobs run up to 13 h and Tapis access tokens last ~4 h: each request must carry a token that is still valid."""
    import base64
    import json
    import openai
    from digitalagedu.core.llm import ai_setup
    from digitalagedu.core.llm.rag import qdrant_client

    clock = [1_000_000.0]
    monkeypatch.setattr(ai_setup.time, "time", lambda: clock[0])
    minted = []

    def exchange(refresh_token, tapis_base_url=None):
        assert refresh_token == "refresh-token"
        claims = base64.urlsafe_b64encode(json.dumps({"exp": clock[0] + 4 * 3600}).encode()).decode().rstrip("=")
        minted.append(f"hdr.{claims}.sig{len(minted)}")
        return minted[-1]

    monkeypatch.setattr(qdrant_client, "exchange_tapis_refresh_token", exchange)
    monkeypatch.setenv("TAPIS_REFRESH_TOKEN", "refresh-token")
    sent = []
    http = getattr(openai._base_client, "httpx2", None) or getattr(openai._base_client, "httpx")

    def endpoint(request):
        sent.append(request.headers["Authorization"])
        return http.Response(200, json={"object": "list", "data": []})

    client = openai.OpenAI(base_url=ai_setup.LLM_PROXY_URL, api_key=ai_setup.llm_api_key(ai_setup.LLM_PROXY_URL),
                           http_client=openai.DefaultHttpxClient(transport=http.MockTransport(endpoint)))
    client.models.list()
    clock[0] += 3 * 3600  # still inside the token's lifetime: reused
    client.models.list()
    clock[0] += 3600 - ai_setup.TAPIS_TOKEN_RENEW_S  # inside the renewal margin: a new token
    client.models.list()
    assert sent == [f"Bearer {minted[0]}", f"Bearer {minted[0]}", f"Bearer {minted[1]}"]


def test_stream_drop_error_found_under_either_sdk_http_library_name():
    # The container's openai exposes httpx2, older SDKs httpx; a missing name crashed Phase 2 on import (run 82400814)
    import types
    import openai
    from digitalagedu.core.llm.ai_setup import _sdk_transport_error

    class TransportError(Exception):
        pass

    lib = types.SimpleNamespace(TransportError=TransportError)
    assert _sdk_transport_error(types.SimpleNamespace(httpx2=lib)) is TransportError
    assert _sdk_transport_error(types.SimpleNamespace(httpx=lib)) is TransportError
    assert _sdk_transport_error(types.SimpleNamespace()) is openai.APIConnectionError
