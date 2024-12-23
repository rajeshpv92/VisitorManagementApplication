from functools import wraps
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Blueprint
from datetime import datetime
import logging
from sqlalchemy import func

from numpy import append
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
from twilio.rest import Client
from flask_mail import Message, Mail

# Initialize the Mail object globally
mail = Mail()


# Define the Blueprint
view_reports = Blueprint('view_reports', __name__, url_prefix='/view_reports')
    
# Define a route for the main /view_reports page
@view_reports.route('/')
def view_reports_home():
    return render_template('view_reports.html')

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

    # Add email configuration in your app
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'moonlights1321@gmail.com'
    app.config['MAIL_PASSWORD'] = 'kjibhyzsznlbjyps'
    app.config['MAIL_DEFAULT_SENDER'] = 'moonlights1321@gmail.com'
     # Bind Mail to the app
    mail.init_app(app)
    
    # Initialize database
    db.init_app(app)

    # Setup logging
    setup_logging(app)

    # Register routes
    register_routes(app)

    # Load configuration from config.py
    app.config.from_object(Config)

    app.register_blueprint(view_reports)

    with app.app_context():
        db.create_all()  # Ensure tables are created

    

    return app
# Twilio Configuration
TWILIO_PHONE_NUMBER = "+12185027429"
TWILIO_ACCOUNT_SID = "AC5c5089546c5959a3ebb5bb32daae691a"
TWILIO_AUTH_TOKEN = "751d764d457ed71d9dd2bf8647368a0b"

