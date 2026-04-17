import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Dictionary to store task status information
task_store = {}


def create_task() -> str:
    """Create a new task and return its ID"""
    task_id = str(uuid.uuid4())
    task_store[task_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }
    return task_id


def update_task_success(task_id: str, result: Dict[str, Any]):
    """Update a task with successful completion"""
    task_store[task_id].update(
        {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result,
        }
    )


def update_task_failure(task_id: str, error: str):
    """Update a task with failure information"""
    task_store[task_id].update(
        {"status": "failed", "completed_at": datetime.now().isoformat(), "error": error}
    )


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task information by ID"""
    return task_store.get(task_id)


def get_all_tasks() -> Dict[str, Dict[str, Any]]:
    """Get all tasks"""
    return task_store
