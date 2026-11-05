import errno

import numpy as np
import pytest
from PIL import Image

from curriculum_resources.segmentation import solution


def test_png_save_retries_lustre_io_errors_then_gives_up(tmp_path, monkeypatch):
    # Expanse's Lustre returned EIO on PNG writes and ended Phase 1 (runs c2adab2d, 7ed996a7)
    real_save, calls = Image.Image.save, []

    def flaky_save(self, path, *a, **kw):
        calls.append(path)
        if len(calls) == 1:
            raise OSError(errno.EIO, "Input/output error")
        return real_save(self, path, *a, **kw)

    monkeypatch.setattr(Image.Image, "save", flaky_save)
    out = tmp_path / "mask.png"
    solution._save_png(np.zeros((4, 4), np.uint8), str(out), wait_s=0)
    assert len(calls) == 2 and out.exists()

    monkeypatch.setattr(Image.Image, "save", lambda self, path, *a, **kw: (_ for _ in ()).throw(OSError(errno.EIO, "x")))
    with pytest.raises(OSError):
        solution._save_png(np.zeros((4, 4), np.uint8), str(tmp_path / "never.png"), wait_s=0)
