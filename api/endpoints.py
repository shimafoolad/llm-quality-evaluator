from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from api.routes import evaluations, datasets
from api.models import TaskStatus
from api.services.task_service import get_task, get_all_tasks

# Load environment variables (uncomment if needed)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Quality Evaluator API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from separate modules
app.include_router(evaluations.router)
app.include_router(datasets.router)


# Add task status check endpoint
@app.get("/tasks/{task_id}", response_model=TaskStatus, tags=["tasks"])
async def check_task_status(task_id: str):
    """
    Check the status of a background task
    
    Args:
        task_id: The ID of the task to check
        
    Returns:
        Task status information
    """
    task_info = get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        
    return TaskStatus(
        task_id=task_id,
        status=task_info["status"],
        created_at=task_info["created_at"],
        completed_at=task_info["completed_at"],
        result=task_info["result"],
        error=task_info["error"]
    )

# Add list all tasks endpoint
@app.get("/tasks/", response_model=List[TaskStatus], tags=["tasks"])
async def list_tasks():
    """
    List all tasks and their statuses
    
    Returns:
        List of task status information
    """
    tasks = get_all_tasks()
    return [
        TaskStatus(
            task_id=task_id,
            status=info["status"],
            created_at=info["created_at"],
            completed_at=info["completed_at"],
            result=info["result"],
            error=info["error"]
        )
        for task_id, info in tasks.items()
    ]