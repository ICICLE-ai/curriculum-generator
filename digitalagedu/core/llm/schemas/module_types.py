from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Module(BaseModel):
    id: str
    title: str
    week: int
    context: str
    difficulty: str

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

