#app/main/routes.pyfrom app.models import User, db, SupportTicketimport os
import base64
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID
from flask_login import current_user, login_required
from google import auth
import markdown
import requests
from flask import (
    Flask, request, Blueprint, current_app, jsonify, render_template,
    redirect, url_for, flash, send_from_directory, send_file, abort
)
from app.extensions import limiter
import pandas as pd
from app.models import User, db, UserNotification
from .security import login, logout

main = Blueprint('main', __name__)

# ------------------------
# main Routes
# ------------------------

@main.route('/', methods=['GET'])
def home():
    return render_template('home.html', active_page="home")

@main.route('/tools', methods=['GET'])
def tools():
    return render_template('home.html', active_page="tools")
@main.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('home.html', active_page="dashboard")
@main.route('/reports', methods=['GET'])
def reports():
    return render_template('home.html', active_page="reports")



@main.route('/UM', methods=['GET'])
@login_required
def admin():
    # only allow users with admin role (case insensitive)
    if getattr(current_user, 'role', '').upper() != 'ADMIN':
        abort(403)
    return render_template('user/UM.html', active_page="admin")

@main.route('/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    # ensure notification belongs to current user
    notif = UserNotification.query.filter_by(id=notification_id, user_id=current_user.user_id).first()
    if not notif:
        abort(404)
    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.session.commit()
    unread = UserNotification.query.filter_by(user_id=current_user.user_id, is_read=False).count()
    return jsonify({"unread": unread})

@main.route('/login', methods=['GET', 'POST'])
def login_route():
    return login()

@main.route('/logout', methods=['GET'])
def logout_route():
    return logout()

@main.route('/changelog', methods=['GET'])
@login_required
def changelog():
    changelog_path = Path(current_app.root_path).parent / "changelog.md"

    try:
        with open(changelog_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    except Exception as e:
        current_app.logger.error(f"Failed to load changelog: {e}")
        html_content = "<p><strong>Error loading changelog.</strong></p>"
    return render_template('changelog.html', changelog_html=html_content, active_page="changelog")

