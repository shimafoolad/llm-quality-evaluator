# LLM Model Evaluation System

A comprehensive automated testing framework for evaluating and comparing different versions of Our Models using LLM-Judge metrics and the Opik evaluation platform.

## Overview

This system enables rigorous comparison between different LLM versions through four key evaluation dimensions:

1. **Comparative Score**: Evaluates relative response quality between model versions
2. **truthfulness Score**: Indicates the accuracy and reliability of the model's responses
3. **Answer Relevance Score**: Measures how appropriately responses address the original query
4. **Response Time Comparison**: Compares individual response times between model versions

## Key Features

- Automated testing pipeline with customizable sample sizes
- Comprehensive scoring system with multiple metrics
- Integration with Opik for visualization and analysis
- RESTful API for programmatic access and integration
- Detailed reporting and visualization capabilities

## Prerequisites

- Python 3.9+
- Opik platform access (API key and workspace required)
- Access to LLM server endpoints
- Evaluation model: `models/Llama-3.1-70B-Instruct-lorablated-AWQ`

## Configuration

Create a `.env` file with the following essential parameters:

### API Configuration
```python
# Opik Integration
OPIK_API_KEY = your_opik_key
OPIK_WORKSPACE = your_opik_workspace
# Model Endpoints
LLM_API_BASE_URL = http://x.x.x.x:40575/v1  #LLM server
LLM_MODEL_NAME=Llama-3.1-70B-Instruct-lorablated-AWQ
LLM_SERVER_PORT=40575
LLM_API_KEY="None"
LLM_TEMPERATURE=0.0
SWAGGER_BASE_URL = http://x.x.x.x:p/api-llm  # Model API
```

## Installation and Setup

### 1. Install and Start Servers
```bash
scripts/run-server.sh
```
This script will:
- Install all required dependencies
- Launch the API server

### 2. Run Evaluation

#### Using the API Endpoints

The system provides RESTful endpoints for all operations:

- **Start Evaluation**: `POST /evaluate/`
- **Create Dataset**: `POST /datasets/`
- **Add Conversation to Dataset**: `POST /datasets/conversations/`

## API Usage Examples

### Trigger Evaluation
```bash
curl -X 'POST' \
  'http://localhost:8000/evaluate/' \
  -H 'Content-Type: application/json' \
  -d '{
    "num_samples": 10, "dataset_name": "eval_dataset"
  }'
```

### Create New Dataset
```bash
curl -X 'POST' \
  'http://localhost:8000/datasets/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'directory_path=data/convo_files' \
  -F 'dataset_name=DB_20250319_090917' \
  -F 'output_csv_path=a.csv' \
  -F 'files=@/path/to/conversation1.csv' 
```

### Add Conversation to Dataset
```bash
curl -X 'POST' \
  'http://localhost:8000/datasets/conversations/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'dataset_name=Automated_test_db_v3' \
  -F 'file_path=data/convo_files/conversation1.csv'
  -F "files=@/path/to/conversation1.csv" \
  -F "files=@/path/to/conversation2.csv"
```

### Check Task Status
```bash
curl -X GET "http://localhost:8000/tasks/task-id"
```
### List All Tasks
```bash
curl -X GET "http://localhost:8000/tasks/"
```

## Evaluation Modes

The system supports two evaluation modes:

### 1. Staging Mode (Default)
When `run_staging=True`:
- Automatically generates new responses using the current model version
- Stores responses in the dataset with the current date as version identifier
- Compares against the previous version automatically detected from the dataset

### 2. Non-Staging Mode
When `run_staging=False`:
- Uses pre-existing responses in the dataset
- Requires manual specification of version names:
  - `new_version_name`: The version identifier for the newer model responses
  - `old_version_name`: The version identifier for the older model responses
- Useful for comparing historical versions or when responses are pre-generated

Example usage for non-staging mode:
```python
evaluator = ModelEvaluator(
    num_samples=10,
    dataset_name="my_dataset",
    experiment_name="my_experiment",
    run_staging=False,
    new_version_name="20250528",  # Version identifier for newer responses
    old_version_name="20250418"   # Version identifier for older responses
)
results = evaluator.run_evaluation()
```

