from datetime import datetime, timezone
from app.extensions import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    segment = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, default="")
    source_type = db.Column(db.String(30), nullable=False, default="csv")
    status = db.Column(db.String(20), nullable=False, default="ready")
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def segment_label(self):
        return {
            "financeiro": "Financeiro",
            "comercio": "Comércio",
            "empresa": "Empresarial",
            "geral": "Análise Geral",
        }.get(self.segment, self.segment.title())
