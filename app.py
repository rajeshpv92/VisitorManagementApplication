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
from models.role import RoleInfo
import pandas as pd
from werkzeug.utils import secure_filename
import os
from config import Config  # Import your config class
import bcrypt
import re
from utils import hash_password  # Now import from your utils.py

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

    # Load configuration from config.py
    app.config.from_object(Config)

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
            if user and bcrypt.checkpw(password.encode('utf-8'), user.Password.encode('utf-8')):
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
            fname = request.form.get("fname")
            lname = request.form.get("lname")
            dialling_code = request.form.get("dialling_code")
            userid = request.form.get("userid")
            password = request.form.get("password")
            email = request.form.get("email")
            phone = request.form.get("phone")

            if not all([fname, userid, password]):
                flash("All fields are required.", "danger")
                return redirect(url_for("create_user"))

            # Password validation regex
            #password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$"
            if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$", password):
                flash("Password must be 8-16 characters long, include at least one letter, one number, and one special character.", "danger")
                return redirect(url_for("dashboard"))

            # Email format validation using a regex pattern
            if email is None or not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
                flash("Invalid email format.", "danger")
                return redirect(url_for("create_user"))

            # Phone number format validation (basic validation for example)
            if phone is None or not re.match(r"^\+?\d{1,4}[\s-]?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,4}$", phone):
                flash("Invalid phone number format.", "danger")
                return redirect(url_for("create_user"))

            # Check if user already exists (by userid or email)
            if UserInfo.query.filter_by(UserID=userid).first():
                flash("User {userid} already exists!", "danger")
                return redirect(url_for("create_user"))
            if UserInfo.query.filter_by(email=email).first():
                flash("Email {email} is already in use.", "danger")
                return redirect(url_for("create_user"))

            createdby = updatedby = session.get("username")

            try:

                # Hash the password using bcrypt
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                new_user = UserInfo(
                    firstname=fname,
                    lastname=lname,
                    email=email,
                    phone=phone,
                    countrycode=dialling_code,
                    UserID=userid,  # Updated to match the model
                    Password=hashed_password,
                    CreatedBy=createdby,
                    UpdatedBy=updatedby,
                    CreatedTime=datetime.now(),
                    UpdatedTime=datetime.now(),
                )

                db.session.add(new_user)
                db.session.commit()
                flash(f"User {userid} created successfully!", "success")
                return redirect(url_for("create_user"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating user: {str(e)}", "danger")
        return render_template("create_user.html")
    
    #Create View User definition.
    @app.route("/view_users", methods=["GET", "POST"])
    def view_users():
        try:
            # Pagination settings
            page = request.args.get('page', 1, type=int)  # Default to page 1 if no page is specified
            per_page = 5  # Set how many records you want to show per page

            # Fetch users with pagination
            users = UserInfo.query.order_by(UserInfo.CreatedBy).paginate(page=page, per_page=per_page, error_out=False) # False for not including query string for pagination

            # Log the paginated users for debugging
            app.logger.info("Users fetched from the database (paginated): %s", users.items)

            # Render the template with paginated data
            return render_template("view_users.html", users=users.items, pagination=users)

        except Exception as e:
            app.logger.error(f"Error querying Users: {e}")
            flash(f"An error occurred while fetching Users: {str(e)}", "danger")  # Display specific error message
            return redirect(url_for("dashboard"))

        users = UserInfo.query.all()

        return render_template("view_users.html", users=users)

    # Fetch roles here inside the route
        roles = RoleInfo.query.all()
        
        return render_template("view_users.html", roles=roles)


    @app.route("/edit_user/<string:userid>", methods=["GET", "POST"])
    @admin_required
    def edit_user(userid):
        user = UserInfo.query.filter_by(UserID=userid).first()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("view_users"))

        if request.method == "POST":
            role_id = request.form.get("role_id")
            fname = request.form.get("fname")
            lname = request.form.get("lname")
            email = request.form.get("email")
            phone = request.form.get("phone")

            if not fname:
                flash("Name is required.", "danger")
                return redirect(url_for("edit_user", userid=userid))

            try:
                user.firstname = fname
                user.lastname = lname
                user.email = email
                user.phone = phone
                user.Role_ID = role_id
                user.UpdatedBy = session.get("username")
                user.UpdatedTime = datetime.now()

                db.session.commit()
                flash(f"User {userid} updated successfully.", "success")
                return redirect(url_for("view_users"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating user: {str(e)}", "danger")

        return render_template("edit_user.html", user=user)


    @app.route("/delete_user/<string:userid>", methods=["GET", "POST"])
    @admin_required
    def delete_user(userid):
        user = UserInfo.query.filter_by(UserID=userid).first()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("view_users"))

        try:
            db.session.delete(user)
            db.session.commit()
            flash(f"User {userid} deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting user: {str(e)}", "danger")

        return redirect(url_for("view_users"))


    # Create Visitor definition.
    @app.route("/create_visitor", methods=["GET", "POST"])
    def create_visitor():

         # Initialize photo variable to None outside of the POST check
        photo = None

        if request.method == "POST":
            name = request.form.get("name")
            contact = request.form.get("contact")
            empno = request.form.get("empno")  # Ensure you are getting the empno value
            purpose = request.form.get("purpose")
            address = request.form.get("address")
            photo = request.files.get("photo")
            created_by = updated_by = session.get("username")

            # Debugging: print form data to see if it's being received correctly
            print("Form Data - Name:", name, "Contact:", contact, "Purpose:", purpose)

            # Validation: check if all required fields are provided
            if not name or not contact or not purpose:
                flash("All fields are required.", "danger")
                return redirect(url_for("dashboard"))

                 # Save photo to the upload folder
            photo_path = None
            if photo:
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                # Save relative path for database
                photo_path = f'static/uploads/{filename}'

                
                try:
                    # Create a new VisitorInfo object to add to the database
                    new_visitor = VisitorInfo(
                        Name=name,
                        ContactNumber=contact,
                        Purpose=purpose,
                        empno=empno,
                        Address=address,
                        photo=photo_path,  # Use the correct column name from the model
                        CreatedBy=created_by,
                        UpdatedBy=updated_by,
                        CreatedTime=datetime.now(),
                        UpdatedTime=datetime.now(),
                        CheckIn=datetime.now(),
                        CheckOut=None
                    )
                    db.session.add(new_visitor)
                    db.session.commit()
                    flash(f"Visitor {name} added successfully!", "success")
                    return redirect(url_for("create_visitor"))

                except Exception as e:
                    db.session.rollback()
                    flash(f"Error adding visitor: {str(e)}", "danger")
                    return redirect(url_for("dashboard"))
        
        # Fetch departments here inside the route
        employees = EmployeeInfo.query.all()

        return render_template("create_visitor.html", employees=employees)                       

    #Create View Visitor definition.
    @app.route("/view_visitors", methods=["GET", "POST"])
    def view_visitors():
        try:
            # Pagination settings
            page = request.args.get('page', 1, type=int)  # Default to page 1 if no page is specified
            per_page = 5  # Set how many records you want to show per page

            # Fetch users with pagination
            visitors_pag = VisitorInfo.query.order_by(VisitorInfo.CreatedTime).paginate(page=page, per_page=per_page, error_out=False)

            # Log the paginated users for debugging
            app.logger.info("Visitors fetched from the database (paginated): %s", visitors_pag.items)

            # Handle POST request for visitor checkout
            if request.method == "POST":
                visitor_id = request.form.get("ID")
                app.logger.info("Visitor ID from the form: %s", visitor_id)

                if visitor_id:
                    try:
                        # Fetch the specific visitor
                        visitor = VisitorInfo.query.get(visitor_id)
                        app.logger.info("Visitor object fetched: %s", visitor)

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

            # Render the template with paginated data
            return render_template("view_visitors.html", visitors=visitors_pag.items, pagination=visitors_pag)

        except Exception as e:
            app.logger.error(f"Error querying visitors: {e}")
            flash(f"An error occurred while fetching visitors: {str(e)}", "danger")  # Display specific error message
            return redirect(url_for("dashboard"))

    @app.route("/edit_visitor/<string:userid>", methods=["GET", "POST"])
    def edit_visitor(userid):
        visitor = VisitorInfo.query.filter_by(ID=userid).first()
        if not visitor:
            flash("Visitor not found.", "danger")
            return redirect(url_for("view_visitors"))
    
        # Get all employees from the Employee table
        employees = EmployeeInfo.query.all()

        if request.method == "POST":
            name = request.form.get("name")
            contact = request.form.get("contact")
            empno = request.form.get("empno")
            purpose = request.form.get("purpose")
            address = request.form.get("address")
        
            # Initialize 'photo' variable
            photo = request.files.get("photo")

            # Handle the photo upload if a new photo is provided
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                visitor.photo = filename  # Store the filename (not the FileStorage object)

            if not name:
                flash("Name is required.", "danger")
                return redirect(url_for("edit_visitor", userid=userid))

            try:
                # Update visitor details
                visitor.Name = name
                visitor.ContactNumber = contact
                visitor.empno = empno
                visitor.Purpose = purpose
                visitor.Address = address
                # The photo is already updated earlier if a new photo was uploaded
                visitor.UpdatedBy = session.get("username")
                visitor.UpdatedTime = datetime.now()

                db.session.commit()
                flash(f"Visitor {name} updated successfully.", "success")
                return redirect(url_for("view_visitors"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating visitor: {str(e)}", "danger")

        return render_template("edit_visitor.html", visitor=visitor, employees=employees)


    @app.route("/delete_visitor/<string:userid>", methods=["GET", "POST"])
    def delete_visitor(userid):

        visitor = VisitorInfo.query.filter_by(ID=userid).first()
        if not visitor:
            flash("visitor not found.", "danger")
            return redirect(url_for("view_visitors"))

        try:
            db.session.delete(visitor)
            db.session.commit()
            flash(f"visitor {visitor.Name} deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting user: {str(e)}", "danger")

        return redirect(url_for("view_visitors"))

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
        
        return render_template("create_employee.html", departments=departments)


    #Create View Employee definition.
    @app.route("/view_employee", methods=["GET", "POST"])
    def view_employees():
        try:
            # Pagination settings
            page = request.args.get('page', 1, type=int)  # Default to page 1 if no page is specified
            per_page = 5  # Set how many records you want to show per page

            # Fetch employees with pagination
            employees_pag = EmployeeInfo.query.order_by(EmployeeInfo.ID).paginate(page=page, per_page=per_page, error_out=False)

            app.logger.info("Employees fetched from the database (paginated): %s", employees_pag.items)  # Debugging info

            # Handle POST request for any form processing (if needed)
            if request.method == "POST":
                employees = EmployeeInfo.query.all()

            # Render the template with paginated data
            return render_template("view_employee.html", employees=employees_pag.items, pagination=employees_pag)

        except Exception as e:
            app.logger.error(f"Error querying employees: {e}")
            flash(f"An error occurred while fetching employees: {str(e)}", "danger")
            return redirect(url_for("dashboard"))
        
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

    @app.route("/visitor_id", methods=["GET", "POST"])
    def visitor_id():
        visitor = None  # Initialize visitor to None in case no data is passed

        if request.method == "POST":
            visitor_id = request.form.get("visitor_id")  # Get visitor_id from form
            app.logger.info(f"Visitor ID received: {visitor_id}")  # Log the ID for debugging

            if visitor_id:
                visitor = VisitorInfo.query.get(visitor_id)
                if visitor:
                    return render_template("visitor_id.html", visitor=visitor)  # Render ID card page
                else:
                    flash("Visitor not found.", "danger")
            else:
                flash("No visitor selected.", "danger")  # If no ID is provided
        else:
            flash("Invalid request method.", "danger")
            return redirect(url_for('view_visitors'))  # Redirect back to the visitor list page

        return render_template("visitor_id.html", visitor=visitor)  # Ensure visitor is passed here





# Run the application
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
