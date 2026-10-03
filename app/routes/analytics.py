from flask import Blueprint, current_app, render_template
from app.extensions import db
from app.models.project import Project
from app.models.dataset import DatasetRun
from app.routes.data import _path
from app.services.data_engine import load_dataframe
from app.services.analytics_engine import build_analytics

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.get("/projects/<int:project_id>/analytics/<int:run_id>")
def dashboard(project_id, run_id):
    project = db.get_or_404(Project, project_id)
    run = db.get_or_404(DatasetRun, run_id)
    if run.project_id != project.id:
        return ("Not found", 404)
    df = load_dataframe(_path(run, processed=True))
    analytics = build_analytics(df, run.mapping_json or {}, project.segment, run.quality_score)
    return render_template("analytics/dashboard.html", project=project, run=run, analytics=analytics)
