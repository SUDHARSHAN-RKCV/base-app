#app/main/routes.py
from multiprocessing import context
import os
from flask import Flask, render_template, send_file, request, abort
import base64
import logging
from datetime import datetime, timedelta,timezone
from pathlib import Path
from uuid import UUID
from flask_login import current_user, login_required

import markdown
import requests
from flask import (
    Blueprint, current_app, jsonify, request, render_template, redirect,
    url_for, flash, abort, send_from_directory
)

import pandas as pd
from app.models import User, db

main = Blueprint('main', __name__)

# ------------------------
# main Routes
# ------------------------

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/changelog')
#@login_required
def changelog():
    changelog_path = os.path.join(current_app.root_path, '..', 'changelog.md')
    try:
        with open(changelog_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    except Exception as e:
        current_app.logger.error(f"Failed to load changelog: {e}")
        html_content = "<p><strong>Error loading changelog.</strong></p>"
    return render_template('changelog.html', changelog_html=html_content, active_page="changelog")
# ------------------------
# Context processors
# ------------------------
@main.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        notifications = [
            {"message": "🔔 Security alert on host 10.0.1.14", "link": ""},
            {"message": "📦 New VAPT report uploaded", "link": "/reports/vapt"},
            {"message": "🛠 Maintenance window scheduled", "link": "/maintenance"}
        ]
    else:
        notifications = []
    return {"notifications": notifications}