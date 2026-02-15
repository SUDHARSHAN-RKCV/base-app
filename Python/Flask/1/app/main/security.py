#app/main/security.py
import os
import base64
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID
import requests

from flask import (
    Blueprint, current_app, jsonify, request, render_template, redirect,
    url_for, flash, abort, send_from_directory
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash


import fitz  # PyMuPDF
import mammoth
import pandas as pd
import markdown as md

import boto3
from sqlalchemy import create_engine
from dateutil import parser as dateparser
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from app import db
from models import User
from config import POSTGRES_URI
from forms import CreateUserForm

load_dotenv()

auth = Blueprint('auth', __name__, template_folder='templates')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



# ------------------------
# Auth Routes
# ------------------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return '', 204
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('user/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        theme = request.form.get('theme', 'system')
        current_user.theme = theme
        db.session.commit()
        flash('Settings updated.', 'success')
        return redirect(url_for('main.user_settings'))
    return render_template('user/settings.html', current_user=current_user)

# ------------------------
# Password Reset
# ------------------------
RESET_PASSWORD_FORM_TEMPLATE = 'user/reset_password_form.html'


@auth.route('/reset-password-form', methods=['GET', 'POST'])
def reset_password_form():
    return render_template(RESET_PASSWORD_FORM_TEMPLATE, email='')


@auth.route('/reset-password', methods=['GET', 'POST'])
@auth.route('/forgot-password', methods=['GET', 'POST'])
def reset_password_form_handler():
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for('main.reset_password_form'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User does not exist.", "danger")
        return redirect(url_for('main.reset_password_form'))

    if not new_password or len(new_password) < 8:
        flash("Password must be at least 8 characters long.", "danger")
        return render_template(RESET_PASSWORD_FORM_TEMPLATE, email=email)

    if new_password != confirm_password:
        flash("Passwords do not match.", "danger")
        return render_template(RESET_PASSWORD_FORM_TEMPLATE, email=email)

    user.password = generate_password_hash(new_password)
    db.session.commit()
    flash("Password has been reset successfully. Please log in.", "success")
    return redirect(url_for('main.login'))


# ------------------------
# Admin User Management
# ------------------------

@auth.route('/UM')
@login_required
def user_management():
    if current_user.role.lower() != 'admin':
        abort(403)
    users = User.query.all()
    return render_template('user/UM.html', users=users, active_page='UM', current_user=current_user)


@auth.route('/defadmin')
def defadmin():
    return redirect(url_for('main.user_management'))


@auth.route('/create', methods=['POST'])
@login_required
def create_user_post():
    if current_user.role.lower() != 'admin':
        abort(403)
    email = request.form['email']
    password = request.form['password']
    role = request.form['role'].upper()
    file_permission = request.form.get('file_permission', 'none')
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, role=role, is_active=True, file_permission=file_permission)
    db.session.add(new_user)
    db.session.commit()
    flash("User created successfully", "success")
    return redirect(url_for('main.user_management'))


@auth.route('/<uuid:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id: UUID):
    if current_user.role.lower() != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    user.role = request.form['role'].upper()
    user.is_active = 'is_active' in request.form
    user.file_permission = request.form.get('file_permission', 'none')
    db.session.commit()
    flash('User updated successfully', 'success')
    return redirect(url_for('main.user_management'))


@auth.route('/<uuid:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id: UUID):
    if current_user.role.lower() != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('main.user_management'))


@auth.route('/<uuid:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id: UUID):
    if current_user.role.lower() != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash('User status toggled', 'info')
    return redirect(url_for('main.user_management'))


@auth.route('/<uuid:user_id>/reset_password', methods=['POST'])
@login_required
def admin_reset_password(user_id: UUID):
    if current_user.role.lower() != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    if not new_password:
        flash("Password cannot be empty.", "danger")
        return redirect(url_for('main.user_management'))
    user.password = generate_password_hash(new_password)
    db.session.commit()
    flash("Password has been reset successfully.", "warning")
    return redirect(url_for('main.user_management'))


@auth.route('/create_user', methods=['GET', 'POST'])
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        new_user = User(
            role='admin',
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('main.defadmin'))
    return render_template('user/create_user.html', form=form)


