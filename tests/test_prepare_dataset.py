import io
import json
import sys
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_dataset as pd_  # noqa: E402

NAMES = ["Downey mildew", "Downy mildew", "Healthy", "Rust"]


def png(seed):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (seed % 256, seed // 256, 7)).save(buf, "PNG")
    return buf.getvalue()


def plan(**kw):
    p = {"repo": "owner/data", "revision": "abc123", "layout": "parquet", "config": "default",
         "data_files": ["data/train-*"], "splits": ["train"], "image_column": "image",
         "label_column": "label", "max_per_class": 1000, "name": "leaves",
         "class_map": {"Downey mildew": "downy_mildew", "Downy mildew": "downy_mildew", "Healthy": "healthy",
                       "Rust": None}}
    p.update(kw)
    return p


def run(tmp_path, monkeypatch, p, root):
    monkeypatch.setattr(pd_, "download", lambda _plan: root)
    monkeypatch.chdir(tmp_path)
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(p))
    return pd_.prepare(plan_file, str(tmp_path / "out"))


@pytest.fixture
def parquet_root(tmp_path):
    root = tmp_path / "snap"
    (root / "data").mkdir(parents=True)
    rows, n = [], 0
    for label, count in [(0, 25), (1, 25), (2, 30), (3, 25)]:
        for _ in range(count):
            n += 1
            rows.append((label, {"bytes": png(n), "path": f"{n}.png"}))
    rows.append((2, {"bytes": b"not an image", "path": "bad.png"}))
    rows.append((2, rows[0][1]))  # same bytes as a "Downey mildew" image, different label: still a duplicate
    meta = {"info": {"features": {"label": {"_type": "ClassLabel", "names": NAMES}}}}
    table = pa.table({"image": [r[1] for r in rows], "label": [r[0] for r in rows]})
    table = table.replace_schema_metadata({"huggingface": json.dumps(meta)})
    pq.write_table(table, root / "data" / "train-00000-of-00001.parquet", row_group_size=20)
    return root


def test_parquet_merge_drop_skip_and_manifest(tmp_path, monkeypatch, parquet_root):
    final = run(tmp_path, monkeypatch, plan(), parquet_root)
    manifest = json.loads((final / "dataset_manifest.json").read_text())
    assert manifest["counts"] == {"downy_mildew": 50, "healthy": 30}
    assert manifest["skipped"] == {"corrupt": 1, "duplicate": 1, "dropped": 25, "over_cap": 0}
    assert len(list((final / "downy_mildew").glob("*.png"))) == 50
    assert (final / "healthy" / "000001.png").exists()
    assert not (final.parent / "leaves.partial").exists()
    assert manifest["plan"]["name"] == "leaves" and len(manifest["plan_sha256"]) == 64


def test_max_per_class_is_deterministic(tmp_path, monkeypatch, parquet_root):
    first = run(tmp_path, monkeypatch, plan(max_per_class=22), parquet_root)
    files = {c: sorted((first / c).iterdir()) for c in ("downy_mildew", "healthy")}
    assert all(len(v) == 22 for v in files.values())
    content = {c: [f.read_bytes() for f in v] for c, v in files.items()}
    (tmp_path / "plan.json").write_text(json.dumps(plan(max_per_class=22, name="again")))
    second = pd_.prepare(tmp_path / "plan.json", str(tmp_path / "out"))
    assert content == {c: [f.read_bytes() for f in sorted((second / c).iterdir())] for c in content}
    assert json.loads((first / "dataset_manifest.json").read_text())["skipped"]["over_cap"] == 28 + 8


def test_refuses_to_overwrite(tmp_path, monkeypatch, parquet_root):
    run(tmp_path, monkeypatch, plan(), parquet_root)
    with pytest.raises(pd_.PlanError, match="already exists"):
        run(tmp_path, monkeypatch, plan(), parquet_root)


def test_unknown_label_and_small_class_leave_nothing(tmp_path, monkeypatch, parquet_root):
    bad = plan(class_map={"Downey mildew": "a", "Healthy": "b"})
    with pytest.raises(pd_.PlanError, match="not in class_map"):
        run(tmp_path, monkeypatch, bad, parquet_root)
    tiny = plan(class_map={"Downey mildew": "a", "Downy mildew": "a", "Healthy": "b", "Rust": "c"})
    with pytest.raises(pd_.PlanError, match="20\\+ images"):
        run(tmp_path, monkeypatch, tiny | {"max_per_class": 10}, parquet_root)
    assert not list((tmp_path / "out").glob("*"))


@pytest.mark.parametrize("change", [
    {"name": "../x"}, {"name": "Has Caps"}, {"revision": ""}, {"layout": "zip"}, {"max_per_class": 0},
    {"max_per_class": True}, {"repo": "../etc/passwd"}, {"splits": ["../train"]},
    {"class_map": {"a": "../x", "b": "y"}}, {"class_map": {"a": "only", "b": "only", "c": None}},
    {"data_files": []}, {"data_files": ["../x"]}, {"data_files": ["/abs/*"]}, {"config": "a/b"},
])
def test_plan_validation_rejects(change):
    with pytest.raises(pd_.PlanError):
        pd_.validate_plan(plan(**change))


def test_reads_only_the_planned_configs_files(tmp_path, monkeypatch, parquet_root):
    # Another config with different label names, like Project-AgML/three_plant_leaf_disease_classification (raw/augmented)
    (parquet_root / "augmented").mkdir()
    other = pa.table({"image": [{"bytes": png(9000 + i), "path": f"{i}.png"} for i in range(3)], "label": [0, 0, 0]})
    other = other.replace_schema_metadata({"huggingface": json.dumps({"info": {"features": {"label": {"names": ["Healthy_Leaf"]}}}})})
    pq.write_table(other, parquet_root / "augmented" / "train-00000-of-00001.parquet")
    final = run(tmp_path, monkeypatch, plan(), parquet_root)  # data_files data/train-*: augmented/ is never read
    assert json.loads((final / "dataset_manifest.json").read_text())["counts"] == {"downy_mildew": 50, "healthy": 30}


def test_imagefolder_zip_and_directory(tmp_path, monkeypatch):
    root = tmp_path / "snap"
    for cls, base in (("cat", 0), ("dog", 100)):
        d = root / "train" / cls
        d.mkdir(parents=True)
        for i in range(21):
            (d / f"{i}.jpg").write_bytes(png(base + i))
    with zipfile.ZipFile(root / "train.zip", "w") as z:  # zip repeats nothing from the folders above
        for i in range(21):
            z.writestr(f"bird/{i}.png", png(500 + i))
        z.writestr("__MACOSX/bird/._0.png", b"junk")
    p = plan(layout="imagefolder", image_column="", label_column="",
             class_map={"cat": "cat", "dog": "dog", "bird": "bird"})
    final = run(tmp_path, monkeypatch, p, root)
    manifest = json.loads((final / "dataset_manifest.json").read_text())
    assert manifest["counts"] == {"bird": 21, "cat": 21, "dog": 21}
    assert not (tmp_path / "leaves.partial").exists()
