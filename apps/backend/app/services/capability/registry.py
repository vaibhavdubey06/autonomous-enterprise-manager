from pydantic import BaseModel
from typing import Dict, List


class CapabilityDecision(BaseModel):
    required_capability: str
    confidence: float
    ranked_scores: Dict[str, float]
    matched_keywords: Dict[str, List[str]]
    reasoning: str


# Configurable Capability Registry
# This maps each capability to a set of keywords and their weights (1.0 default)
CAPABILITY_REGISTRY = {
    "Architecture": {
        "keywords": {
            "architecture": 1.5,
            "design": 1.0,
            "system": 1.0,
            "diagram": 1.0,
            "scalable": 1.0,
            "diagrams": 1.0,
            "architectural": 1.2,
        }
    },
    "Software Engineering": {
        "keywords": {
            "code": 1.0,
            "develop": 1.0,
            "implement": 1.0,
            "function": 1.0,
            "api": 1.2,
            "bug": 1.0,
            "fix": 1.0,
            "frontend": 1.2,
            "backend": 1.2,
            "software": 1.0,
            "engineer": 1.0,
            "script": 1.0,
        }
    },
    "Infrastructure": {
        "keywords": {
            "cloud": 1.0,
            "aws": 1.2,
            "server": 1.0,
            "database": 1.0,
            "network": 1.0,
            "vpc": 1.5,
            "storage": 1.0,
            "infrastructure": 1.5,
        }
    },
    "DevOps": {
        "keywords": {
            "ci/cd": 1.5,
            "pipeline": 1.2,
            "deploy": 1.0,
            "docker": 1.2,
            "kubernetes": 1.5,
            "jenkins": 1.5,
            "terraform": 1.5,
            "automation": 1.0,
            "devops": 1.5,
        }
    },
    "Finance": {
        "keywords": {
            "budget": 1.0,
            "cost": 1.0,
            "revenue": 1.0,
            "financial": 1.2,
            "accounting": 1.5,
            "invoice": 1.5,
            "payroll": 1.0,
            "finance": 1.5,
        }
    },
    "HR": {
        "keywords": {
            "hire": 1.0,
            "recruitment": 1.5,
            "employee": 1.0,
            "onboarding": 1.2,
            "benefits": 1.0,
            "human resources": 1.5,
            "hr": 1.5,
        }
    },
    "Marketing": {
        "keywords": {
            "campaign": 1.0,
            "seo": 1.5,
            "social media": 1.2,
            "advertisement": 1.2,
            "brand": 1.0,
            "marketing": 1.5,
        }
    },
    "Legal": {
        "keywords": {
            "contract": 1.0,
            "compliance": 1.2,
            "law": 1.5,
            "policy": 1.0,
            "nda": 1.5,
            "terms of service": 1.2,
            "legal": 1.5,
        }
    },
    "Security": {
        "keywords": {
            "auth": 1.0,
            "vulnerability": 1.5,
            "encryption": 1.2,
            "audit": 1.0,
            "security": 1.5,
            "firewall": 1.5,
            "hacker": 1.2,
            "cyber": 1.2,
        }
    },
    "Research": {
        "keywords": {
            "investigate": 1.0,
            "study": 1.0,
            "analysis": 1.0,
            "paper": 1.0,
            "research": 1.5,
            "explore": 1.0,
            "findings": 1.0,
        }
    },
    "Knowledge": {
        "keywords": {
            "wiki": 1.5,
            "confluence": 1.5,
            "documentation": 1.2,
            "guide": 1.0,
            "knowledge base": 1.5,
            "notion": 1.5,
            "knowledge": 1.0,
        }
    },
    "Analytics": {
        "keywords": {
            "data": 1.0,
            "metrics": 1.2,
            "dashboard": 1.2,
            "statistics": 1.2,
            "report": 1.0,
            "analytics": 1.5,
            "tracking": 1.0,
        }
    },
    "Product": {
        "keywords": {
            "roadmap": 1.2,
            "user story": 1.5,
            "feature": 1.0,
            "requirements": 1.2,
            "product": 1.5,
            "agile": 1.2,
            "sprint": 1.2,
        }
    },
    "Operations": {
        "keywords": {
            "logistics": 1.5,
            "supply chain": 1.5,
            "support": 1.0,
            "ticket": 1.0,
            "operations": 1.5,
            "maintenance": 1.0,
        }
    },
}
