"""
Custom metrics for model evaluation
"""

from typing import Any, List
from opik.evaluation.metrics import (
    base_metric,
    score_result,
    AnswerRelevance,
    Hallucination,
)
from utils import utils
import ast
from opik.evaluation.models import OpikBaseModel
from pathlib import Path
from utils.opik_client import OpenAIClient
import json

BASE_DIR = Path(__file__).parent.parent
print("BASE_DIR:", BASE_DIR)

class CustomModel(OpikBaseModel):
    """Custom model implementation for metric computation"""

    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.openai_client = OpenAIClient()
        self.our_llama_model = self.openai_client.get_model_name()

    def our_llm_application(self, prompt: str) -> str:
        """Apply our LLM to generate a response for the given prompt"""
        prompt += "BE SURE RETURN THE RESULT AS A JSON OBJECT, INCLUDING THE SCORE AND THE REASON."
        response = self.openai_client.create_chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        return utils.extract_json_from_string(response.choices[0].message.content)

    async def agenerate_provider_response(self, **kwargs: Any) -> str:
        """async version (not implemented for sync-first model)"""
        raise NotImplementedError("Async generation not supported for this sync model")

    async def agenerate_string(self, input: str, **kwargs: Any) -> str:
        """Async version (not implemented for sync-first model)"""
        raise NotImplementedError("Async generation not supported for this sync model")

    # The following methods are required by the base class but not used in async flow
    def generate_provider_response(self, **kwargs: Any) -> str:
        prompt = kwargs.get("prompt", "")
        return self.our_llm_application(prompt)

    def generate_string(self, input: str, **kwargs: Any) -> str:
        return self.our_llm_application(input)

    async def agenerate_provider_response_stream(self, **kwargs: Any) -> str:
        """Streaming version (implement if needed)"""
        raise NotImplementedError("Streaming generation not implemented")

class TruthfulnessCustomModel(OpikBaseModel):
    """Custom model implementation for metric computation"""

    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.openai_client = OpenAIClient()
        self.our_llama_model = self.openai_client.get_model_name()

    def our_llm_application(self, prompt: str) -> str:
        """Apply our LLM to generate a response for the given prompt"""
        prompt += "BE SURE RETURN THE RESULT AS A JSON OBJECT, INCLUDING THE SCORE AND THE REASON."
        response = self.openai_client.create_chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        content = utils.extract_json_from_string(response.choices[0].message.content)
        try:
            dict_content = ast.literal_eval(content)
            dict_content["score"] = 1.0-dict_content["score"]
        except Exception as e:
            raise RuntimeError(
                "Failed to parse the model output."
            ) from e
        
        return json.dumps(dict_content)

    async def agenerate_provider_response(self, **kwargs: Any) -> str:
        """async version (not implemented for sync-first model)"""
        raise NotImplementedError("Async generation not supported for this sync model")

    async def agenerate_string(self, input: str, **kwargs: Any) -> str:
        """Async version (not implemented for sync-first model)"""
        raise NotImplementedError("Async generation not supported for this sync model")

    # The following methods are required by the base class but not used in async flow
    def generate_provider_response(self, **kwargs: Any) -> str:
        prompt = kwargs.get("prompt", "")
        return self.our_llm_application(prompt)

    def generate_string(self, input: str, **kwargs: Any) -> str:
        return self.our_llm_application(input)

    async def agenerate_provider_response_stream(self, **kwargs: Any) -> str:
        """Streaming version (implement if needed)"""
        raise NotImplementedError("Streaming generation not implemented")
        

def AnswerRelevanceMetric():
    """Factory function to create AnswerRelevance metric with custom model"""
    return AnswerRelevance(
        model=CustomModel(model_name="our_custom_model"),
        name="answer_relevance_score",
    )

def HullucinationMetric():
    """Factory function to create Hallucination metric with custom model"""
    return Hallucination(
        model=CustomModel(model_name="our_custom_model"),
        name="hullucination_score",
    )
    
def TruthfulnessMetric():
    """Factory function to create truthfulness metric with custom model"""
    return Hallucination(
        model=TruthfulnessCustomModel(model_name="our_truthfulness_model"),
        name="truthfulness_score",
    )


