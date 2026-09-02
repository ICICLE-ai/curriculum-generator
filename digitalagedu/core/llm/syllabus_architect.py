import re
import logging
from typing import Dict, Any, List, Tuple
from digitalagedu.core.llm.schemas.module_types import Module, SyllabusPlanSchema, SyllabusModuleSchema

logger = logging.getLogger(__name__)

def _slugify(text: str) -> str:
    """Convert text to a clean, URL-safe / folder-safe slug."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", text).strip("_")

def formulate_syllabus(
    config: Any,
    telemetry: Dict[str, Any],
    client: Any,
    model_name: str
) -> Tuple[SyllabusPlanSchema, List[Module]]:
    """
    Syllabus Architect Agent:
    Autonomously plans a complete, multi-week pedagogical course progression
    grounded in the user's high-level domain context, target grade level,
    course duration (weeks), and Phase 1 dataset profile.
    """
    curriculum = getattr(config, "curriculum", None)
    project = getattr(config, "project", None)

    domain = getattr(project, "domain", "Artificial Intelligence & Data Science")
    context_statement = getattr(project, "context_statement", "Domain-specific AI applications and modeling")
    grade = getattr(curriculum, "grade", 10) or 10
    total_weeks = getattr(curriculum, "weeks", None) or 6
    subject = getattr(curriculum, "subject", domain)

    # Extract dataset profiling insights from Phase 1 telemetry if available
    dataset_summary = telemetry.get("run_summary", {}) if telemetry else {}
    num_classes = dataset_summary.get("num_classes", len(telemetry.get("class_mapping", {})) if telemetry else 0)
    total_samples = dataset_summary.get("total_samples", len(telemetry.get("results_df", [])) if telemetry else 0)
    imbalance_ratio = dataset_summary.get("imbalance_ratio", "N/A")
    classes_list = list(telemetry.get("class_mapping", {}).keys()) if telemetry and "class_mapping" in telemetry else []

    telemetry_context = ""
    if num_classes > 0 or total_samples > 0:
        telemetry_context = (
            f"\n--- AUTHENTIC DATASET PROFILE (Phase 1 Telemetry) ---\n"
            f"- Total Dataset Samples: {total_samples}\n"
            f"- Number of Target Classes: {num_classes}\n"
            f"- Identified Classes: {', '.join(classes_list[:10]) if classes_list else 'Standard domain classes'}\n"
            f"- Class Imbalance Ratio: {imbalance_ratio}\n"
        )

    prompt = (
        f"You are a master AI Curriculum Architect and Education Specialist.\n"
        f"Design a complete, highly engaging {total_weeks}-week course syllabus for {grade} level students.\n\n"
        f"--- COURSE METADATA ---\n"
        f"Subject / Course: {subject}\n"
        f"Domain: {domain}\n"
        f"Educational Objective / Context: {context_statement}\n"
        f"Target Grade / Level: {grade}\n"
        f"Course Duration: {total_weeks} Weeks\n"
        f"{telemetry_context}\n"
        f"PEDAGOGICAL & ARCHITECTURAL REQUIREMENTS:\n"
        f"1. Structure exactly {total_weeks} academic weeks, creating 1 distinct, progressive module per week (Week 1 through Week {total_weeks}).\n"
        f"2. Ensure a rigorous prerequisite progression tailored to {grade} students:\n"
        f"   - Week 1: Data Exploration, Problem Understanding & Visual Patterns in {domain}\n"
        f"   - Week 2: Feature Representation & Basic Modeling Foundations\n"
        f"   - Intermediate Weeks: Deep Neural Networks, Transfer Learning, Segmentation, or Domain-Specific Analytics\n"
        f"   - Late Weeks: Explainability (Model Debugging / Where the AI looks) & Error Analysis\n"
        f"   - Final Week: Interactive Web Application / Deployment (Gradio or API) for Domain Stakeholders\n"
        f"3. All module titles, descriptions, and learning outcomes MUST be deeply grounded in '{domain}' and '{context_statement}'. Avoid dry or generic titles.\n"
        f"4. Calibrate difficulty strictly for {grade} students (e.g. emphasize visual intuition and data literacy for High School, vs. formal tensor math and architectural depth for College)."
    )

    logger.info(f"Syllabus Architect: Formulating dynamic {total_weeks}-week curriculum for domain '{domain}' (Grade {grade})...")

    syllabus_plan: SyllabusPlanSchema = client.chat.completions.create(
        model=model_name,
        response_model=SyllabusPlanSchema,
        max_retries=3,
        max_tokens=4096,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an elite AI Curriculum Designer. Synthesize comprehensive, structured course syllabi "
                    "following Bloom's Revised Taxonomy and ABET outcomes. Output strict JSON matching the SyllabusPlanSchema."
                )
            },
            {"role": "user", "content": prompt}
        ]
    )

    # Convert SyllabusPlanSchema to standard Module objects for downstream multi-agents
    modules_list: List[Module] = []
    for m in syllabus_plan.modules:
        clean_id = _slugify(m.id) if m.id else f"week_{m.week:02d}_{_slugify(m.title)}"
        modules_list.append(
            Module(
                id=clean_id,
                title=m.title,
                week=m.week,
                context=m.context,
                difficulty=m.difficulty
            )
        )

    # Sort modules by academic week
    modules_list.sort(key=lambda x: (x.week, x.id))

    return syllabus_plan, modules_list
