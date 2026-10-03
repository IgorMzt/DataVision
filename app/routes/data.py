import json
from pathlib import Path
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.project import Project
from app.models.dataset import DatasetRun
from app.services.data_engine import load_dataframe, profile_dataframe, smart_mapping, cleaning_recommendations, apply_cleaning

data_bp = Blueprint("data", __name__)
ALLOWED={".csv",".xlsx",".xlsm"}
ROLES=[("outro","Outro / ignorar"),("id","Identificador"),("cliente","Cliente"),("valor","Valor"),("data_hora","Data/Hora"),("status","Status"),("produto","Produto"),("quantidade","Quantidade"),("departamento","Departamento"),("funcionario","Funcionário")]

def _run(run_id): return db.get_or_404(DatasetRun, run_id)
def _path(run, processed=False):
    rel=run.processed_path if processed and run.processed_path else run.original_path
    return Path(current_app.config["STORAGE_ROOT"]) / rel

@data_bp.route("/projects/<int:project_id>/data/upload", methods=["GET","POST"])
def upload(project_id):
    project=db.get_or_404(Project, project_id)
    if request.method=="POST":
        file=request.files.get("dataset")
        if not file or not file.filename:
            flash("Selecione um arquivo CSV ou XLSX.","error"); return redirect(request.url)
        suffix=Path(file.filename).suffix.lower()
        if suffix not in ALLOWED:
            flash("Formato não suportado. Use CSV ou XLSX.","error"); return redirect(request.url)
        folder=Path(current_app.config["STORAGE_ROOT"])/str(project.id)/"runs"
        folder.mkdir(parents=True,exist_ok=True)
        safe=secure_filename(file.filename) or f"dataset{suffix}"
        temp=folder/f"upload_{safe}"; file.save(temp)
        try:
            df=load_dataframe(temp); profile=profile_dataframe(df)
        except Exception as exc:
            temp.unlink(missing_ok=True); flash(f"Não foi possível ler o arquivo: {exc}","error"); return redirect(request.url)
        run=DatasetRun(project_id=project.id, original_name=file.filename, original_path="", file_type=suffix.lstrip("."), row_count=len(df), column_count=len(df.columns), quality_score=profile["quality"], profile_json=profile)
        db.session.add(run); db.session.flush()
        run_folder=folder/str(run.id); run_folder.mkdir(parents=True,exist_ok=True)
        final=run_folder/("original"+suffix); temp.replace(final)
        run.original_path=str(final.relative_to(Path(current_app.config["STORAGE_ROOT"])))
        previous=DatasetRun.query.filter(DatasetRun.project_id==project.id, DatasetRun.id!=run.id).order_by(DatasetRun.created_at.desc()).first()
        prev_roles={k:v.get("role","outro") for k,v in (previous.mapping_json or {}).items()} if previous else {}
        run.mapping_json=smart_mapping(df,project.segment,prev_roles)
        db.session.commit()
        flash("Dataset importado e analisado.","success")
        return redirect(url_for("data.profile",project_id=project.id,run_id=run.id))
    return render_template("data/upload.html",project=project)

@data_bp.get("/projects/<int:project_id>/data/<int:run_id>/profile")
def profile(project_id,run_id):
    project=db.get_or_404(Project,project_id); run=_run(run_id)
    if run.project_id!=project.id: return ("Not found",404)
    df=load_dataframe(_path(run,processed=True))
    preview=df.head(8).fillna("").to_dict(orient="records")
    return render_template("data/profile.html",project=project,run=run,profile=run.profile_json,columns=list(df.columns),preview=preview)

@data_bp.route("/projects/<int:project_id>/data/<int:run_id>/mapping",methods=["GET","POST"])
def mapping(project_id,run_id):
    project=db.get_or_404(Project,project_id); run=_run(run_id)
    if request.method=="POST":
        mapping={}
        for col,info in (run.mapping_json or {}).items():
            mapping[col]={**info,"role":request.form.get(f"role::{col}","outro"),"confidence":"confirmado","reason":"confirmado pelo usuário"}
        run.mapping_json=mapping; db.session.commit(); flash("Mapeamento confirmado.","success")
        return redirect(url_for("data.clean",project_id=project.id,run_id=run.id))
    return render_template("data/mapping.html",project=project,run=run,roles=ROLES)

@data_bp.route("/projects/<int:project_id>/data/<int:run_id>/clean",methods=["GET","POST"])
def clean(project_id,run_id):
    project=db.get_or_404(Project,project_id); run=_run(run_id); df=load_dataframe(_path(run,processed=True))
    recs=cleaning_recommendations(df)
    if request.method=="POST":
        actions=request.form.getlist("actions")
        cleaned,history=apply_cleaning(df,actions)
        run_folder=Path(current_app.config["STORAGE_ROOT"])/str(project.id)/"runs"/str(run.id)
        processed=run_folder/"processed.csv"; cleaned.to_csv(processed,index=False)
        run.processed_path=str(processed.relative_to(Path(current_app.config["STORAGE_ROOT"])))
        run.transformations_json=(run.transformations_json or [])+history
        new_profile=profile_dataframe(cleaned); run.profile_json=new_profile; run.row_count=len(cleaned); run.column_count=len(cleaned.columns); run.quality_score=new_profile["quality"]
        db.session.commit(); flash("Transformações aplicadas ao dataset processado. O original foi preservado.","success")
        return redirect(url_for("data.profile",project_id=project.id,run_id=run.id))
    return render_template("data/clean.html",project=project,run=run,recommendations=recs,history=run.transformations_json or [])
