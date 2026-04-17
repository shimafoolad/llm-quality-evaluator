import json
import re


def extract_json_from_string(text: str) -> str:
    """
    Extracts a JSON object from a string, assuming it's the first and last curly brace.
    Args:
        text: The input string containing the JSON object.
    Returns:
        A Python dictionary representing the JSON object, or None if extraction fails.
    Raises:
        ValueError: If no opening or closing brace is found
        json.JSONDecodeError: If JSON parsing fails
    """
    try:
        if '"response":' in text:
            text = text.split('"response":')[-1]
        elif re.search(r'"response":', text, flags=re.IGNORECASE):
            text = re.split(r'"response":', text, flags=re.IGNORECASE)[-1]

        start_index = text.find("{")
        if start_index == -1:
            raise ValueError(f"No opening brace found in the input text, the response is {text}")

        end_index = text.rfind("}")
        if end_index == -1:
            raise ValueError(f"No closing brace found in the input text, the response is {text}")

        json_string = text[start_index : end_index + 1]  # Include the closing brace
        return json_string

    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Error extracting JSON: {str(e)}") from e


def clean_and_parse_response(text: str) -> str:
    """
    Extract and clean response content from input text.
    Handles both JSON-like structures and plain text.

    Args:
        text: Input text to clean and parse

    Returns:
        Cleaned and parsed response string
    """
    text = text.replace("*", "")
    # split with last ":":
    if "{" in text:
        text = re.split(r":", text, flags=re.IGNORECASE)[-1]

    elif "response:" in text:
        text = text.split("response:")[-1]

    elif re.search(r"response:", text, flags=re.IGNORECASE):
        text = re.split(r"response:", text, flags=re.IGNORECASE)[-1]

    text = re.sub(r"\}.*$", "", text)

    text = text.strip().strip("}").strip().strip('"').strip().strip("'").strip("{")
    # Clean and format the text
    cleaned_text = (
        text.strip()
        .replace("\n", "")
        .replace("\\", "")
        .replace('"', "")
        .replace("`", "")
        .replace(", huh", "")
        .replace(" huh?", "?")
        .replace("No need to apologize,", "")
        .replace("no need to apologize,", "")
        .strip("}")
        .strip("{")
        .strip('"')
        .strip("'")
        .strip()
    )
    cleaned_text = re.sub(r"([^a-zA-Z0-9])n$", "", cleaned_text)
    cleaned_text = re.sub(r"\}.*$", "", cleaned_text)

    return cleaned_text.strip()
