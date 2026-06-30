from typing import Optional
from pydantic import BaseModel
import datetime
import uuid


class AlertRule(BaseModel):
    rule_id: str = ""
    metric_name: str
    condition: str  # "gt", "lt", "eq"
    threshold: float
    severity: str = "WARNING"  # WARNING, CRITICAL
    cooldown_seconds: int = 60

    def __init__(self, **data):
        super().__init__(**data)
        if not self.rule_id:
            self.rule_id = str(uuid.uuid4())[:8]


class Alert(BaseModel):
    alert_id: str = ""
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    message: str
    timestamp: Optional[datetime.datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.alert_id:
            self.alert_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.datetime.utcnow()
