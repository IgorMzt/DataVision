from datetime import datetime, timezone
from app.extensions import db

class DatasetRun(db.Model):
    __tablename__ = "dataset_runs"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    processed_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20), nullable=False)
    row_count = db.Column(db.Integer, default=0)
    column_count = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0)
    profile_json = db.Column(db.JSON, default=dict)
    mapping_json = db.Column(db.JSON, default=dict)
    transformations_json = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    project = db.relationship("Project", backref=db.backref("dataset_runs", lazy=True, cascade="all, delete-orphan"))
