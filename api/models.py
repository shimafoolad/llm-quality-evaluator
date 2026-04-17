from pydantic import BaseModel, Field
from typing import Dict, Optional, Any


class EvaluationRequest(BaseModel):
    num_samples: Optional[int] = None
    dataset_name: Optional[str] = "eval_dataset"
    experiment_name: Optional[str] = None


class TaskStatus(BaseModel):
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
