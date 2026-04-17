"""
Orchestrates the evaluation process for comparing LLM versions
"""

from opik import track
from opik.evaluation import evaluate
from config import config
from utils import utils, metrics
import json
from utils.opik_client import OpikClient, APIClient
import time
from datetime import datetime 


class ModelEvaluator:
    """Orchestrates the evaluation process for comparing LLM versions"""

    def __init__(self, nb_samples=None, dataset_name=None, experiment_name=None, run_staging=True, new_version_name=None, old_version_name=None):
        """
        Initialize the evaluator, using provided parameters or falling back to config

        Args:
            nb_samples: Number of samples to evaluate (defaults to config value)
            dataset_name: Name of the dataset (defaults to config value)
            experiment_name: Name of the experiment (defaults to config value)
            run_staging: If True, generates new responses and uses current date as version.
                        If False, uses pre-existing responses with specified version names.
            new_version_name: Required when run_staging=False. Version identifier for newer responses.
            old_version_name: Required when run_staging=False. Version identifier for older responses.
        """
        # Initialize clients
        self.opik_client = OpikClient()
        self.api_client = APIClient()

        # Use provided values or fall back to config
        self.dataset = self.opik_client.get_or_create_dataset(dataset_name)
        self.dataset_name = dataset_name
        self.experiment_name = experiment_name
        self.nb_samples = nb_samples

        # Version handling based on staging mode
        if run_staging:
            # In staging mode: use current date for new version and auto-detect old version
            self.current_date = datetime.now().strftime('%Y%m%d')
            self.OLD_VERSION_NAME = self.opik_client.find_old_version_name(dataset_name) 
        else:
            # In non-staging mode: use provided version names for comparison
            if not new_version_name or not old_version_name:
                raise ValueError("new_version_name and old_version_name are required when run_staging=False")
            self.current_date = new_version_name 
            self.OLD_VERSION_NAME = old_version_name 
        

        self.metrics = [
            metrics.ComparativeMetric(),
            metrics.AnswerRelevanceMetric(),
            metrics.TruthfulnessMetric(),
            metrics.ResponseTimeMetric(),
        ]

    
    def query_model(self, request_data: str):
        """Execute model query with error handling"""
        try:
            start_time = time.time()

            default_values = {
            "chat_pause_interval": 0,
            "chat_pause_type": "",
            "leave_conversation": ""
            }
            
            # Check and add missing keys
            for key, default_value in default_values.items():
                if key not in request_data["chat_summary"]:
                    request_data["chat_summary"][key] = default_value
            
            response = self.api_client.post_request(request_data)
            response_time = round((time.time()) - start_time)
            prompt = response["prompt"]
            output = response["response"]
            return output, prompt, response_time

        except KeyError as e:
            raise RuntimeError(
                f"API response missing required field: {str(e)}"
            ) from e

    
    def evaluation_task(self, dataset_item):
        """Single evaluation task definition"""
        return {
            f"prompt_{self.current_date}": dataset_item[f"prompt_{self.current_date}"].split("!@#$%^&*()"),
        }

    def run_evaluation(self):
        """Execute full evaluation workflow"""
        try:
            return evaluate(
                experiment_name=self.experiment_name,
                dataset=self.dataset,
                task=self.evaluation_task,
                scoring_metrics=self.metrics,
                nb_samples=self.nb_samples,
                scoring_key_mapping={"output": f"output_{self.current_date}", 
                                     "context": f"prompt_{self.current_date}",
                                     "old_output": f"output_{self.OLD_VERSION_NAME}",
                                     "new_response_time": f"response_time_{self.current_date} (sec)",
                                     "old_response_time": f"response_time_{self.OLD_VERSION_NAME} (sec)",
                                    }
            )
        except Exception as e:
            raise RuntimeError(
                f"Evaluation execution failed: {str(e)}"
            ) from e

    def generate_and_store_new_model_responses(self):
        """Query the model API for all dataset items and store the new responses with the current date"""
        dataset_info = self.opik_client.get_dataset(self.dataset_name)
        try:
            items = dataset_info.get_items()
            for item in items: #items[741:]:
                if f"output_{self.current_date}" not in item.keys():
                    print("get new prompt from staging")
                    try:
                        request_data = json.loads(item["request_data"])
                    except json.JSONDecodeError as e:
                        raise RuntimeError(
                            f"Invalid JSON in request_data: {str(e)}"
                        ) from e
                    new_output, new_prompt, response_time = self.query_model(request_data)
                    new_item = {**item}  # Create a copy of the dataset item
                    new_item.update({
                        f"output_{self.current_date}": new_output,
                        f"prompt_{self.current_date}": new_prompt,
                        f"response_time_{self.current_date} (sec)": response_time,
                    })
                
                    dataset_info.update([new_item])
        except Exception as e:
            raise RuntimeError(
                f"Update dataset failed: {str(e)}"
            ) from e
        
            

async def run_evaluation_task(
    task_id: str, num_samples: int, dataset_name: str, experiment_name: str
):
    """
    Run evaluation task with support for both staging and non-staging modes
    
    Args:
        task_id: Unique identifier for the evaluation task
        num_samples: Number of samples to evaluate
        dataset_name: Name of the dataset to use
        experiment_name: Name of the experiment
    """
    from api.services.task_service import update_task_success, update_task_failure
    

    # Configuration for non-staging mode
    run_staging = True  # Set to False to use pre-existing responses
    old_version_name = "20250528"  # Required when run_staging=False
    new_version_name = "20250603"  # Required when run_staging=False
    
    try:
        if run_staging:
            # Staging mode: Generate new responses and store in dataset
            evaluator = ModelEvaluator(num_samples, dataset_name, experiment_name, run_staging)
            # step 1: run staging to get new response and put in dataset
            evaluator.generate_and_store_new_model_responses()
        else:
            # Non-staging mode: Use pre-existing responses with specified versions
            evaluator = ModelEvaluator(num_samples, dataset_name, experiment_name, run_staging, new_version_name, old_version_name)
        
        # step 2: run evaluation task to compute metrics
        results = evaluator.run_evaluation()
        # Update task status
        update_task_success(task_id, {"experiment_id": results.experiment_id})
    except Exception as e:
        # Update task status with error
        update_task_failure(task_id, str(e))
        
