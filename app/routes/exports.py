from flask import Blueprint, abort, request, send_file
from app.extensions import db
from app.models.project import Project
from app.models.dataset import DatasetRun
from app.routes.data import _path
from app.services.data_engine import load_dataframe
from app.services.analytics_engine import build_analytics
from app.services.anomaly_engine import analyze_anomalies
from app.services.export_service import export_csv, export_excel, export_pdf, export_chart_png

exports_bp = Blueprint("exports", __name__)


def _context(project_id, run_id):
    project = db.get_or_404(Project, project_id)
    run = db.get_or_404(DatasetRun, run_id)
    if run.project_id != project.id:
        abort(404)
    df = load_dataframe(_path(run, processed=True))
    analytics = build_analytics(df, run.mapping_json or {}, project.segment, run.quality_score)
    anomalies = analyze_anomalies(df, run.mapping_json or {}, project.segment)
    return project, run, df, analytics, anomalies


@exports_bp.get("/projects/<int:project_id>/analytics/<int:run_id>/export/<kind>")
def export(project_id, run_id, kind):
    project, run, df, analytics, anomalies = _context(project_id, run_id)
    base = f"datavision_{project.id}_execucao_{run.id}"
    if kind == "csv":
        return send_file(export_csv(df), mimetype="text/csv", as_attachment=True, download_name=f"{base}.csv")
    if kind == "xlsx":
        return send_file(export_excel(df), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=f"{base}.xlsx")
    if kind == "pdf":
        return send_file(export_pdf(project, run, analytics, anomalies), mimetype="application/pdf", as_attachment=True, download_name=f"{base}_relatorio.pdf")
    if kind == "png":
        index = request.args.get("chart", 0, type=int)
        charts = analytics.get("charts", [])
        if not charts or index < 0 or index >= len(charts):
            abort(404)
        return send_file(export_chart_png(charts[index]), mimetype="image/png", as_attachment=True, download_name=f"{base}_grafico_{index+1}.png")
    abort(404)
