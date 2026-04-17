"""
Utilities for dataset processing and management
"""

import re
import json
import pandas as pd
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from utils.opik_client import OpikClient, APIClient


def parse_custom_timestamp(ts_str):
    """Convert custom timestamp format to datetime object"""
    try:
        return datetime.strptime(ts_str, "%b %d, %Y @ %H:%M:%S.%f")
    except ValueError:
        return datetime.max  # Put invalid dates at end


def parse_llm_response(response_str):
    """Parse LLM RESPONSE string to extract conversation_id and response"""
    parsed = {}

    # Extract conversation ID
    conv_id_match = re.search(r"\[([^\]]+)\]", response_str)
    parsed["conversation_id"] = conv_id_match.group(1) if conv_id_match else None

    # Extract response content (special handling for commas in message)
    response_match = re.search(r"response:\s*\[([^\]]+)\]", response_str, re.DOTALL)

    if response_match:
        parsed["response"] = response_match.group(1).strip()
    else:
        parsed["response"] = None

    return parsed


def determine_file_type(file_path: str) -> str:
    """
    Determine if a file is JSON or CSV
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: 'json' or 'csv'
    """
    # First check by extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.json':
        return 'json'
    if ext.lower() == '.csv':
        return 'csv'
    
    # If extension doesn't clearly indicate the type, try to read the file
    try:
        with open(file_path, 'r') as f:
            first_char = f.read(1).strip()
            # Check if file starts with '{' or '[' which indicates JSON
            if first_char in ['{', '[']:
                # Try to parse it as JSON
                f.seek(0)
                json.load(f)
                return 'json'
            else:
                # Try to parse it as CSV
                pd.read_csv(file_path, nrows=1)
                return 'csv'
    except json.JSONDecodeError:
        return 'csv'
    except pd.errors.ParserError:
        # If both attempts fail, default to JSON (since that's the new format)
        return 'json'
    except Exception:
        # For any other errors, default to JSON
        return 'json'


def process_json_convo(json_data: Dict[str, Any], api_client: APIClient) -> Dict[str, Any]:
    """
    Process JSON conversation data
    
    Args:
        json_data: The parsed JSON data
        api_client: API client for prompt fetching
        
    Returns:
        Dict: Processed conversation request data
    """
    # Extract timestamp - using current time as it's not in the JSON
    timestamp = datetime.now().strftime("%b %d, %Y @ %H:%M:%S.%f")
    
    # Extract conversation ID from chat_summary
    conversation_id = json_data.get("chat_summary", {}).get("conversation_id", "")
    
    # Process participants info
    participants = json_data.get("participants_info", [])
    local_hour = json_data.get("local_hour", "")
    for info in participants:
        if isinstance(info, dict) and info.get("user_type") == "R":
            info["local_hour"] = local_hour
    
    # Extract chat history
    chat_history = json_data.get("chat_history", [])
    
    input_text = ""
    for message in chat_history:
        if message.get("sender_type") == "R":
            input_text = message.get("content","")
            break
    
    # Create the request data structure
    current_request = {
        "timestamp": timestamp,
        "conversation_id": conversation_id,
        "request_data": {
            "chat_history": chat_history,
            "chat_summary": json_data.get("chat_summary", {}),
            "participants_info": participants,
            "follow_up": json_data.get("follow_up", False),
            "max_premium_messages": json_data.get("max_premium_messages", 0),
            "gap_more_than_8h": json_data.get("gap_more_than_8h", False),
            "contact_info_detected": json_data.get("contact_info_detected", False),
            "profile_imgs": json_data.get("profile_imgs", []),
            "local_hour": local_hour,
            "profile_r": json_data.get("profile_r", {}),
            "profile_v": json_data.get("profile_v", {}),
            "feature_flags": json_data.get("feature_flags", {}),
        },
        "input": input_text,
        #"output_v1": None,
        #"prompt_v1": None,
    }
    
    # If this is dataset creation, fetch the prompt from API
    #if is_dataset_creation and current_request["request_data"]:
    #    response = api_client.post_request(current_request["request_data"])
    #    current_request[f"prompt_{date}"] = response["prompt"]
    
    return current_request


