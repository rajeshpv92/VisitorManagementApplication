# from flask import Blueprint, render_template, redirect, request, url_for, flash, session
# from models.visitor import User, db, bcrypt

# auth = Blueprint('auth', __name__)

# @auth.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User.query.filter_by(username=username).first()
#         if user and user.check_password(password):
#             session['user_id'] = user.id
#             session['role'] = user.role
#             return redirect(url_for('home'))
#         else:
#             flash('Invalid credentials', 'danger')
#     return render_template('login.html')

# @auth.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('auth.login'))
from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_bcrypt import Bcrypt
from models.visitor import db
from services.db_service import User

auth_blueprint = Blueprint("auth", __name__)

@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and Bcrypt().check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            return redirect(url_for("visitor.home"))
        return "Invalid credentials"
    return render_template("login.html")

@auth_blueprint.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
