from pathlib import Path
import pandas as pd
from app import create_app
from app.extensions import db
from app.models.project import Project
from app.services.data_engine import profile_dataframe, smart_mapping, apply_cleaning

class TestConfig:
    TESTING=True; SECRET_KEY="test"; SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"; SQLALCHEMY_TRACK_MODIFICATIONS=False; STORAGE_ROOT=Path("/tmp/datavision-v12-tests")

def sample():
    return pd.DataFrame({"cliente_id":[1,1,2,2],"valor_compra":[10.0,10.0,None,40.0],"data_operacao":["01/10/2026"]*4,"status":["ok","ok","negado","ok"]})

def test_profiler_and_mapping():
    df=sample(); p=profile_dataframe(df); m=smart_mapping(df,"financeiro")
    assert p["rows"]==4 and p["missing"]==1 and p["duplicates"]==1
    assert m["valor_compra"]["role"]=="valor"
    assert m["data_operacao"]["role"]=="data_hora"

def test_cleaning_preserves_input():
    df=sample(); cleaned,h=apply_cleaning(df,["drop_duplicates","median::valor_compra"])
    assert len(df)==4 and df["valor_compra"].isna().sum()==1
    assert len(cleaned)==3 and cleaned["valor_compra"].isna().sum()==0 and h

def test_upload_route_exists():
    app=create_app(TestConfig)
    with app.app_context():
        p=Project(name="Dados",segment="geral",source_type="csv"); db.session.add(p); db.session.commit(); pid=p.id
    with app.test_client() as c:
        r=c.get(f"/projects/{pid}/data/upload")
        assert r.status_code==200 and b"CSV" in r.data
