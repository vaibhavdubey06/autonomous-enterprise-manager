from enum import Enum


class EnvironmentProfile(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"
