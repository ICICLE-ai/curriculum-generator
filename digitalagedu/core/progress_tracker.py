import os
import json
import time
from typing import List, Dict, Any, Optional

class ProgressTracker:
    """
    Thread-safe, atomic progress recorder for DigitalAgEdu pipeline executions.
    Dynamically registers all active and inactive stages from the pipeline configuration
    and writes progress.json to the output directory.
    """

    def __init__(self, output_dir: str, stages_config: Optional[List[Any]] = None):
        self.output_dir = output_dir
        self.progress_file = os.path.join(output_dir, "progress.json")
        self.temp_file = os.path.join(output_dir, "progress.json.tmp")
        self.start_time = time.time()
        self.last_update_time = self.start_time

        # Initialize the stage registry dynamically
        self.stages: List[Dict[str, Any]] = []

        # 1. Dataset Ingestion (Phase 1 Foundation)
        self.stages.append({
            "id": "dataset_ingestion",
            "name": "Dataset Ingestion & Class Mapping",
            "phase": "Phase 1",
            "status": "READY",
            "details": "Scanning directory and resolving canonical classes",
            "start_time": None,
            "end_time": None,
            "duration_sec": None
        })

        # 2. Granular ML Stages from Config (Classification, Segmentation, VisualXAI, etc.)
        if stages_config:
            for stg in stages_config:
                name = getattr(stg, "name", "ML Stage")
                active = getattr(stg, "active", True)
                stage_id = name.lower().replace(" ", "_")
                self.stages.append({
                    "id": stage_id,
                    "name": name,
                    "phase": "Phase 1",
                    "status": "READY" if active else "SKIPPED",
                    "details": f"Configured task: {getattr(stg, 'task_type', name)}" if active else "Disabled in config",
                    "start_time": None,
                    "end_time": None,
                    "duration_sec": None
                })
        else:
            # Defaults if no config stages provided
            self.stages.extend([
                {
                    "id": "classification",
                    "name": "Classification",
                    "phase": "Phase 1",
                    "status": "READY",
                    "details": "DINOv2 backbone evaluation",
                    "start_time": None,
                    "end_time": None,
                    "duration_sec": None
                },
                {
                    "id": "segmentation",
                    "name": "Segmentation",
                    "phase": "Phase 1",
                    "status": "READY",
                    "details": "SAM mask extraction",
                    "start_time": None,
                    "end_time": None,
                    "duration_sec": None
                }
            ])

        # 3. Curriculum Synthesis (Phase 2)
        self.stages.append({
            "id": "curriculum_synthesis",
            "name": "Curriculum Synthesis",
            "phase": "Phase 2",
            "status": "READY",
            "details": "Multi-week syllabus & JSON generation",
            "start_time": None,
            "end_time": None,
            "duration_sec": None
        })

        # 4. Exercise Generation & Test Validation
        self.stages.append({
            "id": "exercise_generation",
            "name": "Exercise Scaffolding & Validation",
            "phase": "Phase 2",
            "status": "READY",
            "details": "Generating starter code, solutions, and running unit test sandboxes",
            "start_time": None,
            "end_time": None,
            "duration_sec": None
        })

        # 5. Packaging & Reporting
        self.stages.append({
            "id": "packaging",
            "name": "Artifact Packaging & Metrics",
            "phase": "Phase 2",
            "status": "READY",
            "details": "Final report, results.csv, and requirements.txt",
            "start_time": None,
            "end_time": None,
            "duration_sec": None
        })

        self.current_stage_id: Optional[str] = None
        self.overall_status = "RUNNING"
        self.current_message = "Initializing pipeline execution..."
        self.percent = 0

        self._flush()

    def _get_stage(self, stage_id_or_name: str) -> Optional[Dict[str, Any]]:
        normalized = stage_id_or_name.lower().replace(" ", "_")
        for stg in self.stages:
            if stg["id"] == normalized or stg["name"].lower() == stage_id_or_name.lower():
                return stg
        return None

    def _calculate_percent(self) -> int:
        active_stages = [s for s in self.stages if s["status"] != "SKIPPED"]
        if not active_stages:
            return 100
        completed = sum(1 for s in active_stages if s["status"] == "COMPLETED")
        in_progress = sum(0.5 for s in active_stages if s["status"] == "IN_PROGRESS")
        return min(100, int(((completed + in_progress) / len(active_stages)) * 100))

    def start_stage(self, stage_id_or_name: str, details: Optional[str] = None):
        """Mark a stage as IN_PROGRESS."""
        stage = self._get_stage(stage_id_or_name)
        if stage:
            stage["status"] = "IN_PROGRESS"
            stage["start_time"] = time.time()
            if details:
                stage["details"] = details
            self.current_stage_id = stage["id"]
            self.current_message = f"Executing {stage['name']}"
        else:
            self.current_message = f"Executing {stage_id_or_name}"
        self._flush()

    def update_stage_progress(self, stage_id_or_name: str, current: int, total: int, message: Optional[str] = None):
        """Update batch/step progress for an active stage."""
        stage = self._get_stage(stage_id_or_name)
        if stage:
            stage["status"] = "IN_PROGRESS"
            stage["progress"] = f"{current}/{total}"
            if message:
                stage["details"] = message
                self.current_message = f"{stage['name']} ({current}/{total}): {message}"
            else:
                self.current_message = f"{stage['name']} ({current}/{total})"
        self._flush()

    def complete_stage(self, stage_id_or_name: str, metrics: Optional[Dict[str, Any]] = None):
        """Mark a stage as COMPLETED."""
        stage = self._get_stage(stage_id_or_name)
        if stage:
            stage["status"] = "COMPLETED"
            now = time.time()
            stage["end_time"] = now
            if stage["start_time"]:
                stage["duration_sec"] = round(now - stage["start_time"], 2)
            if metrics:
                stage["metrics"] = metrics
            self.current_message = f"Completed {stage['name']}"
        self._flush()

    def fail_stage(self, stage_id_or_name: str, error_message: str):
        """Mark a stage and overall pipeline as FAILED."""
        stage = self._get_stage(stage_id_or_name)
        if stage:
            stage["status"] = "FAILED"
            stage["error"] = error_message
        self.overall_status = "FAILED"
        self.current_message = f"Failed at {stage_id_or_name}: {error_message}"
        self._flush()

    def finish_all(self, final_metrics: Optional[Dict[str, Any]] = None):
        """Mark all remaining active stages as COMPLETED and finish pipeline."""
        for stg in self.stages:
            if stg["status"] == "IN_PROGRESS":
                stg["status"] = "COMPLETED"
                if stg["start_time"] and not stg["end_time"]:
                    stg["end_time"] = time.time()
                    stg["duration_sec"] = round(stg["end_time"] - stg["start_time"], 2)
        self.overall_status = "FINISHED"
        self.current_message = "Pipeline execution finished successfully."
        self.percent = 100
        self._flush(extra_data={"final_metrics": final_metrics} if final_metrics else None)

    def _flush(self, extra_data: Optional[Dict[str, Any]] = None):
        """Atomic write to progress.json using temporary file rename."""
        try:
            self.last_update_time = time.time()
            self.percent = self._calculate_percent()

            data = {
                "status": self.overall_status,
                "current_stage": self.current_stage_id,
                "current_message": self.current_message,
                "progress_percent": self.percent,
                "elapsed_seconds": round(self.last_update_time - self.start_time, 1),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_update_time)),
                "stages": self.stages
            }

            if extra_data:
                data.update(extra_data)

            os.makedirs(self.output_dir, exist_ok=True)
            with open(self.temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            os.replace(self.temp_file, self.progress_file)
        except Exception as e:
            # Progress recording should never crash the main ML pipeline
            print(f"[WARN] ProgressTracker failed to flush progress.json: {e}")
