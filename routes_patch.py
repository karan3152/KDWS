from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
import os
import secrets
import uuid

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, DocumentTypes, PasswordResetToken, FamilyMember, NewsUpdate
from forms import (
    LoginForm, RegisterForm, FirstLoginForm, PasswordResetRequestForm, PasswordResetForm,
    EmployeeProfileForm, EmployeeProfileEditForm, EmployerProfileForm, EmployeeSearchForm,
    CreateEmployeeForm, NewsUpdateForm, DocumentReviewForm
)
from utils import send_password_reset_email


# Basic routes
@app.route('/')
def index():
    """Homepage route."""
    # Get active news updates for the login page
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.published_date.desc()).limit(5).all()
    
    return render_template('home.html', news_updates=news_updates)
