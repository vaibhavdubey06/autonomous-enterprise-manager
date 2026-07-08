class CostEvaluator:
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int):
        # Gemini 1.5 Pro approx pricing
        prompt_cost = (prompt_tokens / 1_000_000) * 3.50
        completion_cost = (completion_tokens / 1_000_000) * 10.50
        return prompt_cost + completion_cost
