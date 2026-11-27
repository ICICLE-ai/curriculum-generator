from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Module(BaseModel):
    id: str
    title: str
    week: int
    context: str
    difficulty: str
    learning_outcomes: Optional[List[str]] = Field(default_factory=list)
    level: str = ""  # the students' level (CurriculumConfig.level)
    domain: str = ""
    course_context: str = ""
    subject: str = ""
    topic_focus: str = ""
    estimated_days: Optional[float] = None
    resources: List[Dict[str, str]] = Field(default_factory=list)

    def level_note(self) -> str:
        """Prompt line pitching the week at the students' level; empty when no level is set."""
        if not self.level:
            return ""
        return f"Student Level: {self.level} (pitch vocabulary, math depth and code complexity at this level)\n"

    def course_context_block(self) -> str:
        """Prompt block with course-level context, module ETA, and reference resources; empty when unset."""
        lines: List[str] = []
        if self.subject:
            lines.append(f"Course Subject: {self.subject}")
        if self.domain:
            lines.append(f"Domain: {self.domain}")
        if self.course_context:
            lines.append(f"Course Goal: {self.course_context}")
        if self.topic_focus:
            lines.append(f"Core Topic Focus: {self.topic_focus}")
        if self.estimated_days is not None and self.estimated_days > 0:
            lines.append(
                f"Estimated Module Duration: {self.estimated_days:g} day(s) "
                "(calibrate exercise scope and slide pacing to fit this timeframe)"
            )
        if self.resources:
            res_lines = [
                f"  - {r.get('name') or r.get('url')}: {r.get('url', '')}".rstrip(": ")
                for r in self.resources
                if r.get("name") or r.get("url")
            ]
            if res_lines:
                lines.append("Course Reference Resources:\n" + "\n".join(res_lines))
        return ("\n".join(lines) + "\n") if lines else ""

class SyllabusModuleSchema(BaseModel):
    """Schema for a single module synthesized by the Syllabus Architect Agent."""
    id: str = Field(description="URL-safe unique slug for module directory, e.g. 'crop_leaf_data_exploration'")
    title: str = Field(description="Grade-appropriate, engaging title of the module")
    week: int = Field(description="Academic week number (1 to total_weeks)")
    context: str = Field(description="Specific learning context connecting computational/AI concept to domain")
    difficulty: str = Field(default="Intermediate", description="'Beginner', 'Intermediate', or 'Advanced'")
    learning_outcomes: List[str] = Field(default_factory=list, description="2-3 specific student learning outcomes (Bloom's Taxonomy)")

class SyllabusPlanSchema(BaseModel):
    """Schema for the complete course syllabus synthesized by the Syllabus Architect Agent."""
    course_title: str = Field(description="Overall course title bridging domain science and AI")
    course_description: str = Field(description="Summary paragraph of the course pedagogical progression")
    modules: List[SyllabusModuleSchema] = Field(description="Sequential list of modules covering the requested academic weeks")

