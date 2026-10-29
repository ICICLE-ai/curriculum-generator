"""
Escalating sandbox self-healing for Phase 2.

Each failure signature (test, exception type) climbs a ladder:
  1. routed by issue kind to the QA agent or the coder, with a kind-specific fix hint;
  2. still failing after that repair -> the Arbiter rules on fault (test / solution / contract) and directs the repair;
  3. contract at fault, or still failing after the Arbiter-directed repair -> ContractRevisionNeeded (Agent 0 revises).
Every sandbox run, routing decision, ruling and repair is recorded in the module's PROV trace.
"""
import os
from typing import Any, Dict, List, Optional

from digitalagedu.core.llm.ai_setup import ask_code
from digitalagedu.core.llm.context import build_system_prompt
from digitalagedu.core.llm.generation_trace import GenerationTrace, attribute_failures, now_iso, signature
from digitalagedu.core.llm.sandbox import run_in_sandbox
from digitalagedu.core.llm.schemas import ArbiterVerdictSchema

MAX_SELF_HEAL_ROUNDS = 3
SANDBOX_PACKAGES = "numpy, pandas, scipy, scikit-learn, scikit-image, matplotlib, pillow, opencv, torch, torchvision"

FIX_HINTS = {
    "missing_fixture": "A file was not found. Use only these real files and folders:\n{fixtures}",
    "missing_package": "A module could not be imported. Use only installed packages: {packages}.",
    "missing_symbol": "The solution must define exactly these contract symbols at module level: {symbols}.",
    "missing_import": "A name is used without being imported. Add the import at the top of the file "
                      "(e.g. `from typing import Any, Union`, `import numpy as np`).",
    "api_mismatch": "The installed library version renamed or removed a name. Use exactly the replacement suggested "
                    "under the failure (your training data may show an older API).",
    "contract_mismatch": "The unit test is the specification: match the return types, keys and values it asserts.",
    "timeout": "The sandbox kills runs after 120 s: subsample data and avoid loops over the full dataset.",
}


class ContractRevisionNeeded(Exception):
    """The Arbiter put the fault on the contract, or a failure survived an Arbiter-directed repair."""

    def __init__(self, verdict: ArbiterVerdictSchema, verdict_entity: str, failures: List[Dict[str, Any]],
                 log: str, escalations: List[Dict[str, Any]]):
        super().__init__(f"Contract revision needed: {verdict.rationale}")
        self.verdict, self.verdict_entity, self.failures, self.log, self.escalations = (
            verdict, verdict_entity, failures, log, escalations
        )

    def feedback(self) -> str:
        """Agent 0 revision request text."""
        return (
            f"ARBITER RULING ({self.verdict.fault}): {self.verdict.rationale}\n"
            f"DIRECTIVE: {self.verdict.fix_directive}\n"
            f"UNRESOLVED FAILURES:\n{format_failures(self.failures)}"
        )


def contract_names(problem_formulation: Any) -> List[str]:
    """Symbols the subsystem contract promises the solution defines (components + orchestrator)."""
    names = [c.name for sub in (getattr(problem_formulation, "milestone_subsystems", None) or []) for c in sub.components]
    orchestrator_sig = getattr(problem_formulation, "pipeline_orchestrator_signature", "") or ""
    return names + [orchestrator_sig.split("(")[0].replace("def ", "").strip()]


def format_failures(failures: List[Dict[str, Any]], hint_context: Optional[Dict[str, str]] = None) -> str:
    """Failure list for a repair prompt, followed by one fix hint per issue kind present."""
    lines = [
        f"- {f['test']}: {f['exception']} ({f['file']}:{f['line']}) [{f.get('kind')}]"
        + (f"\n    -> {f['suggestion']}" if f.get("suggestion") else "")
        for f in failures
    ]
    if hint_context:
        hints = dict.fromkeys(FIX_HINTS[f["kind"]].format(**hint_context) for f in failures if f.get("kind") in FIX_HINTS)
        if hints:
            lines += ["", "FIX HINTS:"] + [f"- {h}" for h in hints]
    return "\n".join(lines)


def _side(failure: Dict[str, Any]) -> str:
    return "test" if failure["blame"] == "test" else "solution"


