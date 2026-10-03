from pathlib import Path
import pandas as pd
from app import create_app
from app.extensions import db
from app.models.project import Project
from app.models.dataset import DatasetRun
from app.services.analytics_engine import build_analytics

class TestConfig:
    TESTING=True; SECRET_KEY="test"; SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"; SQLALCHEMY_TRACK_MODIFICATIONS=False; STORAGE_ROOT=Path("/tmp/datavision-v13-tests")

def test_financial_analytics():
    df=pd.DataFrame({"cliente":["A","A","B"],"valor":[10,20,70],"status":["Aprovada","Negada","Aprovada"],"produto":["X","X","Y"],"data":["01/10/2026","02/10/2026","02/10/2026"]})
    roles={"cliente":"cliente","valor":"valor","status":"status","produto":"produto","data":"data_hora"}
    mapping={c:{"role":r} for c,r in roles.items()}
    result=build_analytics(df,mapping,"financeiro",96.0)
    assert result["segment"]=="financeiro"
    assert len(result["kpis"])>=4
    assert any(c["type"]=="doughnut" for c in result["charts"])
    assert result["insights"]

def test_dashboard_route():
    app=create_app(TestConfig)
    root=TestConfig.STORAGE_ROOT; root.mkdir(parents=True,exist_ok=True)
    with app.app_context():
        project=Project(name="Financeiro",segment="financeiro",source_type="csv"); db.session.add(project); db.session.flush()
        folder=root/str(project.id)/"runs"/"1"; folder.mkdir(parents=True,exist_ok=True)
        pd.DataFrame({"valor":[10,20],"status":["Aprovada","Negada"]}).to_csv(folder/"original.csv",index=False)
        run=DatasetRun(project_id=project.id,original_name="dados.csv",original_path=str((folder/"original.csv").relative_to(root)),file_type="csv",row_count=2,column_count=2,quality_score=100,mapping_json={"valor":{"role":"valor"},"status":{"role":"status"}})
        db.session.add(run); db.session.commit(); pid,rid=project.id,run.id
    with app.test_client() as client:
        response=client.get(f"/projects/{pid}/analytics/{rid}")
        assert response.status_code==200
        assert b"INSIGHT ENGINE" in response.data
