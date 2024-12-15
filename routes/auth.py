from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from . import UserInfo
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = UserInfo.query.filter_by(userid=username).first()
        if user and user.password == password:
            session['username'] = username
            session['role'] = user.role_id
            return redirect(url_for('admin.dashboard'))  # Admin or user dashboard
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
