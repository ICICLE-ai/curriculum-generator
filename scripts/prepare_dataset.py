#!/usr/bin/env python3
"""Download a Hugging Face image dataset, clean it into <out-dir>/<name>/<class>/<n>.<ext> and write its manifest.

    python scripts/prepare_dataset.py --plan plan.json --out-dir /abs/smart_curriculum_designer_datasets

The plan is the web app's DatasetPlan JSON (frontend/src/utils/assistant/types.ts); it came from a browser, so it is
validated here. Supported shapes:
Only the plan's `data_files` globs (one Hugging Face config's files) are downloaded and read: configs of one repo can
use different label names.
  parquet:     .parquet files matching data_files, an image struct column {bytes, path}
               and a label column holding ClassLabel indexes (names read from the parquet's `huggingface` metadata)
               or plain strings.
  imagefolder: <split>/<class>/<image> files in the repo, or <split>.zip archives holding <class>/<image>.
Last stdout line: "[DATASET READY] <path>" or "[DATASET FAILED] <reason>" (exit 1).
"""
import argparse
import fnmatch
import hashlib
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

SAFE = re.compile(r"^[a-z0-9_]+$")
SPLIT = re.compile(r"^[A-Za-z0-9_-]+$")
REPO = re.compile(r"^[A-Za-z0-9][\w.-]*/[\w.-]+$")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
MIN_PER_CLASS = 20


class PlanError(Exception):
    pass


def validate_plan(p):
    if not isinstance(p, dict):
        raise PlanError("plan must be a JSON object")
    str_keys = ("repo", "revision", "layout", "image_column", "label_column", "name")
    for k in str_keys + ("splits", "class_map", "max_per_class"):
        if k not in p:
            raise PlanError(f"plan is missing '{k}'")
    if not all(isinstance(p[k], str) for k in str_keys):
        raise PlanError(f"{', '.join(str_keys)} must be strings")
    if not REPO.match(p["repo"]) or ".." in p["repo"]:
        raise PlanError(f"bad repo '{p['repo']}'")
    if not p["revision"].strip() or ".." in p["revision"] or p["revision"].startswith("-"):
        raise PlanError("revision must be a pinned, non-empty commit")
    if p["layout"] not in ("parquet", "imagefolder"):
        raise PlanError(f"layout must be parquet or imagefolder, got '{p['layout']}'")
    if not SAFE.match(p["name"]):
        raise PlanError(f"name '{p['name']}' must match [a-z0-9_]+")
    if not isinstance(p.get("config"), str) or not re.fullmatch(r"[\w.-]+", p["config"]):
        raise PlanError("config must be a plain config name")
    df = p.get("data_files")
    if not isinstance(df, list) or not df or not all(
            isinstance(g, str) and g.strip() and ".." not in g and not g.startswith("/") and "\\" not in g for g in df):
        raise PlanError("data_files must be a non-empty list of relative repo globs")
    sp = p["splits"]
    if not isinstance(sp, list) or not sp or not all(isinstance(s, str) and SPLIT.match(s) for s in sp):
        raise PlanError("splits must be a non-empty list of plain split names")
    if p["layout"] == "parquet" and not (p["image_column"] and p["label_column"]):
        raise PlanError("parquet plans need image_column and label_column")
    m = p["max_per_class"]
    if isinstance(m, bool) or not isinstance(m, int) or not 1 <= m <= 100000:
        raise PlanError("max_per_class must be an integer from 1 to 100000")
    cm = p["class_map"]
    if not isinstance(cm, dict) or not all(isinstance(k, str) for k in cm):
        raise PlanError("class_map must map label names to a folder name or null")
    targets = {v for v in cm.values() if v is not None}
    if not all(isinstance(v, str) and SAFE.match(v) for v in targets):
        raise PlanError("class_map targets must match [a-z0-9_]+")
    if len(targets) < 2:
        raise PlanError("class_map must keep at least 2 distinct classes")


def download(plan):
    from huggingface_hub import snapshot_download
    return Path(snapshot_download(plan["repo"], repo_type="dataset", revision=plan["revision"],
                                  allow_patterns=plan["data_files"] + ["README.md"]))


def class_names(pf, column):
    meta = (pf.schema_arrow.metadata or {}).get(b"huggingface")
    feature = json.loads(meta).get("info", {}).get("features", {}).get(column, {}) if meta else {}
    # ClassLabel is stored as {"_type": "ClassLabel", "names": [...]}; older exports omit _type
    return feature.get("names") if isinstance(feature, dict) else None


def parquet_rows(root, plan):
    img_col, lab_col = plan["image_column"], plan["label_column"]
    planned = [f for f in sorted(root.rglob("*.parquet"))
               if any(fnmatch.fnmatch(f.relative_to(root).as_posix(), g) for g in plan["data_files"])]
    for split in plan["splits"]:
        files = [f for f in planned if split in f.relative_to(root).as_posix()]
        if not files:
            raise PlanError(f"no parquet files for split '{split}' in {plan['data_files']}")
        n = 0
        for f in files:
            pf = pq.ParquetFile(f)
            if img_col not in pf.schema_arrow.names or lab_col not in pf.schema_arrow.names:
                raise PlanError(f"{f.name} has no '{img_col}' or '{lab_col}' column")
            names = class_names(pf, lab_col)
            for batch in pf.iter_batches(batch_size=64, columns=[img_col, lab_col]):
                for row in batch.to_pylist():
                    lab = row[lab_col]
                    yield (names[lab] if names and isinstance(lab, int) else str(lab)), (row[img_col] or {}).get("bytes")
                    n += 1
            print(f"[prepare] {split}: {n} rows", flush=True)


