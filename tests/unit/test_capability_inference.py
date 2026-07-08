import pytest
from app.services.capability.service import CapabilityInferenceService
from app.services.capability.registry import CapabilityDecision

def test_capability_inference_devops():
    service = CapabilityInferenceService()
    decision = service.infer("Deploy a docker container using kubernetes", "The deployment needs a proper ci/cd pipeline.")
    
    assert isinstance(decision, CapabilityDecision)
    assert decision.required_capability == "DevOps"
    assert decision.confidence > 0.0
    assert "docker" in decision.matched_keywords["DevOps"]
    assert "kubernetes" in decision.matched_keywords["DevOps"]
    assert "ci/cd" in decision.matched_keywords["DevOps"]

def test_capability_inference_finance():
    service = CapabilityInferenceService()
    decision = service.infer("Calculate the total cost and budget for Q3", "We need a financial report for accounting.")
    
    assert decision.required_capability == "Finance"
    assert decision.confidence > 0.0
    assert "budget" in decision.matched_keywords["Finance"]

def test_capability_inference_fallback():
    service = CapabilityInferenceService()
    # Meaningless words that shouldn't match any capability
    decision = service.infer("Just do some random stuff", "Nothing specific here.")
    
    assert decision.required_capability == "General"
    assert decision.confidence == 0.0
    assert "No capability keywords matched" in decision.reasoning

def test_capability_inference_multiple_matches():
    service = CapabilityInferenceService()
    # Contains both Marketing and HR keywords, but HR has more weight
    decision = service.infer("Create an SEO campaign", "Also hire a new employee for recruitment and human resources.")
    
    assert decision.required_capability == "HR"
    assert decision.confidence > 0.0
    assert "marketing" not in decision.required_capability.lower() # Because HR has 3 hits vs Marketing's 2
