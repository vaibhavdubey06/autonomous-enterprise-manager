import os
import pytest
from fastapi.testclient import TestClient

# Must set this before importing app to avoid loading actual models against prod db
os.environ["USE_SQLITE"] = "true"

from app.main import app
from app.core.database import Base, get_db, engine, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    def override_get_db():
        try:
            db = SessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_qdrant(mocker):
    # Mock Qdrant Client to prevent hitting local Qdrant server
    mock_client = mocker.patch("app.services.vectorstore.qdrant_service.QdrantClient")
    return mock_client


@pytest.fixture(autouse=True)
def mock_github(mocker):
    # Mock PyGithub to prevent hitting GitHub API
    mock_gh = mocker.patch("app.services.connectors.github.connector.Github")
    return mock_gh


@pytest.fixture(autouse=True)
def mock_gemini(mocker):
    # Mock google generative ai
    mock_genai = mocker.patch("app.services.llm.llm_service.genai")

    # Create a mock response
    class MockResponse:
        @property
        def text(self):
            return "This is a mocked LLM response."

    # Mock the GenerativeModel and its generate_content method
    mock_model = mocker.MagicMock()
    mock_model.generate_content.return_value = MockResponse()
    mock_genai.GenerativeModel.return_value = mock_model

    return mock_genai


@pytest.fixture(autouse=True)
def mock_cross_encoder(mocker):
    # Mock sentence transformers CrossEncoder to avoid loading massive models in tests
    mock_ce = mocker.patch("app.services.reranking.cross_encoder_service.CrossEncoder")
    return mock_ce


@pytest.fixture(autouse=True)
def mock_sentence_transformer(mocker):
    # Mock SentenceTransformer to prevent huggingface model downloads
    mock_st = mocker.patch(
        "app.services.embeddings.embedding_service.SentenceTransformer"
    )

    # Mock the return value of encode
    class MockArray:
        def __init__(self, is_str, count):
            self.is_str = is_str
            self.count = count

        def tolist(self):
            if self.is_str:
                return [0.0] * 384
            return [[0.0] * 384 for _ in range(self.count)]

    class MockModel:
        def encode(self, texts, **kwargs):
            if isinstance(texts, str):
                return MockArray(True, 1)
            return MockArray(False, len(texts))

    mock_st.return_value = MockModel()
    return mock_st
