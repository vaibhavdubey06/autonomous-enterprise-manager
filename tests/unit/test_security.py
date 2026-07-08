from app.security.authentication.jwt_provider import jwt_provider
from app.security.authentication.password_service import password_service
from app.security.identity.identity_models import HumanUser
from app.security.authorization.rbac_engine import rbac_engine
from app.security.authorization.abac_engine import abac_engine
from app.security.api.rate_limiter import RateLimiter
from app.security.authorization.authorization_pipeline import AuthorizationPipeline


def test_password_hashing():
    pwd = "supersecretpassword123"
    hashed = password_service.hash_password(pwd)
    assert pwd != hashed
    assert password_service.verify_password(pwd, hashed) is True
    assert password_service.verify_password("wrong", hashed) is False


def test_jwt_creation_and_decoding():
    payload = {"sub": "123", "tenant_id": "t1"}
    token = jwt_provider.create_access_token(payload)
    decoded = jwt_provider.decode_token(token)
    assert decoded["sub"] == "123"
    assert decoded["tenant_id"] == "t1"


def test_rbac_engine():
    user = HumanUser(
        id="1",
        tenant_id="t1",
        email="test@test.com",
        roles=["user"],
        permissions=["workflow.execute"],
    )
    assert rbac_engine.evaluate(user, ["workflow.execute"]) is True
    assert rbac_engine.evaluate(user, ["security.manage"]) is False

    admin = HumanUser(id="2", tenant_id="t1", email="admin@test.com", roles=["admin"])
    assert rbac_engine.evaluate(admin, ["security.manage"]) is True  # Admin bypass


def test_abac_engine():
    user = HumanUser(id="u1", tenant_id="t1", email="test@test.com")

    # Matches tenant_id and owner_id
    assert abac_engine.evaluate(user, {}, {"tenant_id": "t1", "owner_id": "u1"}) is True

    # Cross tenant attempt
    assert abac_engine.evaluate(user, {}, {"tenant_id": "t2"}) is False


def test_rate_limiter():
    limiter = RateLimiter(calls=2, period=10)
    assert limiter.is_rate_limited("ip1") is False  # Call 1
    assert limiter.is_rate_limited("ip1") is False  # Call 2
    assert limiter.is_rate_limited("ip1") is True  # Call 3 (Limited)
    assert limiter.is_rate_limited("ip2") is False  # Another IP is fine


def test_authorization_pipeline_scenario_missing_permission():
    pipeline = AuthorizationPipeline()
    # If no identity context is set, it should deny
    decision = pipeline.authorize(required_permissions=["workflow.execute"])
    assert decision.allowed is False
    assert decision.reason == "No identity context found"
