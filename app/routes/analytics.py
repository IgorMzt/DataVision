from flask import Blueprint, render_template, request
from app.extensions import db
from app.models.project import Project
from app.models.dataset import DatasetRun
from app.routes.data import _path
from app.services.data_engine import load_dataframe
from app.services.analytics_engine import build_analytics
from app.services.anomaly_engine import analyze_anomalies
from app.services.comparison_engine import compare_runs

analytics_bp = Blueprint("analytics", __name__)


def _project_run(project_id, run_id):
    project = db.get_or_404(Project, project_id)
    run = db.get_or_404(DatasetRun, run_id)
    if run.project_id != project.id:
        return None, None
    return project, run


@analytics_bp.get("/projects/<int:project_id>/analytics/<int:run_id>")
def dashboard(project_id, run_id):
    project, run = _project_run(project_id, run_id)
    if not project:
        return ("Not found", 404)
    df = load_dataframe(_path(run, processed=True))
    analytics = build_analytics(df, run.mapping_json or {}, project.segment, run.quality_score)
    anomalies = analyze_anomalies(df, run.mapping_json or {}, project.segment)
    runs = DatasetRun.query.filter_by(project_id=project.id).order_by(DatasetRun.created_at.desc()).all()
    return render_template("analytics/dashboard.html", project=project, run=run, analytics=analytics, anomalies=anomalies, runs=runs)


@analytics_bp.get("/projects/<int:project_id>/analytics/<int:run_id>/compare")
def compare(project_id, run_id):
    project, run = _project_run(project_id, run_id)
    if not project:
        return ("Not found", 404)
    other_id = request.args.get("with", type=int)
    previous = db.session.get(DatasetRun, other_id) if other_id else None
    if not previous or previous.project_id != project.id or previous.id == run.id:
        previous = (DatasetRun.query.filter(DatasetRun.project_id == project.id, DatasetRun.id != run.id)
                    .order_by(DatasetRun.created_at.desc()).first())
    if not previous:
        return render_template("analytics/compare.html", project=project, run=run, previous=None, comparison=None, runs=[])
    current_df = load_dataframe(_path(run, processed=True))
    previous_df = load_dataframe(_path(previous, processed=True))
    comparison = compare_runs(current_df, previous_df, run, previous)
    runs = DatasetRun.query.filter(DatasetRun.project_id == project.id, DatasetRun.id != run.id).order_by(DatasetRun.created_at.desc()).all()
    return render_template("analytics/compare.html", project=project, run=run, previous=previous, comparison=comparison, runs=runs)