View results on your Opik dashboard at [Comet.com](https://www.comet.com/signup) (GitHub signup required)

## Project Structure

```
response_quality_evaluator/
├── api/                           # Main API package
│   ├── endpoints.py               # API model definitions
│   ├── models.py                  # Data models and schemas
│   ├── routes/
│   │   ├── datasets.py            # Dataset management endpoints
│   │   └── evaluations.py         # Evaluation execution endpoints
│   └── services/
│       ├── dataset_service.py     # Dataset creation and processing
│       ├── evaluation_service.py  # Evaluation orchestration
│       └── task_service.py        # Background task management
├── utils/                         # Utility modules
│   ├── dataset_utils.py           # Conversation processing utilities
│   ├── metrics.py                 # Evaluation metrics implementation
│   ├── opik_client.py             # Opik platform integration
│   └── utils.py                   # General utilities
├── data/                          # Data directory
│   ├── json_files/                # JSON conversation files
│   ├── csv_files/                 # CSV datasets
│   └── convo_files/               # Raw conversation files
├── prompts/                       # Metric prompt templates
│   └── comparative_metric_prompt.txt
├── scripts/                       # Utility scripts
│   └── run-server.sh              # Server startup script
├── tests/                         # Test suite
├── config.py                      # Configuration management
└── requirements.txt               # Python dependencies
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd response_quality_evaluator
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```bash
# Required API Keys
OPIK_API_KEY=your_opik_api_key
OPIK_WORKSPACE=your_workspace_name

# LLM Server Configuration
LLM_API_BASE_URL=http://localhost:40575/v1
LLM_MODEL_NAME=Llama-3.1-70B-Instruct-lorablated-AWQ
LLM_SERVER_PORT=40575
LLM_API_KEY=None
LLM_TEMPERATURE=0.0

# Model API
SWAGGER_BASE_URL=http://localhost:8000/api-llm
```

### 3. Run the Server
```bash
./scripts/run-server.sh
```

### 4. Trigger an Evaluation
```bash
curl -X POST http://localhost:8000/evaluate/ \
  -H "Content-Type: application/json" \
  -d '{"num_samples": 5, "dataset_name": "eval_dataset"}'
```

## Data Format

### JSON Conversation Format
Conversation files should follow this structure:
```json
{
  "chat_history": [
    {
      "content": "User message",
      "conversation_id": "unique_id",
      "created_at": "ISO_timestamp",
      "message_id": "msg_id",
      "sender_id": "user_id",
      "sender_type": "R" (or "V"),
      "state": "received"
    }
  ],
  "chat_summary": {
    "conversation_id": "unique_id",
    "summary": "Brief conversation summary",
    "location": "User location",
    "location_geo": {"lat": 0.0, "lng": 0.0},
    "is_premium": false
  },
  "participants_info": [
    {
      "user_id": "id",
      "given_name": "Name",
      "profession": "Job",
      "location": "City",
      "user_type": "R" (or "V")
    }
  ]
}
```

### CSV Dataset Format
```csv
input,conversation_id,output_v1,response_time,timestamp
User question here,conv_001,Model response,1.5,2024-01-01T10:00:00Z
```

Sample data files are provided in the `data/` directory for testing purposes.

## Service Architecture

### Core Services

#### Dataset Service (`api/services/dataset_service.py`)
- Processes raw conversation files into structured datasets
- Supports JSON and CSV file formats
- Integrates with Opik for dataset creation
- Handles file validation and error recovery

#### Evaluation Service (`api/services/evaluation_service.py`)
- Orchestrates the comparison workflow between model versions
- Manages metric execution
- Handles response generation and collection
- Generates experiment reports in Opik

#### Task Service (`api/services/task_service.py`)
- Manages background task tracking
- Provides status updates for long-running operations
- Stores task results and error information

### Utility Modules

#### Metrics (`utils/metrics.py`)
- **ComparativeMetric**: Compares response quality between versions
- **TruthfulnessMetric**: Evaluates factual accuracy
- **AnswerRelevanceMetric**: Measures response appropriateness
- **ResponseTimeMetric**: Tracks performance differences

#### Opik Client (`utils/opik_client.py`)
- Manages Opik platform authentication
- Handles dataset and experiment creation
- Manages API client for LLM interactions

#### Dataset Utils (`utils/dataset_utils.py`)
- Parses JSON and CSV conversation files
- Extracts and structures conversation data
- Validates data integrity

## Running Tests

### Sample Data Testing
The system includes sample data files for quick testing:

```bash
# Create dataset from sample conversations
curl -X POST http://localhost:8000/datasets/ \
  -H "Content-Type: multipart/form-data" \
  -F "directory_path=data/convo_files" \
  -F "dataset_name=sample_dataset"

# Check task status
curl http://localhost:8000/tasks/<task_id>
```


## Evaluation Metrics

The system implements three sophisticated metrics for comprehensive model evaluation:

### 1. Comparative Metric
- **Implementation**: `metrics.ComparativeMetric`
- **Purpose**: Direct comparison of response quality between model versions
- **Methodology**: Uses customized prompts from `prompts/comparative_metric_prompt.txt`
- **Scoring**: 0 (old version equal or better) to 1 (new version significantly better)

### 2. Truthfulness Metric
- **Implementation**: `metrics.TruthfulnessMetric`
- **Purpose**: Detection of reliability of the model's responses
- **Scoring**: 0 (contains significant unfaithful content) to 1 (completely faithful to context)

### 3. Answer Relevance Metric
- **Implementation**: `metrics.AnswerRelevanceMetric`
- **Purpose**: Measurement of response appropriateness to the input query
- **Scoring**: 0 (completely irrelevant) to 1 (perfectly matched to query intent)

### 4. Response Time 
- **Implementation**: `metrics.ResponseTimeMetric`
- **Purpose**: Direct comparison of response time between model versions
- **Methodology**: Calculates the absolute difference and percentage improvement between a single response time measurement from each version.

## Visualization and Analysis

Results are automatically uploaded to the Opik platform, providing:
- Comparative visualizations between model versions
- Metric distribution analysis
- Sample-level examination of differences
- Trend analysis for iterative improvements

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|----------|
| `OPIK_API_KEY` | Opik platform authentication key | Yes | `your_api_key_here` |
| `OPIK_WORKSPACE` | Opik workspace identifier | Yes | `workspace_name` |
| `LLM_API_BASE_URL` | Base URL for LLM server | Yes | `http://localhost:40575/v1` |
| `LLM_MODEL_NAME` | Model identifier for LLM | Yes | `Llama-3.1-70B-Instruct-lorablated-AWQ` |
| `LLM_SERVER_PORT` | Port for LLM server | No | `40575` |
| `LLM_API_KEY` | API key for LLM (if required) | No | `None` |
| `LLM_TEMPERATURE` | Model temperature parameter | No | `0.0` |
| `SWAGGER_BASE_URL` | Base URL for API documentation | Yes | `http://localhost:8000/api-llm` |

## Workflow Example

### Complete Evaluation Workflow

1. **Prepare Data**
   - Conversation JSON files in `data/json_files/`
   - Or CSV files in `data/csv_files/`

2. **Create Dataset**
   ```bash
   POST /datasets/ with directory_path and dataset_name
   Returns task_id for tracking
   ```

3. **Monitor Dataset Creation**
   ```bash
   GET /tasks/{task_id}
   ```

4. **Run Evaluation**
   ```bash
   POST /evaluate/ with dataset_name and num_samples
   Returns experiment_url for Opik dashboard
   ```

5. **View Results**
   - Access Opik dashboard with provided URL
   - Analyze comparative metrics
   - Compare model versions

## Troubleshooting

### Common Issues

**Issue**: "Connection refused" to LLM server
- **Solution**: Ensure LLM server is running and `LLM_API_BASE_URL` is correct

**Issue**: "Invalid API key" from Opik
- **Solution**: Verify `OPIK_API_KEY` and `OPIK_WORKSPACE` in `.env` file

**Issue**: "Dataset not found" error
- **Solution**: Ensure dataset creation task completed successfully
- Check task status with `GET /tasks/{task_id}`

**Issue**: Evaluation hangs or times out
- **Solution**: Reduce `num_samples` parameter
- Check LLM server performance and availability

## Performance Optimization

- **Reduce Sample Size**: Start with smaller `num_samples` (5-10) for testing
- **Parallel Processing**: System uses async/await for concurrent operations
- **Response Caching**: Consider caching responses for repeated evaluations
- **Batch Operations**: Group multiple evaluations to optimize resource usage

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evaluate/` | Trigger model evaluation |
| POST | `/datasets/` | Create new dataset |
| POST | `/datasets/conversations/` | Add conversations to dataset |
| GET | `/tasks/` | List all background tasks |
| GET | `/tasks/{task_id}` | Get specific task status |

## Support and Documentation

- **Opik Documentation**: [opik.comet.com/docs](https://opik.comet.com/docs)
- **FastAPI Docs**: Available at `http://localhost:8000/docs` when server is running
- **Project Repository**: Check the repository for updates and issues

## License

See LICENSE file in the repository for licensing information.
