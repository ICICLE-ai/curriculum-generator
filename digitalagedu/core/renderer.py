"""
Curriculum Markdown Syllabus Renderer
=====================================
Pure Python markdown generation for curriculum syllabi and lesson plans.
Replaces legacy Jinja2 template dependencies with structured string rendering.
"""

from typing import Dict, Any, List


class CurriculumMarkdownRenderer:
    """
    Renders curriculum syllabus and lesson plans to clean Markdown without external template engines.
    """

    def render(self, context: Dict[str, Any]) -> str:
        """
        Render structured curriculum data (from CurriculumService.build()) to markdown format.
        """
        if not context:
            return "# Curriculum\n\nNo curriculum data provided.\n"

        lines: List[str] = []

        subject = context.get("subject", "Artificial Intelligence & Data Science")
        grade = context.get("grade", "10")
        weeks = context.get("weeks", 6)

        lines.append(f"# {subject} Curriculum\n")
        lines.append(f"**Grade:** {grade}  ")
        lines.append(f"**Duration:** {weeks} weeks\n")

        # Live pipeline execution metrics
        pipeline_metrics = context.get("pipeline_metrics")
        if pipeline_metrics:
            lines.append("## Live Pipeline Run Execution Metrics\n")
            total_samples = pipeline_metrics.get("total_samples", "N/A")
            accuracy = pipeline_metrics.get("accuracy", "N/A")
            lines.append(f"- **Total Evaluated Images:** {total_samples}")
            lines.append(f"- **Baseline Accuracy Achieved:** {accuracy}%\n")

            stage_times = pipeline_metrics.get("stage_times")
            if stage_times and isinstance(stage_times, dict):
                lines.append("### Execution Times\n")
                for stage, time_hr in stage_times.items():
                    clean_stage = str(stage).replace("_", " ").title()
                    lines.append(f"- **{clean_stage} Stage:** {time_hr} hours")
                lines.append("")

            correct_samples = pipeline_metrics.get("correct_samples", [])
            if correct_samples:
                lines.append("### Case Studies for Classroom Discussion\n")
                lines.append("**Correct Predictions (True Positives/Negatives):**\n")
                for sample in correct_samples:
                    p = sample.get("path", "")
                    gt = sample.get("ground_truth", "")
                    lines.append(f"- Image: `{p}` (Classified correctly as *{gt}*)")
                lines.append("")

            misclassified = pipeline_metrics.get("misclassified_samples", [])
            if misclassified:
                lines.append("**Misclassified Predictions (False Positives/Negatives):**\n")
                for sample in misclassified:
                    p = sample.get("path", "")
                    gt = sample.get("ground_truth", "")
                    pred = sample.get("predicted", "")
                    lines.append(f"- Image: `{p}` (True Class: *{gt}*, Predicted Class: *{pred}*)")
                lines.append("")

        # Topics and modules
        topics = context.get("topics", [])
        for topic in topics:
            name = topic.get("name", "Module")
            desc = topic.get("description", "")
            project = topic.get("project", "")

            lines.append(f"## {name}\n")
            if desc:
                lines.append(f"{desc}\n")
            if project:
                lines.append(f"**Project:** {project}\n")

            meta = topic.get("dataset_metadata")
            if meta and isinstance(meta, dict):
                lines.append("### Dataset Summary\n")
                lines.append(f"- **Classes:** {meta.get('num_classes', 'N/A')}")
                lines.append(f"- **Total Images:** {meta.get('total_images', 'N/A')}")
                lines.append(f"- **Imbalance Ratio:** {meta.get('imbalance_ratio', 'N/A')}")
                if meta.get("size_category"):
                    lines.append(f"- **Size Category:** {meta.get('size_category')}")
                if meta.get("difficulty_level"):
                    lines.append(f"- **Difficulty Level:** {meta.get('difficulty_level')}")
                metrics = meta.get("suggested_metrics", [])
                if metrics:
                    lines.append(f"- **Suggested Metrics:** {', '.join(metrics)}")
                lines.append("")

            activities = topic.get("activities", [])
            if activities:
                lines.append("### Activities\n")
                for act in activities:
                    lines.append(f"- {act}")
                lines.append("")

            weeks_dict = topic.get("weeks", {})
            if weeks_dict and isinstance(weeks_dict, dict):
                lines.append("### Weekly Schedule\n")
                for week_name, week_activities in weeks_dict.items():
                    if week_activities:
                        lines.append(f"* **{week_name}:**")
                        for act in week_activities:
                            lines.append(f"  - {act}")
                lines.append("")

        # External Resources
        global_resources = context.get("global_resources", [])
        lines.append("## External Resources\n")
        if global_resources:
            for res in global_resources:
                if isinstance(res, dict):
                    r_name = res.get("name", "Resource")
                    r_url = res.get("url", "#")
                    lines.append(f"- [{r_name}](<{r_url}>)")
                else:
                    lines.append(f"- {res}")
            lines.append("")
        else:
            lines.append("- No external resources provided.\n")

        return "\n".join(lines).strip() + "\n"

