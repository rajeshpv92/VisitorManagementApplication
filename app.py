from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "2c093f1997d3713dc70782007352367a085a5c084d59c3c3bb6e216d99e7e4b8"

# Configure the SQL Server database URI
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://test:test@192.168.29.13:1433/master?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Database model for user_info table
class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    userid = db.Column(db.String(50), unique=True, nullable=False)
    role_id = db.Column(db.Integer, nullable=False, default=2)
    password = db.Column(db.String(100), nullable=False)
    createdby = db.Column(db.String(50), nullable=False)
    updatedby = db.Column(db.String(50), nullable=False)
    createdtime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updatedtime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Mock user data for login authentication
users = {'admin': 'password123'}

@app.route('/')
def home():
    return "Welcome to the Visitor Management System! <a href='/login'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Authentication check
        # if username in users and users[username] == password:
        #     session['username'] = username  # Store username in session

         # Query the User_Info table to check for the user
        user = UserInfo.query.filter_by(userid=username).first()
        if user and user.password == password:
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')
        # Check if the user exists and the password matches
    #     if user and user.password == password:  # You should hash and check the password in a real scenario
    #         session['username'] = username

    #         return redirect(url_for('dashboard'))
    #     else:
    #         flash('Invalid username or password. Please try again.', 'danger')

    # return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        name = request.form.get('name')
        userid = request.form.get('userid')
        password = request.form.get('password')

        if not name or not userid or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('create_user'))

        createdby = updatedby = session.get('username')

        # Check if the user already exists
        existing_user = UserInfo.query.filter_by(userid=userid).first()
        if existing_user:
            flash(f'User {userid} already exists!', 'danger')
            return redirect(url_for('create_user'))

        # Create new user record
        new_user = UserInfo(
            name=name,
            userid=userid,
            password=password,
            createdby=createdby,
            updatedby=updatedby
        )

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash(f'User {userid} created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_user.html')

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    user = UserInfo.query.get_or_404(id)

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.password = request.form.get('password')
        user.updatedby = session.get('username')
        user.updatedtime = datetime.utcnow()

        db.session.commit()

        flash(f'User {user.userid} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('update_user.html', user=user)

if __name__ == '__main__':
    # Set up application context and create tables
   # with app.app_context():
    #    db.create_all()
    app.run(debug=True)
