"""
ImageLab — Flask Application Factory
"""
import os
import logging

from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)

    metrics = PrometheusMetrics(app)
    metrics.info("imagelab_backend_info", "ImageLab backend metrics", version="1.0.0")
    app.config.from_object(config_by_name[config_name])

    # ---------- Extensions ----------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ---------- Logging (12-factor #11 — stdout) ----------
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ---------- Ensure upload folder ----------
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ---------- Register Blueprints ----------
    from app.routes.auth import auth_bp
    from app.routes.images import images_bp
    from app.routes.processing import processing_bp
    from app.routes.cache_demo import cache_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(images_bp, url_prefix="/api/images")
    app.register_blueprint(processing_bp, url_prefix="/api/images")
    app.register_blueprint(cache_bp, url_prefix="/api")

    # ---------- Health check ----------
    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    # ---------- Create tables (dev convenience) ----------
    with app.app_context():
        from app import models  # noqa: F401
        # Ensure instance directory exists for SQLite
        instance_path = os.path.join(os.path.dirname(__file__), '..', 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db.create_all()

    return app