# Initialize Twilio Client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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
        if request.method == "POST":
            name = request.form.get("name")
            contact = request.form.get("contact")
            empno = request.form.get("empno")  # Employee number selected from dropdown
            purpose = request.form.get("purpose")
            address = request.form.get("address")
            photo = request.files.get("photo")
            visitdate = request.form.get("visit_date")
            visit_end_date = request.form.get("visit_end_date")
            created_by = updated_by = session.get("username")

            # Fetch employee email based on the selected empno
            employee = EmployeeInfo.query.filter_by(EMPNO=empno).first()
            if not employee:
                flash("Employee not found.", "danger")
                return redirect(url_for("create_visitor"))

             # Save photo to the upload folder
            photo_path = None
            if photo:
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                # Save relative path for database
                photo_path = f'static/uploads/{filename}'

            employee_email = employee.email  # Assuming EMAIL is a column in EmployeeInfo

            # Save visitor to database
            try:
                new_visitor = VisitorInfo(
                    Name=name,
                    ContactNumber=contact,
                    Purpose=purpose,
                    empno=empno,
                    email=employee_email,
                    visit_date=visitdate,
                    visit_end_date=visit_end_date,
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

                # Send email to the employee
                send_email_to_employee(employee_email, name, purpose, visitdate)

                flash(f"Visitor {name} added successfully!", "success")
                return redirect(url_for("create_visitor"))

            except Exception as e:
                db.session.rollback()
                flash(f"Error adding visitor: {str(e)}", "danger")
                return redirect(url_for("create_visitor"))

        employees = EmployeeInfo.query.all()
        return render_template("create_visitor.html", employees=employees)


    def send_email_to_employee(email, visitor_name, purpose, visit_date):
        """
        Sends an email notification to the employee about the visitor.
        """
        try:
            subject = f"New Visitor: {visitor_name}"
            body = f"""
            Dear Employee,

            You have a new visitor.

            Visitor Name: {visitor_name}
            Purpose: {purpose}
            Visit Date: {visit_date}

            Please attend to them promptly.

            Regards,
            Visitor Management System
            """

            # Using Flask-Mail
            msg = Message(subject, recipients=[email])
            msg.body = body
            mail.send(msg) 
            print(f"Email sent to {email}")

        except Exception as e:
            print(f"Error sending email: {e}")
            # Log the error or flash a message
            logging.error(f"Email sending failed: {e}")
            raise




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
            email = request.form.get("email")
            mobileno = request.form.get("mobileno")
            deptno = request.form.get("Deptno")  # Ensure you are getting the Deptno value
            created_by = updated_by = session.get("username")

            # Validation: check if all required fields are provided
            if not empno or not empname or not mobileno or not deptno or not email:
                flash("All fields are required.", "danger")
                return redirect(url_for("create_employee"))

            try:
                # Create a new EmployeeInfo object to add to the database
                new_employee = EmployeeInfo(
                    EMPNO=empno,
                    EMPNAME=empname,
                    MobileNo=mobileno,
                    email=email,
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
        
    @app.route("/edit_employee/<string:userid>", methods=["GET", "POST"])
    def edit_employee(userid):
        # Fetch the employee by ID
        employee = EmployeeInfo.query.filter_by(ID=userid).first()
        if not employee:
            flash("Employee not found.", "danger")
            return redirect(url_for("view_employees"))

        # Fetch all departments for the dropdown
        departments = DepartmentInfo.query.all()

        if request.method == "POST":
            try:
                # Get form data
                empno = request.form.get("empno")
                empname = request.form.get("empname")
                email = request.form.get("email")
                mobileno = request.form.get("mobileno")
                deptno = request.form.get("Deptno")
                updated_by = session.get("username")

                # Validate mandatory fields
                if not empname:
                    flash("Employee name is required.", "danger")
                    return redirect(url_for("edit_employee", userid=userid))

                # Update the employee record
                employee.EMPNO = empno
                employee.EMPNAME = empname
                employee.MobileNo = mobileno
                employee.email = email
                employee.DEPTNO = deptno
                employee.UpdatedBy = updated_by
                employee.UpdatedTime = datetime.now()

                
                db.session.commit()
                flash(f"Employee {empname} updated successfully.", "success")
                return redirect(url_for("view_employees"))

            except Exception as e:
                db.session.rollback()
                flash(f"Error updating employee: {str(e)}", "danger")

        return render_template("edit_employee.html", employee=employee, departments=departments)


    @app.route("/delete_employee/<string:userid>", methods=["GET", "POST"])
    def delete_employee(userid):

        employee = EmployeeInfo.query.filter_by(ID=userid).first()
        if not employee:
            flash("employee not found.", "danger")
            return redirect(url_for("view_employees"))

        try:
            db.session.delete(employee)
            db.session.commit()
            flash(f"visitor {employee.EMPNAME} deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting user: {str(e)}", "danger")

        return redirect(url_for("view_employees"))

    @app.route("/import_employees", methods=["GET", "POST"])
    def import_employees():

        file = request.files.get('file')  # Get the file from the form
        mappings = request.form.get('mappings')  # Get mappings from the form (if applicable)

        if request.method == "GET":
            return render_template("import_employees.html")

            file = request.files.get('file')
            mappings = request.form.get('mappings')

        if not file or not mappings:
            flash("Invalid file or column mappings.", "danger")
            return redirect(url_for("import_employees"))

        try:
            mappings = json.loads(mappings)
        except json.JSONDecodeError:
            flash("Invalid column mappings format.", "danger")
            return redirect(url_for("import_employees"))

        # Save file temporarily
        filename = secure_filename(file.filename)
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        file.save(file_path)

        # Read the Excel file using pandas
        try:
            data = pd.read_excel(file_path)
        except Exception as e:
            flash(f"Error reading Excel file: {str(e)}", "danger")
            return redirect(url_for("import_employees"))

        # Process rows
        row_count = 0
        errors = []

        for index, row in data.iterrows():
            try:
                empno = int(row[mappings.get("EMPNO")])
                empname = row[mappings.get("EMPNAME")]
                mobileno = int(row[mappings.get("MobileNo")])
                email = row[mappings.get("email")]
                deptno = row[mappings.get("DEPTNO")]

                
                if not all([empno, empname, mobileno, deptno, email]):
                    errors.append(f"Missing data in row {index + 1}")
                    continue

                # Create the Employee record
                new_employee = EmployeeInfo(
                    EMPNO=empno,
                    EMPNAME=empname,
                    MobileNo=mobileno,
                    email=email,
                    DEPTNO=deptno,
                    CreatedBy='admin',  # Replace with the logged-in user
                    UpdatedBy='admin',  # Replace with the logged-in user
                    CreatedTime=datetime.now(),
                    UpdatedTime=datetime.now()
                )

                db.session.add(new_employee)
                row_count += 1

            except (ValueError, TypeError):
                db.session.rollback()
                errors.append(f"Invalid dataype in row {index + 1}: {str(e)}")

        try:
            db.session.commit()
            return jsonify({"success": True, "message": "Employees imported successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            print("Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

        # Cleanup temporary file
        os.remove(file_path)

        # Display errors if any
        if errors:
            for error in errors:
                flash(error, "danger")

        return redirect(url_for("import_employees"))


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


    @view_reports.route('/api/visitors/daily', methods=['GET'])
    def daily_visitors():
        # Connect to the database
        conn = db.engine.connect()

        # Query to get daily visitor statistics
        query = """
            SELECT 
                CONVERT(DATE, visit_date) AS VisitDate, 
                COUNT(*) AS VisitorCount
            FROM 
                Visitor
            WHERE 
                CONVERT(DATE, visit_date) >= DATEADD(DAY, -30, GETDATE())  -- Last 30 days
            GROUP BY 
                CONVERT(DATE, visit_date)
            ORDER BY 
                VisitDate;
        """
        data = pd.read_sql(query, conn)

        # Query to get detailed visitor data (visitor names, times, etc.)
        detailed_query = """
            SELECT empno, Name, ContactNumber, Purpose, visit_date
            FROM Visitor where CAST(visit_date AS DATE)=CAST(GETDATE() AS DATE)
            ORDER BY CreatedTime;

        """
        visitor_details = pd.read_sql(detailed_query, conn)

        conn.close()

        # Convert data to lists for passing to the template
        date_data = data['VisitDate'].tolist()  # Dates for x-axis
        visitor_data = data['VisitorCount'].tolist()  # Counts for y-axis
        visitor_list = visitor_details[['empno', 'Name', 'ContactNumber', 'Purpose', 'visit_date']].to_dict(orient='records')  # List of visitors

        # Render the template with the data
        return render_template('daily_visitors.html', dates=date_data, visitors=visitor_data, visitor_list=visitor_list)

    @view_reports.route('/api/visitors/monthly', methods=['GET'])
    def monthly_visitors():
        conn = db.engine.connect()
        query = """
            SELECT FORMAT(visit_date, 'yyyy-MM') AS VisitMonth, COUNT(*) AS VisitorCount
            FROM Visitor 
            GROUP BY FORMAT(visit_date, 'yyyy-MM')
            ORDER BY VisitMonth
        """
        data = pd.read_sql(query, conn)

        # Query to get detailed visitor data (visitor names, times, etc.)
        detailed_query = """
            SELECT empno, Name, ContactNumber, Purpose, visit_date
            FROM Visitor where FORMAT(visit_date, 'yyyy-MM')=FORMAT(GETDATE(), 'yyyy-MM')
            ORDER BY CreatedTime;

        """
        visitor_details = pd.read_sql(detailed_query, conn)
        conn.close()
        # Convert data to a list of dicts for easy access in the template
        date_data = data['VisitMonth'].tolist()  # Dates for x-axis
        visitor_data = data['VisitorCount'].tolist()  # Counts for y-axis
        visitor_list = visitor_details[['empno', 'Name', 'ContactNumber', 'Purpose', 'visit_date']].to_dict(orient='records')  # List of visitors

        return render_template('monthly_visitors.html', dates=date_data, visitors=visitor_data, visitor_list=visitor_list)
        #return jsonify(data.to_dict(orient='records'))

    @view_reports.route('/api/visitors/yearly', methods=['GET'])
    def yearly_visitors():
        conn = db.engine.connect()
        query = """
            SELECT FORMAT(visit_date, 'yyyy') AS VisitYear, COUNT(*) AS VisitorCount
            FROM Visitor
            GROUP BY FORMAT(visit_date, 'yyyy')
            ORDER BY VisitYear;
        """
        data = pd.read_sql(query, conn)

        # Query to get detailed visitor data (visitor names, times, etc.)
        detailed_query = """
            SELECT empno, Name, ContactNumber, Purpose, visit_date
            FROM Visitor
            WHERE YEAR(visit_date) = YEAR(GETDATE())
            ORDER BY CreatedTime;

        """
        visitor_details = pd.read_sql(detailed_query, conn)
        conn.close()
        # Convert data to a list of dicts for easy access in the template
        date_data = data['VisitYear'].tolist()  # Dates for x-axis
        visitor_data = data['VisitorCount'].tolist()  # Counts for y-axis
        visitor_list = visitor_details[['empno', 'Name', 'ContactNumber', 'Purpose', 'visit_date']].to_dict(orient='records')  # List of visitors

        return render_template('yearly_visitors.html', dates=date_data, visitors=visitor_data, visitor_list=visitor_list)
        #return jsonify(data.to_dict(orient='records'))

    @view_reports.route('/api/visitors/department', methods=['GET'])
    def department_visitors():
        conn = db.engine.connect()
        query = """
            SELECT D.dname AS Department, COUNT(*) AS VisitorCount
            FROM Visitor V
            JOIN Employee E ON V.empno = E.empno  
            JOIN DEPT D ON E.deptno = D.deptno   
            GROUP BY D.dname                     
            ORDER BY VisitorCount DESC;          
        """
        data = pd.read_sql(query, conn)
        conn.close()
        return jsonify(data.to_dict(orient='records'))

    @view_reports.route('/api/visitors/employee', methods=['GET'])
    def employee_visitors():
        conn = db.engine.connect()
        query = """
            SELECT E.EMPNAME AS EmployeeName, COUNT(*) AS VisitorCount
            FROM Visitor V
            JOIN Employee E ON V.empno = E.empno   
            GROUP BY E.EMPNAME                       
            ORDER BY VisitorCount DESC;            

        """
        data = pd.read_sql(query, conn)
        conn.close()
        return jsonify(data.to_dict(orient='records'))

    @app.route('/get_filter_options', methods=['GET'])
    def get_filter_options():
        try:
            # Fetch unique visitor names from the database
            visitors = VisitorInfo.query.with_entities(VisitorInfo.Name).distinct().all()

            # Convert the result to a plain list of visitor names
            visitor_names = [visitor[0] for visitor in visitors]

            # Return visitor names as a JSON response
            return jsonify({
                "visitors": visitor_names
            })

        except Exception as e:
            print(f"Error fetching filter options: {e}")
            return jsonify({"error": "An error occurred while fetching filter options."}), 500
    
    from flask import Flask, request, jsonify



    @app.route('/preview_records', methods=['POST'])
    def preview_records():
        try:
            data = request.get_json()
            visitor_name = data.get('visitorName')
            visit_date = data.get('visitDate')
            visit_end_date = data.get('visitendDate')
            # Validate inputs
            if not visitor_name or not visit_date:
                return jsonify({"error": "Visitor Name and Visit Date are required"}), 400

            # If only date is passed, set the default time (e.g., '00:00:00')
            if len(visit_date) == 10:  # 'YYYY-MM-DD' format (date only)
                visit_date += " 00:00:00"  # Default time to midnight

            if len(visit_end_date) == 10:  # 'YYYY-MM-DD' format (date only)
                visit_end_date += " 00:00:00"  # Default time to midnight

            # Convert visit_date string to datetime object
            visit_date = datetime.strptime(visit_date, "%Y-%m-%d %H:%M:%S")
            visit_end_date = datetime.strptime(visit_end_date, "%Y-%m-%d %H:%M:%S")

            # Query database for matching records (case-insensitive for name)
            records = VisitorInfo.query.filter(
                VisitorInfo.Name.ilike(f"%{visitor_name}%"),  # Use `ilike` for case-insensitive search
                VisitorInfo.visit_date >= visit_date,
                VisitorInfo.visit_end_date <= visit_end_date
                #VisitorInfo.employee.EMPNAME
            ).all()

            try:
            # Convert records to a list of dictionaries
                results = [
                    {
                        "empno": record.empno,
                        "name": record.Name,
                        "phone": record.ContactNumber,
                        "purpose": record.Purpose,
                        "visit_date": record.visit_date,
                        "visit_end_date": record.visit_end_date,
                        "employee": record.employee.EMPNAME, 
                    }
                    for record in records
                ]
            except Exception as e:
                print(f"Error: {e}")  # Debugging exception details
                return jsonify({"report": records.Name})

            # Return results
            return jsonify({"preview": results}), 200

        except Exception as e:
            print(f"Error: {e}")  # Debugging exception details
            return jsonify({"error": "Internal Server Error"}), 500
            

    from datetime import datetime

    # @app.route('/generate_report', methods=['POST'])
    # def generate_report():
    #     try:
    #         # Log the incoming request body for debugging
    #         print(f"Received request: {request.data}")

    #         # Parse JSON data from the request body
    #         filters = request.get_json()

    #         # Validate that the request body is valid JSON
    #         if not filters:
    #             return jsonify({"error": "Invalid or empty JSON body provided."}), 400

    #         # Extract filter values
    #         visitor_name = filters.get('visitorName', '')
    #         visit_date = filters.get('visitDate', '')

    #         # If only date is passed, add default time '00:00:00'
    #         if len(visit_date) == 10:  # 'YYYY-MM-DD' format (date only)
    #             visit_date += " 00:00:00"  # Add midnight as default time

    #         # Convert visit_date string to datetime object (including default time)
    #         try:
    #             visit_date = datetime.strptime(visit_date, "%Y-%m-%d %H:%M:%S")
    #         except ValueError:
    #             return jsonify({"error": "Invalid date format. Expected 'YYYY-MM-DD'."}), 400

    #         print(f"Visitor Name: {visitor_name}, Visit Date: {visit_date}")

    #         # Fetch visitor data from the database using db.session.query
    #         visitor_data = db.session.query(
    #             VisitorInfo.Name,
    #             VisitorInfo.visit_date,
    #             VisitorInfo.email,
    #             VisitorInfo.Purpose,
    #             VisitorInfo.ContactNumber,
    #             VisitorInfo.empno
    #         ).all()

    #         # Convert the query result to a list of dictionaries for easier filtering
    #         visitor_data_list = [
    #             {
    #                 "name": entry.Name,
    #                 "visit_date": entry.visit_date,
    #                 "email": entry.email,
    #                 "purpose": entry.Purpose,
    #                 "contact_number": entry.ContactNumber,
    #                 "empno": entry.empno,
    #             }
    #             for entry in visitor_data
    #         ]

    #         # Apply filters - compare visit_date with the time included
    #         filtered_data = [
    #             entry for entry in visitor_data_list if
    #             (not visitor_name or visitor_name.lower() in entry['name'].lower()) and
    #             (not visit_date or visit_date <= entry['visit_date'])  # Compare datetime objects
    #         ]

    #         # Return the filtered report data
    #         return jsonify({"report": filtered_data})

    #     except Exception as e:
    #         # Log the full exception details
    #         print(f"Error generating report: {str(e)}")
    #         return jsonify({"error": f"An error occurred while generating the report: {str(e)}"}), 500
    
        
        # Function to validate international phone number format
    def is_valid_phone_number(phone_number):
        # Regular expression to check if the phone number starts with '+' and contains digits
        # and ensures a valid length (at least 10 digits + country code)
        pattern = r'^\+?[1-9]\d{1,14}$'  # Matches phone numbers starting with '+' followed by digits
        return re.match(pattern, phone_number) is not None

    # Endpoint to display the form for the employee
    @app.route('/web_request', methods=['GET', 'POST'])
    def web_request():
        if request.method == 'POST':
            # Get form data (visitor phone number and comments)
            visitor_phone = request.form.get('visitor_phone')  # Visitor's phone number
            additional_comments = request.form.get('comments')  # Additional comments from the employee

            # Validate phone number format (you can enhance this part with more validation)
            if not is_valid_phone_number(visitor_phone):
                flash("Invalid phone number. Please enter a valid phone number with country code.", "danger")
                return redirect(url_for('web_request'))

            # Generate the registration link for the visitor (this will be the form link)
            visitor_link = url_for('visitor_reg_form', _external=True)  # This is the registration page link
        
            # SMS body that will be sent to the visitor
            sms_body = f"Hello, you have a visitor registration. Please fill out the form here: {visitor_link}"
            if additional_comments:
                sms_body += f"\nAdditional Comments: {additional_comments}"

            # Send SMS to visitor using Twilio
            try:
                message = client.messages.create(
                    body=sms_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=visitor_phone
                )
                flash("Visitor registration link sent successfully!", "success")
            except Exception as e:
                flash(f"Error sending SMS: {str(e)}", "danger")
                return redirect(url_for('web_request'))

            return redirect(url_for('web_request'))

        # Render the form for the employee
        return render_template('web_request.html')

    # Endpoint for the visitor to fill out the registration form
    @app.route('/visitor_reg_form', methods=['GET', 'POST'])
    def visitor_reg_form():
        if request.method == 'POST':
            # Get form data from visitor (name, contact, etc.)
            name = request.form.get('name')
            contact = request.form.get('contact')
            purpose = request.form.get('purpose')
            visit_date = request.form.get('visit_date')
            visit_end_date = request.form.get('visit_end_date')

            # Save visitor information to the database (add database logic as required)
            # Example: Save to a VisitorInfo model (this is a placeholder)
            new_visitor = {
                "name": name,
                "contact": contact,
                "purpose": purpose,
                "visit_date": visit_date,
                "visit_end_date": visit_end_date,
                "created_at": datetime.now(),
            }

            # Simulate saving to the database
            print(f"Visitor data saved: {new_visitor}")

            flash("Visitor registration submitted successfully!", "success")
            return redirect(url_for('visitor_reg_form'))

        # Render the visitor registration form
        return render_template('visitor_reg_form.html')

# Run the application
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
