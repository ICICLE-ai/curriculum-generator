"""Quality gates between Phase 2 steps (dev/plans/quality_gates.md, Phase 2): plain code checks of what each step
produced. Log-only: findings go to the week log, the PROV trace and <module>_gates.json, and never change generation.
A later phase lets each gate that proves accurate request one repair. A gate's own error is recorded, never raised.

    G1 contract  after Agent 0     milestones, components, every objective taught by a milestone
    G2 tests     after QA           every component and objective tested; no run-bookkeeping or structure-only tests
    G3 scaffold  after starter code the step-by-step TODO check: student work unlocks the tests gradually
    G4 numbers   after lesson plan  slide numbers match the run's telemetry; no impossible metrics
"""
import ast
import math
import re
import time
from typing import Any, Callable, Dict, List, Optional, Sequence

from digitalagedu.core.llm.generation_trace import now_iso

MODE = "log"  # "log" or "off"; execution.quality_gates, set per week by configure()
RECORDS: List[Dict[str, Any]] = []  # this week's gate results, written to <module>_gates.json by week_builder


def configure(mode: Optional[str]) -> None:
    """Starts a week: sets the mode and clears the previous week's records (weeks run one per process, or in turn)."""
    global MODE
    MODE = mode or "log"
    RECORDS.clear()


def _finding(gate: str, check: str, message: str) -> Dict[str, str]:
    return {"gate": gate, "check": check, "message": message}


def run_gate(name: str, check: Callable[[], List[Dict[str, str]]], trace=None) -> List[Dict[str, str]]:
    """Runs one gate and records its findings; an error inside the gate becomes a `gate_error` finding."""
    if MODE == "off":
        return []
    start, started = now_iso(), time.monotonic()
    try:
        findings = check()
    except Exception as err:
        findings = [_finding(name, "gate_error", repr(err)[:300])]
    seconds = round(time.monotonic() - started, 1)
    summary = "no findings" if not findings else f"{len(findings)} finding(s): " + " | ".join(f["message"] for f in findings)
    print(f"  -> [Gate {name}, {MODE}] {summary[:1000]} ({seconds:.0f}s)")
    if trace is not None:
        trace.add_activity("gate", "quality_gate", start=start, gate=name, mode=MODE,
                           findings=[f"{f['check']}: {f['message']}" for f in findings])
    RECORDS.append({"gate": name, "seconds": seconds, "findings": findings})
    return findings


# ---- G1 contract -------------------------------------------------------------------------------------------------

def contract_gate(formulation: Any) -> List[Dict[str, str]]:
    """Agent 0's contract: 3 milestones with components, and every learning objective taught by one (objective_indices).
    AgentZeroContract re-asks for the structure; this also covers contracts that skipped it (e.g. revisions)."""
    milestones = getattr(formulation, "milestone_subsystems", None) or []
    objectives = getattr(formulation, "learning_objectives", None) or []
    out = []
    if len(milestones) < 3:
        out.append(_finding("G1", "milestones", f"{len(milestones)} milestone subsystems; the prompt asks for 3"))
    for m in milestones:
        if not m.components:
            out.append(_finding("G1", "empty_milestone", f"milestone {m.milestone_num} '{m.title}' has no components"))
    taught = {i for m in milestones for i in (getattr(m, "objective_indices", None) or [])}
    untaught = [i for i in range(len(objectives)) if i not in taught]
    if untaught:
        out.append(_finding("G1", "untaught_objectives", "objectives taught by no milestone: "
                            + "; ".join(f"{i}. {objectives[i][:80]}" for i in untaught)))
    return out


# ---- G2 tests ----------------------------------------------------------------------------------------------------

# Run bookkeeping a student can't compute from the exercise's files (QA requirement 5)
_BOOKKEEPING = re.compile(r"(^|_)(seed|runtime|duration|elapsed|timestamp|run_id|job_id|uuid|hash|sha256|"
                          r"num_workers|workers|gpus?|hours|wall_?time)($|_)", re.IGNORECASE)
_STRUCT_CALLS = {"isinstance", "hasattr", "callable", "type", "len", "set", "sorted", "list", "tuple", "dict", "frozenset"}
_STRUCT_ATTRS = {"shape", "dtype", "ndim", "keys", "size"}
_STRUCT_OPS = (ast.In, ast.NotIn, ast.Is, ast.IsNot)


