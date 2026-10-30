import os
import sys
import tempfile
import uuid
from pathlib import Path

# Isolated, offline test environment (set before the app is imported)
_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db.as_posix()}"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["JUDGE0_API_KEY"] = ""
os.environ["ENVIRONMENT"] = "development"
os.environ["ADMIN_EMAILS"] = "boss@gapx.test"
os.environ["EMAIL_DOMAIN_CHECK"] = "false"
os.environ["EMAIL_VERIFICATION_REQUIRED"] = "false"  # verification has its own tests
os.environ["SMTP_HOST"] = ""  # tests use fake domains; the checker has its own tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def register(client, email, password="Gx!9vQ#tRw42", name="Test User"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": name})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def make_user(client):
    def _make(email=None, **kw):
        return register(client, email or f"user_{uuid.uuid4().hex[:10]}@gapx.test", **kw)
    return _make
