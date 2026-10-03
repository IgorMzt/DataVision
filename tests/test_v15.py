from pathlib import Path
import numpy as np
import pandas as pd
from app import create_app
from app.extensions import db
from app.models.project import Project
from app.models.dataset import DatasetRun
from app.services.data_engine import profile_dataframe
from app.services.export_service import export_csv, export_excel, export_chart_png

class TestConfig:
    TESTING=True
    SECRET_KEY="test"
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    STORAGE_ROOT=Path("/tmp/datavision-v15-tests")
    WTF_CSRF_ENABLED=False


def test_quality_detects_non_finite_numeric_value():
    df=pd.DataFrame({"valor":[10.0,20.0,np.inf]})
    p=profile_dataframe(df)
    assert p["quality_parts"]["validade"] < 100
    assert p["column_profiles"][0]["invalid"] == 1


def test_exports_generate_content():
    df=pd.DataFrame({"a":[1,2],"b":["x","y"]})
    assert len(export_csv(df).getvalue()) > 10
    assert len(export_excel(df).getvalue()) > 100
    chart={"type":"bar","title":"Teste","labels":["A","B"],"values":[1,2]}
    assert export_chart_png(chart).getvalue().startswith(b"\x89PNG")


def test_csrf_disabled_automatically_during_tests():
    app=create_app(TestConfig)
    with app.test_client() as client:
        response=client.post("/projects/new",data={"name":"V15","segment":"geral","source_type":"csv","description":""},follow_redirects=True)
        assert response.status_code == 200


def test_exports_blueprint_is_registered():
    app=create_app(TestConfig)
    rules={rule.endpoint for rule in app.url_map.iter_rules()}
    assert "exports.export" in rules
