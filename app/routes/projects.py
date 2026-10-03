import shutil
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from app.extensions import db
from app.models.project import Project

projects_bp = Blueprint("projects", __name__)
SEGMENTS = {"financeiro", "comercio", "empresa", "geral"}
SOURCES = {"csv", "xlsx", "postgresql", "mysql"}

@projects_bp.get("/")
def index():
    projects = Project.query.filter_by(archived=False).order_by(Project.updated_at.desc()).all()
    archived = Project.query.filter_by(archived=True).order_by(Project.updated_at.desc()).all()
    return render_template("projects/index.html", projects=projects, archived=archived)

@projects_bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        segment = request.form.get("segment", "geral")
        source_type = request.form.get("source_type", "csv")
        description = request.form.get("description", "").strip()
        if not name:
            flash("Informe um nome para o projeto.", "error")
            return render_template("projects/create.html")
        if segment not in SEGMENTS or source_type not in SOURCES:
            flash("Configuração de projeto inválida.", "error")
            return render_template("projects/create.html")
        project = Project(name=name, segment=segment, source_type=source_type, description=description)
        db.session.add(project)
        db.session.commit()
        (current_app.config["STORAGE_ROOT"] / str(project.id)).mkdir(parents=True, exist_ok=True)
        flash("Projeto criado. A base está pronta para receber dados na V1.2.", "success")
        return redirect(url_for("projects.detail", project_id=project.id))
    return render_template("projects/create.html")

@projects_bp.get("/<int:project_id>")
def detail(project_id):
    project = db.get_or_404(Project, project_id)
    return render_template("projects/detail.html", project=project)

@projects_bp.route("/<int:project_id>/edit", methods=["GET", "POST"])
def edit(project_id):
    project = db.get_or_404(Project, project_id)
    if request.method == "POST":
        project.name = request.form.get("name", project.name).strip() or project.name
        segment = request.form.get("segment", project.segment)
        if segment in SEGMENTS:
            project.segment = segment
        project.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Projeto atualizado.", "success")
        return redirect(url_for("projects.detail", project_id=project.id))
    return render_template("projects/create.html", project=project, editing=True)

@projects_bp.post("/<int:project_id>/duplicate")
def duplicate(project_id):
    original = db.get_or_404(Project, project_id)
    copy = Project(name=f"{original.name} — cópia", segment=original.segment, description=original.description, source_type=original.source_type)
    db.session.add(copy)
    db.session.commit()
    (current_app.config["STORAGE_ROOT"] / str(copy.id)).mkdir(parents=True, exist_ok=True)
    flash("Projeto duplicado.", "success")
    return redirect(url_for("projects.detail", project_id=copy.id))

@projects_bp.post("/<int:project_id>/archive")
def archive(project_id):
    project = db.get_or_404(Project, project_id)
    project.archived = not project.archived
    db.session.commit()
    flash("Projeto arquivado." if project.archived else "Projeto restaurado.", "success")
    return redirect(url_for("projects.index"))

@projects_bp.post("/<int:project_id>/delete")
def delete(project_id):
    project = db.get_or_404(Project, project_id)
    storage = current_app.config["STORAGE_ROOT"] / str(project.id)
    db.session.delete(project)
    db.session.commit()
    if storage.exists():
        shutil.rmtree(storage, ignore_errors=True)
    flash("Projeto excluído permanentemente.", "success")
    return redirect(url_for("projects.index"))
