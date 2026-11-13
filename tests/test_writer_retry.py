import builtins
import errno

import pytest

from digitalagedu.core import writer


def test_write_file_retries_lustre_io_errors_then_gives_up(tmp_path, monkeypatch):
    # Expanse's Lustre returned EIO on Phase 2 writes and failed all 4 weeks of run f53b2469
    real_open, calls = builtins.open, []

    def flaky_open(path, *a, **kw):
        calls.append(path)
        if len(calls) == 1:
            raise OSError(errno.EIO, "Input/output error")
        return real_open(path, *a, **kw)

    monkeypatch.setattr(builtins, "open", flaky_open)
    out = tmp_path / "overview.md"
    writer.write_file(str(out), lambda f: f.write("hello"), wait_s=0)
    assert len(calls) == 2 and out.read_text(encoding="utf-8") == "hello"

    def always_eio(path, *a, **kw):
        raise OSError(errno.EIO, "x")

    monkeypatch.setattr(builtins, "open", always_eio)
    with pytest.raises(OSError):
        writer.write_file(str(tmp_path / "never.md"), lambda f: f.write("x"), wait_s=0)


def test_retry_eio_does_not_retry_other_errors(tmp_path):
    calls = []

    def save(path):
        calls.append(path)
        raise OSError(errno.ENOSPC, "No space left on device")

    with pytest.raises(OSError):
        writer.retry_eio(save, str(tmp_path / "deck.pptx"), wait_s=0)
    assert len(calls) == 1
