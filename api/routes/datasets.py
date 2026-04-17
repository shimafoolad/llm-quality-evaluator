from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from typing import Optional, List
import shutil
from api.models import TaskStatus
from api.services.task_service import create_task, get_task, update_task_failure
from api.services.dataset_service import (
    process_directory_and_create_dataset,
    process_conversation_task,
    prepare_files_for_dataset,
    prepare_file_for_conversation,
)
from datetime import datetime
from utils.opik_client import OpikClient

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/", status_code=200, response_model=TaskStatus)
async def create_dataset(
    background_tasks: BackgroundTasks,
    directory_path: Optional[str] = Form("data/convo_files"),
    dataset_name: Optional[str] = Form("eval_dataset"),
    output_csv_path: Optional[str] = Form(None),
    # files: Optional[List[UploadFile]] = File(None),
):
    """
    Create a new dataset from conversation files as a background task

    You can either:
    1. Upload files directly using the 'files' parameter
    2. Provide dataset_info as form data with directory_path and dataset_name

    If both are provided, the uploaded files will be processed first.

    Returns a task ID that can be used to check status later
    """
    task_id = create_task()
    temp_dir = None
    try:
        # Set default output path if not provided
        if output_csv_path is None:
            output_csv_path = f"data/{dataset_name}.csv"
        if dataset_name is None:
            dataset_name = f"DB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # Prepare files for processing
        # TODO: file upload is not implemented yet
        convo_files, temp_dir = prepare_files_for_dataset(directory_path, files=None)

        # Process in background to avoid timeout
        background_tasks.add_task(
            process_directory_and_create_dataset,
            task_id,
            convo_files,
            output_csv_path,
            dataset_name,
        )

        # Add cleanup task if we created a temp directory
        if temp_dir:
            background_tasks.add_task(
                lambda: shutil.rmtree(temp_dir, ignore_errors=True)
            )

        task_info = get_task(task_id)
        return TaskStatus(
            task_id=task_id,
            status=task_info["status"],
            created_at=task_info["created_at"],
        )

    except ValueError as e:
        # Clean up on exception
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up on exception
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/", status_code=200, response_model=TaskStatus)
async def add_conversation_to_dataset(
    background_tasks: BackgroundTasks,
    dataset_name: Optional[str] = Form("db_autotest"),
    file_path: Optional[str] = Form(None),
    # file: Optional[UploadFile] = File(None),
):
    """
    Add a new conversation file to an existing dataset as a background task
    You can either:
    1. Upload a file directly using the 'file' parameter
    2. Provide a ConversationAdd object with a file path and dataset name

    If file is provided, it will be used instead of the file_path in the ConversationAdd object.
    Returns a task ID that can be used to check status later
    """
    task_id = create_task()
    temp_dir = None

    try:

        # Prepare file for processing
        # TODO: file upload is not implemented yet
        #file_path, temp_dir = prepare_file_for_conversation(file_path, file=None)
        # Process in background
        background_tasks.add_task(
            process_conversation_task, task_id, file_path, dataset_name, temp_dir
        )

        task_info = get_task(task_id)
        return TaskStatus(
            task_id=task_id,
            status=task_info["status"],
            created_at=task_info["created_at"],
        )

    except ValueError as e:
        # Clean up on exception
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Clean up on exception
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Update task status with error
        update_task_failure(task_id=task_id, error=str(e))

        raise HTTPException(status_code=500, detail=str(e)) from e
