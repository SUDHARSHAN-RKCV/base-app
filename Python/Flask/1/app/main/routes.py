#app/main/routes.py
from multiprocessing import context
import os
import base64
import logging
from datetime import datetime, timedelta,timezone
from pathlib import Path
from uuid import UUID
from flask_login import current_user, login_required
import markdown
import requests
from flask import (
    Flask, request, Blueprint, current_app, jsonify, render_template,
    redirect, url_for, flash, send_from_directory, send_file,  abort
)
from app.extentions import limiter
import pandas as pd
from app.models import User, db,SupportTicket,UserNotification

main = Blueprint('main', __name__)

# ------------------------
# main Routes
# ------------------------

@main.route('/')
def home():
    return render_template('home.html',unread_count=0,active_page="home")

@main.route('/tools')
def tools():
    return render_template('home.html',unread_count=0,active_page="tools")
@main.route('/dashboard')
def dashboard():
    return render_template('home.html',unread_count=0,active_page="dashboard")
@main.route('/admin')
def admin():
    return render_template('home.html',unread_count=0,active_page="admin")




@main.route('/changelog')
#@login_required
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

@main.route("/support", methods=["POST"])
def support():
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not subject or not message:
        flash("Subject and message are required.", "danger")
        return redirect(request.referrer or url_for("main.home"))

    if len(subject) > 255:
        flash("Subject is too long.", "danger")
        return redirect(request.referrer or url_for("main.home"))

    ticket = SupportTicket(
        user_id=current_user.id if current_user.is_authenticated else None,
        email=current_user.email if current_user.is_authenticated else None,
        subject=subject,
        message=message
    )

    db.session.add(ticket)
    db.session.commit()
    current_app.logger.info(f"New support ticket: {subject}")

    flash("Support ticket submitted successfully.", "success")
    return redirect(request.referrer or url_for("main.home"))