"""
Application factory for the School Management System.

Using the factory pattern (create_app) rather than a global `app` object so the app
can be configured differently for testing vs. development vs. production, and so
extensions can be initialized without circular imports.
"""
import os
from flask import Flask, Blueprint
from flask_login import current_user

from config import config_by_name
from app.extensions import db, migrate, login_manager, bcrypt, mail, csrf


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # --- Initialize extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Registers every model with SQLAlchemy's metadata so `flask db migrate`
    # can see all tables, not just whichever ones happen to be imported elsewhere.
    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # --- Register blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.audit import audit_bp
    from app.routes.academic import academic_bp
    from app.routes.students import students_bp
    from app.routes.guardians import guardians_bp
    from app.routes.teachers import teachers_bp
    from app.routes.staff import staff_bp
    from app.routes.attendance import attendance_bp
    from app.routes.teacher_attendance import teacher_attendance_bp
    from app.routes.leave import leave_bp
    from app.routes.timetable import timetable_bp
    from app.routes.exams import exams_bp
    from app.routes.fees import fees_bp
    from app.routes.expenses import expenses_bp
    from app.routes.salaries import salaries_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(academic_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(guardians_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(teacher_attendance_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(salaries_bp)
    app.register_blueprint(reports_bp)

    # Temporary health-check — useful during setup, harmless to keep long-term.
    health_bp = Blueprint("health", __name__)

    @health_bp.route("/health")
    def health():
        return {"status": "ok", "app": app.config["APP_NAME"]}

    app.register_blueprint(health_bp)

    # Makes the role-filtered sidebar available to every template without
    # each view having to pass it in explicitly.
    @app.context_processor
    def inject_nav():
        from app.utils.navigation import visible_sections
        if current_user.is_authenticated:
            return {"nav_sections": visible_sections(current_user.role)}
        return {"nav_sections": []}

    return app