class ComparativeMetric(base_metric.BaseMetric):
    """
    LLM-based comparative evaluation metric for model outputs.
    Uses a judge LLM to compare new vs old model responses.
    """

    def __init__(self, name: str = "output_comparison_score"):
        super().__init__(name=name)
        self.openai_client = OpenAIClient()
        self.model_name = self.openai_client.model_name
        self.prompt_template = self._load_prompt_template()
        self.name = name

    def _load_prompt_template(self) -> str:
        """Load prompt template from file"""
        try:
            with open(BASE_DIR / "prompts" / "comparative_metric_prompt.txt", "r") as f:
                return f.read()
        except FileNotFoundError as e:
            raise RuntimeError(
                "Prompt template file not found at 'prompts/comparative_metric_prompt.txt'"
            ) from e

    def score(
        self, input: str, output: str, old_output: str, context: List[str], **kwargs
    ) -> score_result.ScoreResult:
        """Score model outputs using the judge LLM"""
        formatted_prompt = self.prompt_template.format(
            input=input,
            context=context,
            old_output=old_output,
            new_output=output,
        )

        try:
            response = self.openai_client.create_chat_completion(
                messages=[{"role": "user", "content": formatted_prompt}]
            )
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Scoring failed: {str(e)}") from e

    def _parse_response(self, response) -> score_result.ScoreResult:
        """Parse and validate the judge LLM response"""
        content = response.choices[0].message.content
        content = utils.extract_json_from_string(content)
        try:
            dict_content = ast.literal_eval(content)
        except Exception as e:
            raise RuntimeError(
                "Failed to parse the model output."
            ) from e

        return score_result.ScoreResult(
            name=self.name,
            value=dict_content["improvement_score"],
            reason=dict_content["reason"],
            metadata=dict_content,
        )


class ResponseTimeMetric(base_metric.BaseMetric):
    """
    A metric that compares individual response times between old and new versions of a system.
    
    This metric calculates the absolute difference and percentage improvement
    between a single response time measurement from each version.
    
    Args:
        threshold_sec: Minimum time difference (in seconds) considered meaningful. Defaults to 0.1s.
        name: The name of the metric. Defaults to "response_time_comparison".
    
    Example:
        >>> from opik.evaluation.metrics import ResponseTimeComparison
        >>> rt_metric = ResponseTimeComparison(threshold_sec=0.1)
        >>> result = rt_metric.score(new_time=9, old_time=8)
        >>> print(f"Improvement: {result.value:.2f}%")
        Improvement: 11%
        >>> print(result.reason)
        {'time_diff_sec': 0.7, 'is_meaningful': True}
    """
    
    def __init__(
        self,
        name: str = "response_time_comparison",
    ):
        super().__init__(
            name=name,
        )
    
    def score(
        self, 
        new_response_time: int,
        old_response_time: int,
        **ignored_kwargs: Any
    ) -> score_result.ScoreResult:
        """
        Calculate metrics comparing individual response times between old and new versions.
        
        Args:
            new_response_time: Response time (in seconds) from the new version.
            old_response_time: Response time (in seconds) from the old version.
            **ignored_kwargs: Additional keyword arguments that are ignored.
            
        Returns:
            score_result.ScoreResult: A ScoreResult object with:
                - value: Percentage improvement (positive means new is faster)
                - metadata: Dictionary containing detailed statistics
        """
        # Calculate the absolute difference
        time_diff = old_response_time - new_response_time
        #print(f"old_time:{old_response_time}, new_time:{new_response_time}, time_diff:{time_diff}")
        
        # Calculate percentage improvement (positive = faster, negative = slower)
        if old_response_time > 0:  # Avoid division by zero
            percent_improvement = (time_diff / old_response_time) 
        else: 
            #  no change
            percent_improvement = 0.0
        
        reason = self.interpret_result(time_diff, percent_improvement)

        return score_result.ScoreResult(
            value=round(percent_improvement, 2), 
            name=self.name,
            reason=reason
        )
    
    def interpret_result(self, time_diff: int, percent_improvement: float) -> str:
        """
        Provides a human-readable interpretation of the metric result.
        
        Args:
            result: The ScoreResult returned by the score method.
            
        Returns:
            str: Human-readable interpretation of the results.
        """
        
        if percent_improvement > 0:
            performance = f"The new version is {percent_improvement:.2f}% faster than the old version"
        elif percent_improvement < 0:
            performance = f"The new version is {abs(percent_improvement):.2f}% slower than the old version"
        else:
            performance = "There is no difference in response time"
            
       
        
        return f"{performance} (absolute difference: {time_diff} seconds)."