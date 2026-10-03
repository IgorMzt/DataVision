from pathlib import Path
from app import create_app
from app.extensions import db

class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORAGE_ROOT = Path("/tmp/datavision-tests")

def test_home_works():
    app = create_app(TestConfig)
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert b"DataVision" in response.data

def test_project_crud_entrypoint():
    app = create_app(TestConfig)
    with app.test_client() as client:
        response = client.post("/projects/new", data={"name":"Teste","segment":"geral","source_type":"csv","description":""}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Teste" in response.data