def _test_functions(tree: ast.Module) -> List[ast.AST]:
    funcs = (ast.FunctionDef, ast.AsyncFunctionDef)
    found = [n for n in tree.body if isinstance(n, funcs) and n.name.startswith("test_")]
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        found += [n for n in cls.body if isinstance(n, funcs) and n.name.startswith("test_")]
    return found


def _shape_term(node: ast.AST) -> bool:
    """A length, type, shape or key set: len(x), isinstance(...), set(d.keys()), a.shape, a.dtype."""
    if isinstance(node, ast.Call):
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        return name in _STRUCT_CALLS or name == "keys"
    return isinstance(node, ast.Attribute) and node.attr in _STRUCT_ATTRS


def _plain(node: ast.AST) -> bool:
    """What a structure check compares against: a name, a constant, a literal collection, or np.float32-style types."""
    return (isinstance(node, (ast.Name, ast.Constant, ast.Set, ast.List, ast.Tuple))
            or isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name))


def _structural_assert(node: ast.Assert) -> bool:
    """True when the assert checks only structure (types, lengths, shapes, key sets, membership, None), not a value:
    `assert len(rows) == 500` is structural, `assert x == 2` and `assert abs(a - b) < 0.1` are not.
    shortcut: syntactic heuristic over `assert` statements (unittest self.assert* calls are not inspected); it feeds
    a log-only gate whose false-alarm rate is measured before it may trigger repairs."""
    test = node.test
    if isinstance(test, ast.Call):
        return _shape_term(test)
    if isinstance(test, ast.Compare):
        if all(isinstance(op, _STRUCT_OPS) for op in test.ops):
            return True
        sides = [test.left, *test.comparators]
        return any(_shape_term(s) for s in sides) and all(_shape_term(s) or _plain(s) for s in sides)
    return False


def tests_gate(test_code: str, formulation: Any) -> List[Dict[str, str]]:
    """The QA test file: every contract component called, every objective named by a test's docstring
    ("Objective <i>:"), no asserts on run bookkeeping, no test whose asserts all check only structure."""
    try:
        tree = ast.parse(test_code)
    except SyntaxError as err:
        return [_finding("G2", "syntax", f"test file does not parse: {err}")]
    out = []
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    components = [c.name for m in (getattr(formulation, "milestone_subsystems", None) or []) for c in m.components]
    untested = [c for c in components if c not in used]
    if untested:
        out.append(_finding("G2", "untested_components", f"{len(untested)} of {len(components)} contract components "
                            f"are never called by a test: {', '.join(untested)}"))

    tests = _test_functions(tree)
    named = {int(i) for t in tests for i in re.findall(r"Objective\s+(\d+)", ast.get_docstring(t) or "")}
    objectives = getattr(formulation, "learning_objectives", None) or []
    unassessed = [i for i in range(len(objectives)) if i not in named]
    if unassessed:
        out.append(_finding("G2", "unassessed_objectives", "no test docstring names objective(s) "
                            + ", ".join(str(i) for i in unassessed) + " (QA requirement 4: 'Objective <i>:')"))

    for t in tests:
        asserts = [n for n in ast.walk(t) if isinstance(n, ast.Assert)]
        keys = sorted({s for a in asserts for n in ast.walk(a.test)  # the condition, not the failure message
                       for s in ([n.value] if isinstance(n, ast.Constant) and isinstance(n.value, str) else
                                 [n.attr] if isinstance(n, ast.Attribute) else [])
                       if _BOOKKEEPING.search(s)})
        if keys:
            out.append(_finding("G2", "bookkeeping_assert", f"{t.name} asserts run bookkeeping: {', '.join(keys)}"))
        if asserts and all(_structural_assert(a) for a in asserts):
            out.append(_finding("G2", "structure_only", f"{t.name} checks only types, lengths, shapes or keys"))
    return out


# ---- G3 scaffold -------------------------------------------------------------------------------------------------

