# app/__init__.py
import os
from pathlib import Path
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from app.models import db, User
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
IST = ZoneInfo("Asia/Kolkata")
from .extensions import limiter
load_dotenv()

login_manager = LoginManager()
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("SECRET_KEY environment variable must be set")



def create_app():
    app = Flask(__name__, static_folder="main/static", template_folder="main/templates")
    app.config["APP_NAME"] = os.getenv("APP_NAME", "MyApp")
    app.config["SUPPORT_EMAIL"] = os.getenv("SUPPORT_EMAIL","support@yourdomain.com")
    from app.main.security import auth
    app.register_blueprint(auth)

    # if running behind one or more proxies, ensure remote_addr uses X-Forwarded-For
    from werkzeug.middleware.proxy_fix import ProxyFix
    # adjust x_for count as needed for your deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

    limiter.init_app(app)
    # ---------------------------
    # Core Config
    # ---------------------------
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRES_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # ensure application version is available
    app.config['APP_VERSION'] = os.getenv("APP_VERSION", "0.0.0")

    # 🔥 Maintenance Toggle
    app.config['MAINTENANCE_MODE'] = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
    
    @app.context_processor
    def inject_app_globals():
        return {
            "app_name": app.config.get("APP_NAME"),
            "support_email": app.config.get("SUPPORT_EMAIL"),
            "app_version": app.config.get("APP_VERSION")
        }

    window = os.getenv("MAINTENANCE_WINDOW")

    app.config["MAINTENANCE_WINDOW_START"] = None
    app.config["MAINTENANCE_WINDOW_END"] = None
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login_route'

    @app.context_processor
    def inject_app_name():
        return {
            'app_name': app.config.get('APP_NAME', 'APP NAME'),
            'app_version': app.config.get('APP_VERSION', '0.0.0')
        }

    # ---------------------------
    # Maintenance Interceptor
    # ---------------------------
    if window:
        try:
            start_str, end_str = window.split("/")

            start = datetime.fromisoformat(start_str).replace(tzinfo=IST)
            end = datetime.fromisoformat(end_str).replace(tzinfo=IST)

            app.config["MAINTENANCE_WINDOW_START"] = start
            app.config["MAINTENANCE_WINDOW_END"] = end
        except Exception as e:
            app.logger.error("Invalid MAINTENANCE_WINDOW format", exc_info=True)

    @app.before_request
    def check_for_maintenance():

        if not app.config['MAINTENANCE_MODE']:
            return

        from flask_login import current_user
        from datetime import datetime, timezone

        # Allow static
        if request.path.startswith('/static/') or request.path.startswith('/main/static/'):
            return

        # Allow admins
        if current_user.is_authenticated and current_user.role == "admin":
            return

        start = app.config.get("MAINTENANCE_WINDOW_START")
        end = app.config.get("MAINTENANCE_WINDOW_END")
        

        now = datetime.now(timezone.utc)

        # If window defined, check time
        if start and end:
            if not (start <= now <= end):
                return  # Outside maintenance window → allow traffic

            retry_after = int((end - now).total_seconds())
        else:
            retry_after = 3600  # fallback

        response = render_template(
            "maintenance.html",
            start=start,
            end=end
        )

        return response, 503, {"Retry-After": str(retry_after)}

    
    # ---------------------------
    # Register Blueprints
    # ---------------------------
    from app.main.routes import main
    app.register_blueprint(main)

    # ---------------------------
    # Error Handlers
    # ---------------------------
    import logging
    from logging.handlers import RotatingFileHandler
    from pathlib import Path

    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_all_errors(e):

        if isinstance(e, HTTPException):
            app.logger.warning(
                f"HTTP Error {e.code} - {request.method} {request.path} - IP: {request.remote_addr}"
            )
            return render_template(f"errors/{e.code}.html"), e.code

        # Uncaught Exception (Crash)
        app.logger.error(
            f"Unhandled Exception - {request.method} {request.path} - IP: {request.remote_addr}",
            exc_info=True
        )

        return render_template("errors/500.html"), 500


    # ---------------------------
    # Logging Setup
    # ---------------------------

    log_dir = Path(app.root_path) / "main" / "static" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app-log.txt"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )

    file_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s | %(pathname)s:%(lineno)d"
    )

    file_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
