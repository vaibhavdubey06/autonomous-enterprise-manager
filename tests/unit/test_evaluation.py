import pytest
import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend")
    ),
)
from evaluation.utils.metrics import (
    calculate_precision,
    calculate_recall,
    calculate_mrr,
)


def test_calculate_precision():
    retrieved = [1, 2, 3]
    relevant = [2, 3, 4]
    precision = calculate_precision(retrieved, relevant)
    assert precision == pytest.approx(0.666, 0.01)


def test_calculate_recall():
    retrieved = [1, 2, 3]
    relevant = [2, 3, 4]
    recall = calculate_recall(retrieved, relevant)
    assert recall == pytest.approx(0.666, 0.01)


def test_calculate_mrr():
    retrieved = [1, 2, 3]
    relevant = [3, 4]
    mrr = calculate_mrr(retrieved, relevant)
    assert mrr == pytest.approx(0.333, 0.01)


def test_calculate_mrr_no_hits():
    retrieved = [1, 2, 3]
    relevant = [4, 5]
    mrr = calculate_mrr(retrieved, relevant)
    assert mrr == 0.0


def test_get_percentile():
    from evaluation.utils.timer import get_percentile

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    p50 = get_percentile(data, 0.50)
    p90 = get_percentile(data, 0.90)
    assert p50 == pytest.approx(5.5)
    assert p90 == pytest.approx(9.1)