def process_csv_convo(csv_file: str, api_client: APIClient) -> List[Dict[str, Any]]:
    """
    Process CSV conversation data
    
    Args:
        csv_file: Path to CSV file
        api_client: API client for prompt fetching
        
    Returns:
        List[Dict]: List of processed conversation request data
    """
    all_data = []
    
    # Read and sort by timestamp
    df = pd.read_csv(csv_file)

    # Convert timestamp column
    df["_parsed_ts"] = df["⏰ (@timestamp)"].apply(parse_custom_timestamp)
    df = df.sort_values("_parsed_ts").reset_index(drop=True)

    all_llm_requests = []
    all_llm_responses = []

    for _, row in df.iterrows():
        current_request = {}
        cell_value = row.get("custom.message.keyword", "")
        timestamp = row["⏰ (@timestamp)"]

        # Extract LLM REQUEST
        if cell_value.startswith("LLM REQUEST"):
            # Extract conversation ID and JSON
            match = re.search(
                r"LLM REQUEST for chat \[([^\]]+)\]:\s*(\{.*\})", cell_value, re.DOTALL
            )

            if not match:
                continue

            conversation_id, json_str = match.groups()

            try:
                json_data = json.loads(json_str)
            except json.JSONDecodeError:
                continue

            # Process participants info
            participants = json_data.get("participants_info", [])
            local_hour = json_data.get("local_hour", "")
            for info in participants:
                if isinstance(info, dict) and info.get("user_type") == "R":
                    info["local_hour"] = local_hour

            chat_history = json_data.get("chat_history", [])
            if not chat_history:
                continue

    
            input = ""
            for message in chat_history:
                if message.get("sender_type") == "R":
                    input = message.get("content","")
                    break

            
            #input = chat_history[0]["content"]

            # Store request data
            current_request = {
                "timestamp": timestamp,
                "conversation_id": conversation_id,
                "request_data": {
                    "chat_history": chat_history,
                    "chat_summary": json_data.get("chat_summary", {}),
                    "participants_info": participants,
                    "follow_up": json_data.get("follow_up", False),
                    "max_premium_messages": json_data.get("max_premium_messages", 0),
                    "gap_more_than_8h": json_data.get("gap_more_than_8h", False),
                    "contact_info_detected": json_data.get(
                        "contact_info_detected", False
                    ),
                    "profile_imgs": json_data.get("profile_imgs", []),
                    "local_hour": local_hour,
                    "profile_r": json_data.get("profile_r", {}),
                    "profile_v": json_data.get("profile_v", {}),
                    "feature_flags": json_data.get("feature_flags", {}),
                },
                "input": input,
                #"output_v1": None,
                #f"prompt_{date}": None,
            }
            all_llm_requests.append(current_request)

        # Extract LLM RESPONSE
        #elif cell_value.startswith("LLM RESPONSE"):
        #    response_data = parse_llm_response(cell_value)
        #    all_llm_responses.append(response_data["response"])

    # Ensure we have matching request/response pairs
    #if len(all_llm_requests) != len(all_llm_responses):
    #    raise ValueError(
    #        f"Mismatch in requests ({len(all_llm_requests)}) and responses ({len(all_llm_responses)})"
    #    )
    
    # Match responses with requests and fetch prompts
    #for idx in range(len(all_llm_responses)):
    #    data = all_llm_requests[idx]
        #data["output_v1"] = all_llm_responses[idx]
        # Send API request for prompt
        #if data["request_data"]:
        #    response = api_client.post_request(data["request_data"])
        #    data[f"prompt_{date}"] = response["prompt"]
    #   all_data.append(data)
    
    return all_llm_requests #all_data


def is_directory(path: str) -> bool:
    """Check if the path is a directory"""
    return os.path.isdir(path)


def get_files_in_directory(directory: str, extension: Optional[str] = None) -> List[str]:
    """
    Get all files in a directory with optional extension filter
    
    Args:
        directory: Path to directory
        extension: Optional file extension to filter by (e.g., '.json')
        
    Returns:
        List[str]: List of file paths
    """
    files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            if extension is None or filename.lower().endswith(extension.lower()):
                files.append(file_path)
    return files


def process_convo(file_path):
    """Process a single conversation file or directory of files
    Args:
        file_path: The conversation file or directory to process    
    """

    api_client = APIClient()
    all_data = []
    
    # Check if the path is a directory
    if is_directory(file_path):
        # Process all files in the directory
        json_files = get_files_in_directory(file_path, '.json')
        csv_files = get_files_in_directory(file_path, '.csv')
        
        # Process JSON files
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                current_request = process_json_convo(json_data, api_client)
                all_data.append(current_request)
            except Exception as e:
                print(f"Error processing JSON file {json_file}: {str(e)}")
        
        # Process CSV files
        for csv_file in csv_files:
            try:
                csv_data = process_csv_convo(csv_file, api_client)
                all_data.extend(csv_data)
            except Exception as e:
                print(f"Error processing CSV file {csv_file}: {str(e)}")
    else:
        # Process a single file
        file_type = determine_file_type(file_path)
        
        if file_type == 'json':
            # Process JSON file
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            
            current_request = process_json_convo(json_data, api_client)
            all_data = [current_request]
        else:
            # Process CSV file
            all_data = process_csv_convo(file_path, api_client)
    
    # If no data was processed, return empty DataFrame
    if not all_data:
        return pd.DataFrame()
    
    # Create final DataFrame
    df_dataset = pd.DataFrame(all_data)
    
    # Handle nested structures by converting to JSON strings
    json_cols = [
        "timestamp",
        "conversation_id",
        "request_data",
        "input",
        "output_v1",
    ]
    for col in json_cols:
        if col in df_dataset.columns:
            df_dataset[col] = df_dataset[col].apply(json.dumps)
    
    return df_dataset


def add_dataset_to_opik(data, dataset_name):
    """Add dataset to Opik platform"""
    if data.empty:
        raise ValueError("No data to add to dataset")
        
    client = OpikClient()
    try:
        dataset = client.get_or_create_dataset(name=dataset_name)
    except Exception as e:
        raise ValueError(f"Dataset with Name {dataset_name} not found: {str(e)}") from e
    return client.insert_from_pandas(dataset, data)
