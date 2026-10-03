from flask import Blueprint, render_template
from app.models.project import Project

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def index():
    recent_projects = Project.query.filter_by(archived=False).order_by(Project.updated_at.desc()).limit(3).all()
    return render_template("index.html", recent_projects=recent_projects)
