from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Module(BaseModel):
    id: str
    title: str
    week: int
    context: str
    difficulty: str
