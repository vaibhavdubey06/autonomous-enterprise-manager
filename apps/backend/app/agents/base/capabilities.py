from enum import Enum


class Capability(str, Enum):
    """
    Capabilities representing specific domain expertise an Executive Agent possesses.
    """

    CODE_REVIEW = "CODE_REVIEW"
    ARCHITECTURE_ANALYSIS = "ARCHITECTURE_ANALYSIS"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    TECHNICAL_PLANNING = "TECHNICAL_PLANNING"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    REPORT_GENERATION = "REPORT_GENERATION"
