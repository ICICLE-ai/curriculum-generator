"""
W3C PROV-JSON generation trace for Phase 2 (https://www.w3.org/submissions/prov-json/).

Records every LLM call, code version, compile check, sandbox run and repair for one module,
linked to the Phase 1 artifacts they used. Full prompt/reply/code text lives under <module>/trace/
and each entity carries the SHA-256 of its file, so the trace is verifiable proof of what happened.
"""
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from digitalagedu.core.artifact_validator import compute_file_sha256

PREFIX = {"prov": "http://www.w3.org/ns/prov#", "dage": "https://digitalagedu.org/ns/prov#"}
RELATIONS = ("wasGeneratedBy", "used", "wasAssociatedWith", "wasDerivedFrom", "wasInformedBy", "wasAttributedTo")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class GenerationTrace:
    """PROV-JSON document for one module; ids are auto-numbered, code kinds are versioned (solution_v1, _v2...)."""

    def __init__(self, module_dir: str, module_id: str, model_name: str,
                 workflow_run_id: Optional[str] = None, manifest: Optional[List[Dict[str, Any]]] = None):
        self.module_dir, self.module_id, self.model_name = module_dir, module_id, model_name
        self.trace_dir = os.path.join(module_dir, "trace")
        os.makedirs(self.trace_dir, exist_ok=True)
        self.doc: Dict[str, Any] = {"prefix": PREFIX, "entity": {}, "activity": {}, "agent": {}}
        self.doc.update({rel: {} for rel in RELATIONS})
        self.latest: Dict[str, str] = {}  # kind -> id of its newest version
        self._counts: Counter = Counter()
        self._manifest = {str(a.get("name")): a for a in (manifest or [])}
        self.add_entity("module", module_id=module_id, workflow_run_id=workflow_run_id)

    def _next_id(self, kind: str) -> str:
        self._counts[kind] += 1
        return f"dage:{kind}_{self._counts[kind]:03d}"

    def add_entity(self, kind: str, /, content: Optional[str] = None, ext: str = "txt",
                   versioned: bool = False, **attrs) -> str:
        """Adds an entity; `content` is written to trace/ and hashed. Versioned kinds get ids like dage:solution_v2."""
        if versioned:
            self._counts[kind] += 1
            eid = f"dage:{kind}_v{self._counts[kind]}"
            self.latest[kind] = eid
        else:
            eid = self._next_id(kind)
        record = {"prov:type": f"dage:{kind}", **{f"dage:{k}": v for k, v in attrs.items() if v is not None}}
        if content is not None:
            rel_path = f"trace/{eid.split(':', 1)[1]}.{ext}"
            # newline="" keeps the bytes on disk identical to the hashed text on every OS
            with open(os.path.join(self.module_dir, rel_path), "w", encoding="utf-8", newline="") as f:
                f.write(content)
            record.update({"dage:path": rel_path, "dage:sha256": _sha256_text(content)})
        self.doc["entity"][eid] = record
        return eid

    def agent(self, name: str) -> str:
        aid = f"dage:{name}"
        self.doc["agent"].setdefault(aid, {
            "prov:type": "prov:SoftwareAgent",
            "dage:model": "python subprocess" if name == "sandbox" else self.model_name,
        })
        return aid

    def add_activity(self, kind: str, agent: Optional[str] = None, start: Optional[str] = None, **attrs) -> str:
        aid = self._next_id(kind)
        self.doc["activity"][aid] = {
            "prov:type": f"dage:{kind}", "prov:startTime": start or now_iso(), "prov:endTime": now_iso(),
            **{f"dage:{k}": v for k, v in attrs.items() if v is not None},
        }
        if agent:
            self.relate("wasAssociatedWith", activity=aid, agent=self.agent(agent))
        return aid

    def relate(self, relation: str, **ids: str) -> None:
        """PROV-JSON relation record, e.g. relate('wasDerivedFrom', generatedEntity=a, usedEntity=b)."""
        rel = self.doc[relation]
        rel[f"_:{relation}{len(rel) + 1}"] = {f"prov:{k}": v for k, v in ids.items()}

    def file(self, path: str) -> str:
        """Entity for a file on disk (once per path). Phase 1 manifest files reuse their artifact id
        and record whether the file still matches the manifest checksum."""
        name = os.path.basename(path)
        art = self._manifest.get(name)
        eid = f"dage:artifact_{art['artifact_id']}" if art and art.get("artifact_id") else f"dage:file_{re.sub(r'[^A-Za-z0-9_]', '_', name)}"
        if eid not in self.doc["entity"]:
            sha = compute_file_sha256(path)
            record = {"prov:type": "dage:phase1_artifact" if art else "dage:file", "dage:name": name, "dage:sha256": sha}
            if art and art.get("sha256"):
                record["dage:matches_manifest_sha256"] = art["sha256"] == sha
            self.doc["entity"][eid] = record
        return eid

    def path(self) -> str:
        return os.path.join(self.module_dir, f"{self.module_id.replace('-', '_')}_generation_trace.json")

    def save(self) -> str:
        with open(self.path(), "w", encoding="utf-8") as f:
            json.dump(self.doc, f, indent=2)
        return self.path()