def scaffold_gate(starter: str, solution: str, shipped_tests: str, module_id: str,
                  fixture_dirs: Sequence[str] = (), timeout: int = 120) -> List[Dict[str, str]]:
    """The step-by-step TODO check (eval/scaffold.py) on the starter: one sandbox run per student function."""
    from digitalagedu.core.eval import scaffold
    result = scaffold.check(starter, solution, shipped_tests, module_id, fixture_dirs, timeout)
    if result.get("error"):
        return [_finding("G3", "error", result["error"])]
    f, stubs = result["flags"], result["stubs"]
    out = []
    if f["no_stubs"]:
        out.append(_finding("G3", "no_student_work", "the starter leaves no function for the student to write"))
    if f["pass_without_student_work"]:
        out.append(_finding("G3", "passes_without_work", "tests passing on the bare starter (they assess nothing the "
                            f"student writes): {', '.join(f['pass_without_student_work'])}"))
    if f["fail_with_all_filled"]:
        out.append(_finding("G3", "fails_when_complete", "tests failing with every student function filled from the "
                            f"solution (the starter's fixed code differs): {', '.join(f['fail_with_all_filled'])}"))
    if stubs and len(f["steps_unlocking_nothing"]) > len(stubs) / 2:
        out.append(_finding("G3", "little_feedback", f"{len(f['steps_unlocking_nothing'])} of {len(stubs)} student "
                            f"functions make no new test pass: {', '.join(f['steps_unlocking_nothing'])}"))
    if f["regressions"]:
        out.append(_finding("G3", "regressions", f"tests that pass, then fail after a later step: {', '.join(f['regressions'])}"))
    if f["timed_out_steps"]:
        out.append(_finding("G3", "timeouts", f"{f['timed_out_steps']} step(s) timed out after {timeout} s; their results are unknown"))
    return out


# ---- G4 numbers --------------------------------------------------------------------------------------------------

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _telemetry_numbers(obj: Any, found: Optional[set] = None, depth: int = 0) -> set:
    """Every number in the telemetry, plus the size of every dict and list (class counts, row counts)."""
    found = set() if found is None else found
    if depth > 8:
        return found
    if isinstance(obj, bool):
        return found
    if isinstance(obj, (int, float)) and math.isfinite(obj):
        found.add(float(obj))
    elif isinstance(obj, dict):
        found.add(float(len(obj)))
        for v in obj.values():
            _telemetry_numbers(v, found, depth + 1)
    elif isinstance(obj, (list, tuple)):
        found.add(float(len(obj)))
        for v in obj[:2000]:
            _telemetry_numbers(v, found, depth + 1)
    return found


def _matches(text: str, known: set) -> bool:
    """A displayed number matches a telemetry value within its own rounding, as is or as a percentage."""
    decimals = len(text.split(".")[1]) if "." in text else 0
    shown, tol = float(text), 0.5 * 10 ** -decimals + 1e-9
    return any(abs(shown - k) <= tol or abs(shown - 100 * k) <= tol or abs(shown - k / 100) <= tol for k in known)


def _slide_text(slide: Any) -> str:
    parts = [slide.title, slide.explanation, *slide.on_slide_text, *(f"{e.label} {e.value} {e.context}" for e in slide.evidence)]
    return " ".join(p for p in parts if p)


def numbers_gate(plan: Any, telemetry: Dict[str, Any]) -> List[Dict[str, str]]:
    """The lesson plan's evidence numbers (the slides' "real numbers") against the run's telemetry, and impossible
    metric statements in any slide text (recall 0 with F1 above 0, percentages over 100)."""
    known = _telemetry_numbers(telemetry or {})
    out = []
    for i, slide in enumerate(plan.slides, 1):
        for e in slide.evidence:
            nums = _NUM.findall(e.value)
            if nums and known and not _matches(nums[0], known):
                out.append(_finding("G4", "unknown_number", f"slide {i} '{slide.title[:50]}': evidence "
                                    f"'{e.label}: {e.value}' matches no value in the run's telemetry"))
        text = _slide_text(slide)
        zero_recall = re.search(r"recall\W{0,4}(?:=|of|is|:)?\s*0(?:\.0+)?(?![\d.])", text, re.IGNORECASE)
        some_f1 = re.search(r"F1\W{0,4}(?:=|of|is|:)?\s*0?\.\d*[1-9]", text)
        if zero_recall and some_f1:
            out.append(_finding("G4", "impossible_metric", f"slide {i} '{slide.title[:50]}' shows recall 0 next to "
                                "an F1 above 0 (F1 is 0 whenever recall is 0)"))
        over = [p for p in re.findall(r"(\d+(?:\.\d+)?)\s*%", text) if float(p) > 100]
        if over:
            out.append(_finding("G4", "impossible_metric", f"slide {i} '{slide.title[:50]}' shows percentages over 100: {', '.join(over)}"))
    return out
