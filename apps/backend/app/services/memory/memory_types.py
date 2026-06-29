from enum import Enum


class MemoryType(str, Enum):
    FACT = "FACT"
    DECISION = "DECISION"
    GOAL = "GOAL"
    PREFERENCE = "PREFERENCE"
    PERSON = "PERSON"
    PROJECT = "PROJECT"
    TASK = "TASK"
    EVENT = "EVENT"
    RELATIONSHIP = "RELATIONSHIP"
    SKILL = "SKILL"
    QUESTION = "QUESTION"
    UNKNOWN = "UNKNOWN"


class MemoryStatus(str, Enum):
    NEW = "NEW"
    VERIFIED = "VERIFIED"
    CONSOLIDATED = "CONSOLIDATED"
    ARCHIVED = "ARCHIVED"