_BLOCK = re.compile(r"^(ERROR|FAIL): (\S+)[^\n]*\n-{20,}\n(.*?)(?=^={20,}|^-{20,}\nRan |\Z)", re.MULTILINE | re.DOTALL)
_FRAME = re.compile(r'File "([^"]+)", line (\d+)')


def _attribute(test: str, body: str, contract_names: Iterable[str]) -> Dict[str, Any]:
    """Blames one traceback on the test file or the solution, from its deepest frame in either file."""
    frames = [(f, int(n)) for f, n in _FRAME.findall(body)
              if os.path.basename(f) == "test_runner.py" or f.endswith("solution.py")]
    exc_lines = [l for l in body.splitlines()
                 if l and not l[0].isspace() and not l.startswith(("Traceback", "The above", "During handling"))]
    exception = exc_lines[-1].strip() if exc_lines else body.strip()[-200:]
    file, line = frames[-1] if frames else (None, None)
    missing = re.search(r"name '(\w+)' is not defined|cannot import name '(\w+)'", exception)
    if file is None:
        blame = "environment"
    elif file.endswith("solution.py"):
        blame = "solution"
    elif exception.startswith("AssertionError"):
        blame = "contract_mismatch"  # TDD: the test is the spec, so the solution must change
    else:
        # A contract symbol the test expects but the solution never defined is the solution's fault
        blame = "solution" if missing and (missing.group(1) or missing.group(2)) in set(contract_names) else "test"
    return {"test": test, "exception": exception, "file": os.path.basename(file) if file else None,
            "line": line, "blame": blame, "kind": _kind(exception, blame, missing)}


def _kind(exception: str, blame: str, missing) -> str:
    """Issue class used to pick the repair hint and the escalation path (see self_healing.FIX_HINTS)."""
    if "timed out" in exception:
        return "timeout"
    if exception.startswith("FileNotFoundError"):
        return "missing_fixture"
    if exception.startswith(("ModuleNotFoundError", "ImportError")) and "_solution" not in exception and not missing:
        return "missing_package"
    if missing and blame == "solution":
        return "missing_symbol"
    if blame == "contract_mismatch":
        return "contract_mismatch"
    return "test_error" if blame == "test" else "solution_error"


def signature(failure: Dict[str, Any]) -> tuple:
    """Identity of a failure across rounds: the same test failing with the same exception type."""
    return failure["test"], failure["exception"].split(":", 1)[0]


def attribute_failures(log: str, contract_names: Iterable[str] = ()) -> List[Dict[str, Any]]:
    """Per-failure attribution of a sandbox log: unittest ERROR/FAIL blocks, else the whole script traceback."""
    contract_names = list(contract_names)
    blocks = _BLOCK.findall(log or "")
    if blocks:
        return [_attribute(test, body, contract_names) for _, test, body in blocks]
    return [_attribute("<script>", log or "", contract_names)]
