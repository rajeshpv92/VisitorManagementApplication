from functools import wraps
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import logging
from models.visitor import VisitorInfo  # Ensure correct import
from models.user import UserInfo
from models.employee import EmployeeInfo
from models import db  # Ensure correct import
from models.department import DepartmentInfo
import pandas as pd
from werkzeug.utils import secure_filename
import os

# Flask app factory
def create_app():
    """
    Application factory for creating Flask app instances.
    """
    app = Flask(__name__)
    app.secret_key = "2c093f1997d3713dc70782007352367a085a5c084d59c3c3bb6e216d99e7e4b8"  # Replace with a secure key in production

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://test:test@192.168.29.13:1433/master?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Setup logging
    setup_logging(app)

    # Register routes
    register_routes(app)

    with app.app_context():
        db.create_all()  # Ensure tables are created

    return app

# Setup logging for production
def setup_logging(app):
    handler = logging.FileHandler("app.log")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

# Admin access control decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 1:
            flash("You must be an admin to access this page.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Route definitions
def register_routes(app):
    @app.route("/")
    def home():
        return "Welcome to the Visitor Management System! <a href='/login'>Login</a>"

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = UserInfo.query.filter_by(UserID=username).first()
            if user and user.Password == password:
                session["username"] = username
                session["role"] = user.Role_ID
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "danger")
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    # Define the allowed file extensions
    ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

    # Check if the file is allowed
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/create_user", methods=["GET", "POST"])
    @admin_required
    def create_user():
        if request.method == "POST":
            name = request.form.get("name")
            userid = request.form.get("userid")
            password = request.form.get("password")

            if not all([name, userid, password]):
                flash("All fields are required.", "danger")
                return redirect(url_for("create_user"))

            if UserInfo.query.filter_by(UserID=userid).first():
                flash(f"User {userid} already exists!", "danger")
                return redirect(url_for("create_user"))

            createdby = updatedby = session.get("username")

            try:
                new_user = UserInfo(
                    Name=name,
                    UserID=userid,  # Updated to match the model
                    Password=password,
                    CreatedBy=createdby,
                    UpdatedBy=updatedby,
                    CreatedTime=datetime.now(),
                    UpdatedTime=datetime.now(),
                )

                db.session.add(new_user)
                db.session.commit()
                flash(f"User {userid} created successfully!", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating user: {str(e)}", "danger")
        return render_template("create_user.html")
    
    #Create View User definition.
    @app.route("/view_users", methods=["GET", "POST"])
    def view_users():
        try:
           if request.method == "GET":
            # Fetch all user for display
            users = UserInfo.query.all()
            app.logger.info("Users fetched from the database: %s", users)  # Debugging info
        except Exception as e:
            app.logger.error(f"Error querying Users: {e}")
            flash("An error occurred while fetching Users.", "danger")
            return redirect(url_for("dashboard"))

        users = UserInfo.query.all()

        return render_template("view_users.html", users=users)

    # Create Visitor definition.
    @app.route("/create_visitor", methods=["GET", "POST"])
    def create_visitor():
        if request.method == "POST":
            name = request.form.get("name")  # Consistent lowercase naming
            contact = request.form.get("contact")
            purpose = request.form.get("purpose")
            address = request.form.get("address")
            photo = request.files.get('photo')
            created_by = updated_by = session.get("username")

            # Validation: check if all required fields are provided
            if not name or not contact or not purpose:
                flash("All fields are required.", "danger")
                return redirect(url_for("create_visitor"))

            # Save the photo to a specific folder
            if photo:
                filename = secure_filename(photo.filename)  # Ensure safe filenames
                photo_path = os.path.join('static/uploads', filename)
                photo.save(photo_path)

            try:
                # Create a new VisitorInfo object to add to the database
                new_visitor = VisitorInfo(
                    Name=name,  # Match the model column name
                    ContactNumber=contact,  # Match the model column name
                    Purpose=purpose,  # Match the model column name
                    Address=address,  # Match the model column name
                    photo=photo_path, # Store the path to the photo in the database
                    CreatedBy=created_by,  # Match the model column name
                    UpdatedBy=updated_by,  # Match the model column name
                    CreatedTime=datetime.now(),  # Automatically set created time
                    UpdatedTime=datetime.now(),  # Automatically set updated time
                    CheckIn=datetime.now(),  # Set current time as check-in
                    CheckOut=None  # Check-out will be set later
                )
                db.session.add(new_visitor)
                db.session.commit()
                flash(f"Visitor {name} added successfully!", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding visitor: {str(e)}", "danger")
        return render_template("create_visitor.html")

    #Create View Visitor definition.
    @app.route("/view_visitors", methods=["GET", "POST"])
    def view_visitors():
        visitors = []
        try:
           if request.method == "GET":
            # Fetch all visitors for display
            visitors = VisitorInfo.query.all()
            app.logger.info("Visitors fetched from the database: %s", visitors)  # Debugging info
        except Exception as e:
            app.logger.error(f"Error querying visitors: {e}")
            flash("An error occurred while fetching visitors.", "danger")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            # Get the visitor ID from the form
            visitor_id = request.form.get("ID")
            app.logger.info("Visitor ID from the form: %s", visitor_id)  # Debugging info

            if visitor_id:
                try:
                    # Fetch the specific visitor
                    visitor = VisitorInfo.query.get(visitor_id)
                    app.logger.info("Visitor object fetched: %s", visitor)  # Debugging info

                    if visitor and not visitor.CheckOut:
                        # Update check-out time and updater information
                        visitor.CheckOut = datetime.utcnow()
                        visitor.UpdatedBy = session.get("username")
                        db.session.commit()
                        flash(f"Visitor {visitor.Name} checked out successfully!", "success")
                    else:
                        flash("Visitor not found or already checked out.", "warning")
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error during visitor checkout: {e}")
                    flash(f"Error during checkout: {e}", "danger")
            else:
                flash("Invalid Visitor ID.", "danger")

                # Re-fetch the visitors after the checkout operation
        visitors = VisitorInfo.query.all()

        return render_template("view_visitors.html", visitors=visitors)

    # Create Employee definition.
    @app.route("/create_employee", methods=["GET", "POST"])
    def create_employee():
        if request.method == "POST":
            empno = request.form.get("empno")
            empname = request.form.get("empname")
            mobileno = request.form.get("mobileno")
            deptno = request.form.get("Deptno")  # Ensure you are getting the Deptno value
            created_by = updated_by = session.get("username")

            # Validation: check if all required fields are provided
            if not empno or not empname or not mobileno or not deptno:
                flash("All fields are required.", "danger")
                return redirect(url_for("create_employee"))

            try:
                # Create a new EmployeeInfo object to add to the database
                new_employee = EmployeeInfo(
                    EMPNO=empno,
                    EMPNAME=empname,
                    MobileNo=mobileno,
                    DEPTNO=deptno,  # Ensure DEPTNO is passed correctly
                    CreatedBy=created_by,
                    UpdatedBy=updated_by,
                    CreatedTime=datetime.now(),
                    UpdatedTime=datetime.now()
                )
                db.session.add(new_employee)
                db.session.commit()
                flash(f"Employee {empname} added successfully!", "success")
                return redirect(url_for("create_employee"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding Employee: {str(e)}", "danger")
                return redirect(url_for("create_employee"))

        # Fetch departments here inside the route
        departments = DepartmentInfo.query.all()
    
        # Ensure to pass the departments to the template
        return render_template("create_employee.html", departments=departments)


    #Create View Employee definition.
    @app.route("/view_employee", methods=["GET", "POST"])
    def view_employees():
        try:
           if request.method == "GET":
            # Fetch all Employee for display
            employees = EmployeeInfo.query.all()
            app.logger.info("Employees fetched from the database: %s", employees)  # Debugging info
        except Exception as e:
            app.logger.error(f"Error querying visitors: {e}")
            flash("An error occurred while fetching employees.", "danger")
            return redirect(url_for("dashboard"))

                # Re-fetch the visitors after the checkout operation
        employees = EmployeeInfo.query.all()

        return render_template("view_employee.html", employees=employees)

    @app.route("/import_employees", methods=["POST"])
    def import_employees():
        file = request.files['file']
        mappings = request.form.get('mappings')

        if not file or not mappings:
            flash("Invalid file or column mappings.", "danger")
            return redirect(url_for("import_employees"))

        mappings = json.loads(mappings)
    
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join("uploads", filename)
        file.save(file_path)

        # Read the Excel file using pandas
        try:
            data = pd.read_excel(file_path)
        
            for index, row in data.iterrows():
                empno = row[mappings.get("EMPNO")]
                empname = row[mappings.get("EMPNAME")]
                mobileno = row[mappings.get("MobileNo")]
                deptno = row[mappings.get("DEPTNO")]

                if not empno or not empname or not mobileno or not deptno:
                    flash(f"Missing data in row {index + 1}", "danger")
                    continue

                # Create the Employee record
                new_employee = EmployeeInfo(
                    EMPNO=empno,
                    EMPNAME=empname,
                    MobileNo=mobileno,
                    DEPTNO=deptno,
                    CreatedBy='admin',  # Set user if needed
                    UpdatedBy='admin',  # Set user if needed
                    CreatedTime=datetime.now(),
                    UpdatedTime=datetime.now()
                )

                try:
                    db.session.add(new_employee)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error adding employee {empname}: {str(e)}", "danger")

            flash("Employees imported successfully!", "success")
            return jsonify({"success": True})

        except Exception as e:
            flash(f"Error processing file: {str(e)}", "danger")
            return jsonify({"success": False})

    @app.route("/import_employees")
    def show_import_form():
        return render_template("import_employees.html")

# Run the application
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
