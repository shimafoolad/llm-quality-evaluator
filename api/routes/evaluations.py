from fastapi import APIRouter, BackgroundTasks
from api.models import EvaluationRequest, TaskStatus
from api.services.task_service import create_task, get_task
from api.services.evaluation_service import run_evaluation_task
from datetime import datetime

router = APIRouter(prefix="/evaluate", tags=["evaluations"])


@router.post("/", response_model=TaskStatus)
async def evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """
    Start an evaluation task in the background

    Returns a task ID that can be used to check status later
    """
    if not request.experiment_name or request.experiment_name=="string":
        request.experiment_name = f"Experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if request.num_samples== 0:
        request.num_samples = None
        
    task_id = create_task()

    # Schedule the task to run in the background
    background_tasks.add_task(
        run_evaluation_task,
        task_id,
        request.num_samples,
        request.dataset_name,
        request.experiment_name,
    )

    task_info = get_task(task_id)
    return TaskStatus(
        task_id=task_id, status=task_info["status"], created_at=task_info["created_at"]
    )
