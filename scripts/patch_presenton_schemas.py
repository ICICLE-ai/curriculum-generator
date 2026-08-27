#!/usr/bin/env python3
"""
Sanitizes all JSON schemas in Presenton to ensure compatibility with vLLM outlines guided decoding.
Converts any `"type": ["type1", "type2"]` into `"anyOf": [{"type": "type1"}, {"type": "type2"}]`.
"""

import os
import re
import json
import glob

def sanitize_dict_schema(obj):
    if isinstance(obj, dict):
        if "type" in obj and isinstance(obj["type"], list):
            types = obj.pop("type")
            obj["anyOf"] = [{"type": t} for t in types]
        for k, v in list(obj.items()):
            obj[k] = sanitize_dict_schema(v)
        return obj
    elif isinstance(obj, list):
        return [sanitize_dict_schema(x) for x in obj]
    return obj

def patch_llm_utils(file_path: str):
    if not os.path.exists(file_path):
        print(f"[SKIP] {file_path} not found")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already patched
    if "def _sanitize_vllm_schema" in content:
        print(f"[OK] {file_path} already patched")
        return

    sanitizer_func = '''
def _sanitize_vllm_schema(obj):
    """Recursively converts 'type': ['a', 'b'] to 'anyOf': [{'type': 'a'}, {'type': 'b'}] for vLLM outlines compatibility."""
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if k == "type" and isinstance(v, list):
                new_obj["anyOf"] = [{"type": t} for t in v]
            else:
                new_obj[k] = _sanitize_vllm_schema(v)
        return new_obj
    elif isinstance(obj, list):
        return [_sanitize_vllm_schema(x) for x in obj]
    return obj
'''

    # Inject sanitizer at top of llm_utils.py
    patched = sanitizer_func + "\n" + content

    # Hook into _generate_structured_content and generate_structured_with_schema_retries
    patched = re.sub(
        r'(async def _generate_structured_content\([^)]*?\):)',
        r'\1\n    schema = _sanitize_vllm_schema(schema) if "schema" in locals() and schema else schema',
        patched
    )
    patched = re.sub(
        r'(async def generate_structured_with_schema_retries\([^)]*?\):)',
        r'\1\n    schema = _sanitize_vllm_schema(schema) if "schema" in locals() and schema else schema',
        patched
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(patched)
    print(f"[SUCCESS] Patched schema sanitizer in {file_path}")


def patch_all_json_files(root_dir: str):
    """Sanitizes all JSON template files to use anyOf instead of array types."""
    if not os.path.exists(root_dir):
        return
    count = 0
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".json"):
                full_p = os.path.join(root, f)
                try:
                    with open(full_p, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                    sanitized = sanitize_dict_schema(data)
                    with open(full_p, "w", encoding="utf-8") as jf:
                        json.dump(sanitized, jf, indent=2)
                    count += 1
                except Exception:
                    pass
    print(f"[SUCCESS] Sanitized {count} JSON schema files in {root_dir}")


def patch_export_urls(root_dir: str):
    """Ensures all export tasks route to port 5001 instead of default port 80."""
    if not os.path.exists(root_dir):
        return
    count = 0
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith((".py", ".js", ".cjs", ".ts", ".json")):
                full_p = os.path.join(root, f)
                try:
                    with open(full_p, "r", encoding="utf-8") as file:
                        text = file.read()
                    
                    new_text = text
                    # Replace hardcoded port 80 pdf-maker URLs
                    new_text = re.sub(r'http://127\.0\.0\.1/pdf-maker', 'http://127.0.0.1:5001/pdf-maker', new_text)
                    new_text = re.sub(r'http://localhost/pdf-maker', 'http://127.0.0.1:5001/pdf-maker', new_text)
                    new_text = re.sub(r'http://127\.0\.0\.1:80/pdf-maker', 'http://127.0.0.1:5001/pdf-maker', new_text)
                    
                    # If file is index.cjs, ensure URL rewriting is injected for any url missing port
                    if f == "index.cjs" and "url.replace('http://127.0.0.1/pdf-maker'" not in new_text:
                        new_text = "process.env.PORT = process.env.PORT || '5001';\n" + new_text
                        new_text = re.sub(
                            r'(async function\s*\w*\s*\([^)]*?\)\s*\{)',
                            r"\1\n  if (typeof task !== 'undefined' && task.url) { task.url = task.url.replace('http://127.0.0.1/pdf-maker', 'http://127.0.0.1:5001/pdf-maker').replace('http://localhost/pdf-maker', 'http://127.0.0.1:5001/pdf-maker'); }",
                            new_text,
                            count=1
                        )

                    if new_text != text:
                        with open(full_p, "w", encoding="utf-8") as file:
                            file.write(new_text)
                        count += 1
                except Exception:
                    pass
    print(f"[SUCCESS] Patched {count} export URL references to port 5001 in {root_dir}")


if __name__ == "__main__":
    presenton_dir = os.environ.get("PRESENTON_DIR", "/app/presenton")
    fastapi_utils = os.path.join(presenton_dir, "servers", "fastapi", "utils", "llm_utils.py")
    patch_llm_utils(fastapi_utils)
    patch_all_json_files(presenton_dir)
    patch_export_urls(presenton_dir)

