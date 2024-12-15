from flask import Blueprint, render_template, flash, session, redirect, url_for, request
from . import UserInfo
from . import VisitorInfo
from . import db
from datetime import datetime

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@admin.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if session.get('role') != 1:  # Only admins can create users
        flash("Access denied", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name')
        userid = request.form.get('userid')
        password = request.form.get('password')

        if UserInfo.query.filter_by(userid=userid).first():
            flash("User already exists", "danger")
        else:
            user = UserInfo(name=name, userid=userid, password=password, createdby=session['username'])
            db.session.add(user)
            db.session.commit()
            flash("User created successfully", "success")
            return redirect(url_for('admin.dashboard'))

    return render_template('create_user.html')
