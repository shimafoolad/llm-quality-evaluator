"""
Shared client module for Opik and OpenAI services
"""

from opik import Opik
from openai import OpenAI
from config import config
from typing import Optional, Dict, Any
import requests
import json
from datetime import datetime 

class OpikClient:
    """Singleton client for Opik operations"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpikClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the Opik client"""
        # Ensure configuration is valid
        config.validate()
        self.client = Opik()

    def get_or_create_dataset(self, name: str):
        """Retrieve or create evaluation dataset"""
        try:
            return self.client.get_or_create_dataset(name=name)
        except Exception as e:
            raise FileNotFoundError(
                f"Failed to access dataset '{name}': {str(e)}"
            ) from e
            
    def get_dataset(self, name: str):
        """Retrieve or create evaluation dataset"""
        try:
            return self.client.get_dataset(name=name)
        except Exception as e:
            raise FileNotFoundError(
                f"Failed to access dataset '{name}': {str(e)}"
            ) from e
            
    def insert_from_pandas(self, dataset, dataframe):
        """Add data from pandas dataframe to dataset"""
        dataset.insert_from_pandas(dataframe=dataframe)
        return True

    def get_dataset_columns(self, dataset_name):
        """Get dataset columns from a specific dataset"""
        try:
            dataset_info = self.client.get_dataset(name=dataset_name)
            return list(dataset_info.get_items(1)[0].keys())
        except Exception as e:
            raise FileNotFoundError(
                f"Failed to access dataset '{dataset_name}': {str(e)}"
            ) from e

    def get_last_dataset(self):
        datasets = self.client.get_datasets()
        return datasets[0]

    def find_old_version_name(self, dataset_name):
        dates = []
        dataset_columns = self.get_dataset_columns(dataset_name)
        if dataset_columns:
            # Extract keys starting with "output_"
            output_keys = [col for col in dataset_columns if col.startswith("output_")]
            
            # Get the dates from the keys
            for key in output_keys:
                try:
                    date_str = key.split("_")[1]  # Extract the date part
                    datetime.strptime(date_str, "%Y%m%d")  # Validate date format
                    dates.append(date_str)
                except (IndexError, ValueError):
                    continue  # Skip invalid date formats
        
        if not dates:
            return "v1"
        else:
            # Find the lastest date
            #print("old_version_name:", max(dates))
            return max(dates)
    

class OpenAIClient:
    """Singleton client for OpenAI operations"""

    def __init__(self):
        """Initialize the OpenAI client"""
        # Ensure configuration is valid
        config.validate()
        self.client = OpenAI(
            api_key=config.LLM_API_KEY, base_url=config.LLM_API_BASE_URL
        )
        self.model_name = self.client.models.list().data[0].id

    def get_model_name(self):
        return self.model_name
        
    def create_chat_completion(
        self, messages: list, temperature: Optional[float] = None
    ):
        """Create a chat completion"""
        temp = temperature if temperature is not None else config.LLM_TEMPERATURE
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temp,
        )


class APIClient:
    """Client for API operations"""

    @staticmethod
    def post_request(request_data: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
        """Execute an API request with error handling"""
        try:
            api_response = requests.post(
                config.SWAGGER_BASE_URL,
                json=request_data,
                timeout=timeout,
            )

            if api_response.status_code != 200:
                raise RuntimeError(
                    f"Error sending data: HTTP {api_response.status_code}"
                )

            return json.loads(api_response.text)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"API Request failed: {str(e)}"
            ) from e
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse API response: {str(e)}"
            ) from e