def arbitrate(client, model_name: str, problem_formulation: Any, unit_test: str, solution_code: str,
              stuck: List[Dict[str, Any]], trace: GenerationTrace, used: List[str], fixture_note: str = ""):
    """Structured ruling on failures that survived a repair; recorded as an `arbitration` activity + `verdict` entity."""
    contract = problem_formulation.model_dump_json(
        indent=2, include={"problem_statement", "milestone_subsystems", "pipeline_orchestrator_signature",
                           "target_input_shape", "target_output_shape"}
    )
    prompt = (
        "You are the Verification Arbiter for a test-driven code generation pipeline.\n"
        "The unit tests and the reference solution below keep disagreeing on the listed failures even after a repair.\n"
        "Rule which side is wrong according to the CONTRACT (the contract is the source of truth for both):\n"
        "- 'test': the test asserts behaviour, types or data the contract does not require.\n"
        "- 'solution': the solution violates the contract or a contract-consistent test.\n"
        "- 'contract': the contract is ambiguous (e.g. no return type) or infeasible with the available data.\n\n"
        f"--- CONTRACT ---\n{contract}\n\n"
        f"--- {fixture_note.strip() or 'SANDBOX FIXTURES: unknown'} ---\n\n"
        f"--- UNIT TESTS ---\n```python\n{unit_test}\n```\n\n"
        f"--- REFERENCE SOLUTION ---\n```python\n{solution_code}\n```\n\n"
        f"--- FAILURES THAT SURVIVED A REPAIR ---\n{format_failures(stuck)}\n"
    )
    start = now_iso()
    verdict, completion = client.chat.completions.create_with_completion(
        model=model_name,
        response_model=ArbiterVerdictSchema,
        max_retries=2,
        max_tokens=2048,
        messages=[{"role": "system", "content": build_system_prompt()}, {"role": "user", "content": prompt}],
    )
    usage = getattr(completion, "usage", None)
    act = trace.add_activity(
        "arbitration", "arbiter", start=start, model=model_name, fault=verdict.fault,
        prompt_tokens=getattr(usage, "prompt_tokens", None), completion_tokens=getattr(usage, "completion_tokens", None),
    )
    prompt_entity = trace.add_entity("prompt", prompt, ext="md")
    verdict_entity = trace.add_entity("verdict", verdict.model_dump_json(indent=2), ext="json", fault=verdict.fault)
    trace.relate("wasGeneratedBy", entity=verdict_entity, activity=act)
    for source in [prompt_entity, *used]:
        trace.relate("used", activity=act, entity=source)
        trace.relate("wasDerivedFrom", generatedEntity=verdict_entity, usedEntity=source)
    return verdict, verdict_entity


