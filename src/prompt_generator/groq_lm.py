import os
import dspy
import litellm

class GroqDSPyLM(dspy.LM):
    """A custom DSPy Language Model (LM) to integrate with Groq using litellm."""
    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(model=model)
        self.api_key = api_key
        self.provider = "groq"
        # litellm expects model name to be prefixed with 'groq/' or just the model name
        self.litellm_model = f"{self.provider}/{model}" if not model.startswith('groq/') else model
        self.kwargs = kwargs

    def __call__(self, prompt, only_completed=True, return_sorted=False, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        try:
            # Pass kwargs from dspy.predict to litellm.completion
            merged_kwargs = {**self.kwargs, **kwargs}
            response = litellm.completion(
                model=self.litellm_model,
                messages=messages,
                api_key=self.api_key,
                **merged_kwargs
            )
            completion = response.choices[0].message.content
            return [completion]
        except Exception as e:
            print(f"Error during Groq completion: {e}")
            return []

    def basic_request(self, prompt, **kwargs):
        # Implement if dspy.predict requires this method, otherwise it can be omitted
        raise NotImplementedError("This custom LM does not use basic_request directly for dspy.predict.")