def folder_rows(root, plan, tmp):
    for split in plan["splits"]:
        sources = []  # (base dir, whether every image counts or only those under a <split>/ directory)
        for z in sorted(f for f in root.rglob("*.zip") if split in f.name):
            dest = Path(tmp) / f"{split}_{len(sources)}"
            with zipfile.ZipFile(z) as zf:
                zf.extractall(dest)  # zipfile drops ../ and absolute member paths
            sources.append((dest, True))
        sources.append((root, False))
        n = 0
        for base, everything in sources:
            for f in sorted(base.rglob("*")):
                rel = f.relative_to(base).parts
                if f.suffix.lower() not in IMAGE_EXTS or len(rel) < 2 or any(x[0] in "._" for x in rel):
                    continue
                if not everything and split not in rel[:-2]:
                    continue
                yield rel[-2], f.read_bytes()
                n += 1
        print(f"[prepare] {split}: {n} images", flush=True)


def image_ext(data):
    Image.open(io.BytesIO(data)).verify()
    fmt = Image.open(io.BytesIO(data)).format  # verify() leaves the image unusable, so reopen
    return {"JPEG": "jpg"}.get(fmt, (fmt or "").lower())


def readme_license(root):
    try:
        import yaml
        text = (root / "README.md").read_text(encoding="utf-8")
        lic = yaml.safe_load(text.split("---")[1]).get("license")
        return lic if isinstance(lic, (str, list)) else None
    except Exception:
        return None


def prepare(plan_path, out_dir):
    raw = Path(plan_path).read_bytes()
    plan = json.loads(raw)
    validate_plan(plan)
    if not os.path.isabs(out_dir):
        raise PlanError("--out-dir must be absolute")
    final, partial = Path(out_dir) / plan["name"], Path(out_dir) / f"{plan['name']}.partial"
    if final.exists():
        raise PlanError(f"dataset '{plan['name']}' already exists in {out_dir}; choose another name")

    root = download(plan)
    cap, rng, seen = plan["max_per_class"], random.Random(42), set()
    skipped = {"corrupt": 0, "duplicate": 0, "dropped": 0, "over_cap": 0}
    kept, total = {}, {}  # target class -> reservoir of (ext, bytes); target class -> valid images offered
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp:
        rows = parquet_rows(root, plan) if plan["layout"] == "parquet" else folder_rows(root, plan, tmp)
        for label, data in rows:
            if label not in plan["class_map"]:
                raise PlanError(f"label '{label}' is not in class_map")
            target = plan["class_map"][label]
            if target is None:
                skipped["dropped"] += 1
                continue
            try:
                ext = image_ext(data)
            except Exception:
                skipped["corrupt"] += 1
                continue
            digest = hashlib.sha256(data).digest()
            if digest in seen:
                skipped["duplicate"] += 1
                continue
            seen.add(digest)
            total[target] = total.get(target, 0) + 1
            res = kept.setdefault(target, [])
            if len(res) < cap:
                res.append((ext, data))
            else:  # reservoir sampling: a uniform, seed-deterministic sample without holding every image
                j = rng.randrange(total[target])
                if j < cap:
                    res[j] = (ext, data)
    skipped["over_cap"] = sum(total.values()) - sum(len(v) for v in kept.values())

    counts = {c: len(v) for c, v in sorted(kept.items())}
    if len(counts) < 2 or min(counts.values()) < MIN_PER_CLASS:
        raise PlanError(f"need at least 2 classes with {MIN_PER_CLASS}+ images each, got {counts}")

    shutil.rmtree(partial, ignore_errors=True)
    try:
        for c, items in kept.items():
            (partial / c).mkdir(parents=True)
            for n, (ext, data) in enumerate(items, 1):
                (partial / c / f"{n:06d}.{ext}").write_bytes(data)
        manifest = {"repo": plan["repo"], "revision": plan["revision"], "license": readme_license(root), "plan": plan,
                    "plan_sha256": hashlib.sha256(raw).hexdigest(), "counts": counts, "skipped": skipped,
                    "created": datetime.now(timezone.utc).isoformat()}
        (partial / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if final.exists():
            raise PlanError(f"dataset '{plan['name']}' already exists in {out_dir}")
        partial.rename(final)
    finally:
        shutil.rmtree(partial, ignore_errors=True)
    print(f"[prepare] counts {json.dumps(counts)} skipped {json.dumps(skipped)}", flush=True)
    return final


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, help="DatasetPlan JSON written by the web app")
    ap.add_argument("--out-dir", required=True, help="Absolute smart_curriculum_designer_datasets directory")
    args = ap.parse_args()
    try:
        print(f"[DATASET READY] {prepare(args.plan, args.out_dir)}")
    except Exception as e:
        print(f"[DATASET FAILED] {e if isinstance(e, PlanError) else f'{type(e).__name__}: {e}'}")
        sys.exit(1)


if __name__ == "__main__":
    main()
