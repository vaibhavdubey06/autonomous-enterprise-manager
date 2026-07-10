import numpy as np
from typing import List, Union
from evaluation.models import ScoreModel, MetricState


class ScoreNormalizer:
    @staticmethod
    def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Ensure a score is bounded between min_val and max_val."""
        return max(min_val, min(max_val, float(value)))

    @staticmethod
    def normalize_list(values: List[float], scale_to_100: bool = True) -> ScoreModel:
        """
        Takes a list of raw evaluation values, computes the mean, clamps it,
        determines the appropriate MetricState, and computes a confidence string.
        """
        # Filter out NaNs if any snuck in
        valid_values = [v for v in values if not np.isnan(v)]

        if not valid_values:
            return ScoreModel(
                value=0.0, state=MetricState.NOT_APPLICABLE, confidence="NONE"
            )

        mean_val = float(np.mean(valid_values))

        if scale_to_100 and mean_val <= 1.0:
            # If the raw metric is a probability [0, 1], scale to [0, 100]
            mean_val *= 100

        clamped_val = ScoreNormalizer.clamp(mean_val)

        # Determine confidence
        count = len(valid_values)
        if count < 5:
            confidence = "LOW"
        elif count < 15:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        # Adjust confidence based on variance if we have enough samples
        if count >= 3:
            std_dev = np.std(valid_values)
            # If standard deviation is very high relative to scale, lower confidence
            scale = 100 if scale_to_100 else 1.0
            if std_dev > 0.4 * scale:
                confidence = "LOW" if confidence == "MEDIUM" else "MEDIUM"

        return ScoreModel(
            value=clamped_val, state=MetricState.VALID, confidence=confidence
        )

    @staticmethod
    def normalize_single(
        value: Union[float, int],
        state: MetricState = MetricState.VALID,
        scale_to_100: bool = True,
        samples: int = 1,
    ) -> ScoreModel:
        if state in [
            MetricState.NOT_APPLICABLE,
            MetricState.NOT_EXECUTED,
            MetricState.SKIPPED,
        ]:
            return ScoreModel(value=0.0, state=state, confidence="NONE")

        val = float(value)
        if scale_to_100 and val <= 1.0:
            val *= 100

        val = ScoreNormalizer.clamp(val)

        confidence = "LOW"
        if samples >= 15:
            confidence = "HIGH"
        elif samples >= 5:
            confidence = "MEDIUM"

        return ScoreModel(value=val, state=state, confidence=confidence)
