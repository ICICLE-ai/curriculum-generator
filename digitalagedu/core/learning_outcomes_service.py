from typing import List, Dict

class LearningOutcomesService:
    def __init__(self):
        pass

    def generate(self, topic: Dict, week_distribution: List[str]) -> List[Dict]:
        outcomes = []

        meta = topic.get("dataset_metadata", None) or {}
        imbalance = meta.get("imbalance_ratio", 1)
        difficulty = meta.get("difficulty_level", "intermediate")
        task_type = meta.get("task_type", "classification")

        for week_name, activities in week_distribution.items():
            week_num = int(week_name.split()[-1])

            for activity in activities:
                outcome = self._map_activity_to_outcome(
                    activity, imbalance, difficulty, task_type, week_num
                )
                outcomes.append(outcome)
                week_counter += 1

        return outcomes

    # ---------------------------
    # Core Mapping Logic
    # ---------------------------
    def _map_activity_to_outcome(self, activity, imbalance, difficulty, task_type, week):
        activity_lower = activity.lower()

        # Default
        blooms = "Understand"
        abet = "1"  # Engineering knowledge
        measurable = "Student demonstrates conceptual understanding"

        # ---------------------------
        # RULE-BASED MAPPING
        # ---------------------------

        if "exploratory" in activity_lower or "visualize" in activity_lower:
            blooms = "Analyze"
            abet = "6"  # Experimentation
            measurable = "Student interprets dataset patterns and distributions"

        elif "imbalance" in activity_lower:
            blooms = "Analyze"
            abet = "2"  # Problem analysis
            measurable = "Student identifies imbalance and selects mitigation strategy"

        elif "preprocessing" in activity_lower or "split dataset" in activity_lower:
            blooms = "Apply"
            abet = "1"
            measurable = "Student applies preprocessing techniques correctly"

        elif "train" in activity_lower:
            blooms = "Apply"
            abet = "2"
            measurable = "Student trains a valid ML model"

        elif "evaluate" in activity_lower or "confusion matrix" in activity_lower:
            blooms = "Evaluate"
            abet = "6"
            measurable = "Student evaluates model performance using metrics"

        elif "transfer learning" in activity_lower or "hyperparameter" in activity_lower:
            blooms = "Create"
            abet = "3"  # Design solutions
            measurable = "Student improves model using advanced techniques"

        elif "compare" in activity_lower:
            blooms = "Evaluate"
            abet = "3"
            measurable = "Student compares multiple models and justifies selection"

        elif "project" in activity_lower:
            blooms = "Create"
            abet = "3"
            measurable = "Student builds an end-to-end solution"

        elif "ethical" in activity_lower:
            blooms = "Understand"
            abet = "4"  # Ethics
            measurable = "Student explains ethical implications of AI"

        # ---------------------------
        return {
            "week": week,
            "activity": activity,
            "learning_outcome": self._to_outcome_sentence(activity, blooms),
            "blooms_level": blooms,
            "abet_mapping": abet,
            "measurable_indicator": measurable
        }

    def _to_outcome_sentence(self, activity, blooms):
        prefix_map = {
            "Remember": "Recall",
            "Understand": "Explain",
            "Apply": "Apply",
            "Analyze": "Analyze",
            "Evaluate": "Evaluate",
            "Create": "Design"
        }

        prefix = prefix_map.get(blooms, "Understand")

        return f"{prefix} the concept: {activity}"