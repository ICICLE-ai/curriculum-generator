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


def test_sam_box_comes_from_the_text_prompt_else_the_whole_image(tmp_path, monkeypatch):
    boxes = []

    class FakePredictor:
        def set_image(self, image):
            pass

        def predict(self, box, multimask_output):
            boxes.append(list(box))
            return np.ones((1, 8, 8), bool), np.array([1.0]), None

    monkeypatch.setattr(solution, "get_sam_predictor", lambda *a: FakePredictor())
    detections = {"leaf spot.": [1, 2, 5, 6]}
    monkeypatch.setattr(solution, "detect_prompt_box", lambda image, prompt, device: detections.get(prompt))
    image = tmp_path / "leaf.png"
    Image.new("RGB", (8, 8)).save(image)
    run = lambda prompt: solution.segment_object(str(image), "sam.pth", "cpu", str(tmp_path), (8, 8), prompt=prompt)

    assert run("leaf spot.")[2] is True and boxes[-1] == [1, 2, 5, 6]
    assert run("a cat.")[2] is False and boxes[-1] == [0, 0, 8, 8]  # no match: outline the whole image's object
    assert run(None)[2] is False and boxes[-1] == [0, 0, 8, 8]