def verify_with_self_healing(client, code_client, model_name: str, module: Any, problem_formulation: Any,
                             qa_prompt: str, exercise_prompt: str, unit_test: str, solution_code: str,
                             artifact_source_dirs: List[str], trace: GenerationTrace, fixture_note: str = ""):
    """Sandbox verification with the escalation ladder above.
    Returns (success, log, failures, escalations, unit_test, solution_code); raises ContractRevisionNeeded."""
    contract = contract_names(problem_formulation)
    fixture_paths = [
        os.path.join(d, name)
        for d in artifact_source_dirs for name in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, name))
    ]
    fixtures = [trace.file(p) for p in fixture_paths]
    hint_context = {
        "fixtures": fixture_note.strip() or ", ".join(os.path.basename(p) for p in fixture_paths) or "none",
        "packages": SANDBOX_PACKAGES,
        "symbols": ", ".join(contract),
    }
    escalations: List[Dict[str, Any]] = []
    level: Dict[tuple, int] = {}  # signature -> ladder step reached (1 routed, 2 arbitrated)
    verdicts: Dict[tuple, tuple] = {}  # signature -> (verdict, verdict entity)
    previous: set = set()  # signatures failing in the run before the current one
    # Only a failure carried over from the previous run climbs the ladder; a fixed one that comes back restarts at 1.
    # Library API mismatches never climb: neither the Arbiter nor a contract revision can fix a renamed function.
    carried = lambda f: signature(f) in previous and f.get("kind") != "api_mismatch"

    def verify(heal_round: int):
        start = now_iso()
        success, log = run_in_sandbox(solution_code, unit_test, module_id=module.id, artifact_sources=artifact_source_dirs)
        failures = [] if success else attribute_failures(log, contract)
        run = trace.add_activity("sandbox_run", "sandbox", start=start, round=heal_round, verified=success)
        for entity in [trace.latest["solution"], trace.latest["unit_test"], *fixtures]:
            trace.relate("used", activity=run, entity=entity)
        log_entity = trace.add_entity("sandbox_log", log, verified=success, failure_count=len(failures))
        trace.relate("wasGeneratedBy", entity=log_entity, activity=run)
        for failure in failures:
            trace.relate("wasDerivedFrom", generatedEntity=trace.add_entity("failure", **failure), usedEntity=log_entity)
        return success, log, failures, run, log_entity

    def escalate(heal_round: int, step: int, to_agent: str, reason: str, failures: List[Dict[str, Any]], run: str):
        sigs = "; ".join(f"{t} [{e}]" for t, e in map(signature, failures))
        act = trace.add_activity("escalation", "orchestrator", round=heal_round, level=step, to_agent=to_agent,
                                 reason=reason, signatures=sigs)
        trace.relate("wasInformedBy", informed=act, informant=run)
        escalations.append({"round": heal_round, "level": step, "to_agent": to_agent, "reason": reason, "signatures": sigs})
        print(f"  -> [Escalation L{step}] {to_agent}: {reason} ({sigs})")

    def revision_needed(heal_round, failures, run, log):
        verdict, verdict_entity = verdicts[signature(failures[0])]
        escalate(heal_round, 3, "agent0_director", "failure survived an Arbiter-directed repair", failures, run)
        return ContractRevisionNeeded(verdict, verdict_entity, failures, log, escalations)

    success, log, failures, run, log_entity = verify(0)
    for heal_round in range(1, MAX_SELF_HEAL_ROUNDS + 1):
        if success:
            break
        print(f"  -> Sandbox verification failed (self-healing round {heal_round}/{MAX_SELF_HEAL_ROUNDS}).")
        exhausted = [f for f in failures if carried(f) and level.get(signature(f)) == 2]
        if exhausted:
            raise revision_needed(heal_round, exhausted, run, log)

        to_fix: Dict[str, List[Dict[str, Any]]] = {"test": [], "solution": []}
        directives: Dict[str, List[str]] = {"test": [], "solution": []}
        evidence: Dict[str, List[str]] = {"test": [log_entity], "solution": [log_entity]}

        fresh = [f for f in failures if not carried(f)]
        for f in fresh:
            level[signature(f)] = 1
            to_fix[_side(f)].append(f)

        stuck = [f for f in failures if carried(f) and level.get(signature(f)) == 1]
        if stuck:
            escalate(heal_round, 2, "arbiter", "failure survived a repair aimed at its side", stuck, run)
            verdict, verdict_entity = arbitrate(
                client, model_name, problem_formulation, unit_test, solution_code, stuck, trace,
                used=[log_entity, trace.latest["unit_test"], trace.latest["solution"]], fixture_note=fixture_note,
            )
            for f in stuck:
                level[signature(f)] = 2
                verdicts[signature(f)] = (verdict, verdict_entity)
            if verdict.fault == "contract":
                escalate(heal_round, 3, "agent0_director", "Arbiter ruled the contract at fault", stuck, run)
                raise ContractRevisionNeeded(verdict, verdict_entity, stuck, log, escalations)
            to_fix[verdict.fault] += stuck
            directives[verdict.fault].append(f"ARBITER RULING: {verdict.rationale}\nDIRECTIVE: {verdict.fix_directive}")
            evidence[verdict.fault].append(verdict_entity)

        if to_fix["solution"]:
            kinds = sorted({f["kind"] for f in to_fix["solution"]})
            escalate(heal_round, max(level[signature(f)] for f in to_fix["solution"]), "agent1_coder", f"kinds: {', '.join(kinds)}", to_fix["solution"], run)
            solution_code = ask_code(code_client, model_name, [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": (
                    f"{exercise_prompt}\n\n"
                    f"--- PREVIOUS SANDBOX EXECUTION FAILURE LOG ---\n{log}\n\n"
                    f"--- FAILURES ATTRIBUTED TO YOUR SOLUTION ---\n{format_failures(to_fix['solution'], hint_context)}\n\n"
                    + "".join(f"{d}\n\n" for d in directives["solution"]) +
                    f"CRITICAL FIX DIRECTIVE:\n"
                    f"Your previous solution failed during execution. Fix the errors above:\n"
                    f"1. Explicitly import all used libraries and functions at the top.\n"
                    f"2. Load authentic workflow artifacts from disk fixtures.\n"
                    f"3. Ensure all subsystem component signatures and return types match the unit test expectations.\n"
                    f"Return the complete, working solution."
                )},
            ], "reference solution", trace=trace, agent="agent1_coder", artifact="solution",
                purpose="repair", used=evidence["solution"], informed_by=run)
        if to_fix["test"]:
            kinds = sorted({f["kind"] for f in to_fix["test"]})
            escalate(heal_round, max(level[signature(f)] for f in to_fix["test"]), "agent2_qa", f"kinds: {', '.join(kinds)}", to_fix["test"], run)
            unit_test = ask_code(code_client, model_name, [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": (
                    f"{qa_prompt}\n\n"
                    f"--- REFERENCE SOLUTION CODE ---\n{solution_code}\n\n"
                    f"--- PREVIOUS SANDBOX VERIFICATION LOG ---\n{log}\n\n"
                    f"--- FAILURES ATTRIBUTED TO YOUR TEST FILE ---\n{format_failures(to_fix['test'], hint_context)}\n\n"
                    + "".join(f"{d}\n\n" for d in directives["test"]) +
                    f"Please fix the unit test code to properly assert the solution without syntax or assertion errors."
                )},
            ], "unit test file", trace=trace, agent="agent2_qa", artifact="unit_test",
                purpose="repair", used=evidence["test"], informed_by=run)
        previous = {signature(f) for f in failures}
        success, log, failures, run, log_entity = verify(heal_round)

    if not success:
        exhausted = [f for f in failures if carried(f) and level.get(signature(f)) == 2]
        if exhausted:
            raise revision_needed(MAX_SELF_HEAL_ROUNDS, exhausted, run, log)
    return success, log, failures, escalations, unit_test, solution_code
