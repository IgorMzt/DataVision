from flask import Flask
from config import Config
from .extensions import db, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if hasattr(config_class, "validate"):
        config_class.validate()

    app.config["STORAGE_ROOT"].mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    if app.config.get("TESTING"):
        app.config["WTF_CSRF_ENABLED"] = False
    csrf.init_app(app)

    from .routes.main import main_bp
    from .routes.projects import projects_bp
    from .routes.data import data_bp
    from .routes.analytics import analytics_bp
    from .routes.exports import exports_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(data_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(exports_bp)

    with app.app_context():
        from .models.project import Project
        from .models.dataset import DatasetRun
        db.create_all()

    return app
