from typing import Optional


class CostEstimator:
    @staticmethod
    def calculate_cost(
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        cost_input_per_million: float,
        cost_output_per_million: float,
    ) -> float:
        """
        Calculates estimated cost given token counts and per-million pricing.
        """
        prompt_t = prompt_tokens or 0
        completion_t = completion_tokens or 0

        input_cost = (prompt_t / 1_000_000) * cost_input_per_million
        output_cost = (completion_t / 1_000_000) * cost_output_per_million

        return input_cost + output_cost
