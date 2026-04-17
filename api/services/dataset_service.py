import os
import tempfile
import shutil
from glob import glob
import pandas as pd
from typing import List, Optional, Tuple

from utils.dataset_utils import process_convo, add_dataset_to_opik


async def process_directory_and_create_dataset(
    task_id: str, convo_files: List[str], output_csv_path: str, dataset_name: str
):
    """Process files and create dataset"""
    from api.services.task_service import update_task_success, update_task_failure

    try:
        all_dataframes = []

        for convo_file in convo_files:
            try:
                convo_data = process_convo(convo_file)
                all_dataframes.append(convo_data)
            except Exception as e:
                print(f"Error processing {convo_file}: {e}")

        if not all_dataframes:
            raise Exception("No valid conversation data found in any files")

        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)

        # Save to CSV
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        combined_df.to_csv(output_csv_path, index=False)

        # Add to Opik
        add_dataset = add_dataset_to_opik(combined_df, dataset_name)

        # Update task status
        update_task_success(
            task_id,
            {
                "add_dataset": add_dataset,
                "dataset_name": dataset_name,
                "rows_processed": len(combined_df),
                "output_file": output_csv_path,
            },
        )
    except Exception as e:
        # Update task status with error
        update_task_failure(task_id, str(e))


async def process_conversation_task(
    task_id: str, file_path: str, dataset_name: str, temp_dir: Optional[str] = None
):
    """Process conversation and add to dataset"""
    from api.services.task_service import update_task_success, update_task_failure

    try:
        # Process the conversation
        convo_data = process_convo(file_path)
        
        # Check if any data was processed
        if convo_data.empty:
            update_task_failure(task_id, "No valid conversation data found in the provided path")
            return
            
        # Get client and dataset
        add_dataset = add_dataset_to_opik(convo_data, dataset_name)
        
        # Update task status
        update_task_success(
            task_id,
            {
                "add_dataset": add_dataset,
                "dataset_name": dataset_name,
                "rows_added": len(convo_data),
            },
        )
    except Exception as e:
        # Update task status with error
        update_task_failure(task_id, str(e))
    finally:
        # Clean up temporary files if we created any
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


def prepare_files_for_dataset(
    directory_path: Optional[str] = None, files: Optional[List] = None
) -> Tuple[List[str], Optional[str]]:
    """Prepare files for dataset creation from directory or uploaded files"""
    temp_dir = None
    
    if directory_path:
        # Handle directory path case
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        convo_files = glob(f"{directory_path}/*.csv")
        if not convo_files:
            raise ValueError(f"No CSV files found in {directory_path}")
    elif files and len(files) > 0:
        # Handle file upload case
        temp_dir = tempfile.mkdtemp()
        convo_files = []

        for file in files:
            if not file.filename.endswith(".csv"):
                continue

            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            convo_files.append(file_path)

        if not convo_files:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError("No CSV files were uploaded")
    else:
        raise ValueError(
            "Either files must be uploaded or directory_path must be provided"
        )

    return convo_files, temp_dir


def prepare_file_for_conversation(
    file_path: Optional[str] = None, file=None
) -> Tuple[str, Optional[str]]:
    """Prepare file for conversation addition from path or uploaded file"""
    temp_dir = None

    if file_path:
        # Handle file path case
        if not os.path.isfile(file_path):
            raise ValueError(f"File not found: {file_path}")
    elif file:
        # Handle file upload case
        if not file.filename.endswith(".csv"):
            raise ValueError("Only CSV files are supported")

        # Create a temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_path = temp_file_path
    else:
        raise ValueError("Either file must be uploaded or file_path must be provided")

    return file_path, temp_dir
