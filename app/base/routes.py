from flask import Blueprint,request,url_for,session,flash,get_flashed_messages,render_template,redirect
from app.models import Employee,Authentication,TeamLeader,Department,Administrator,EmployeeEmail
from app import db
from werkzeug.security import check_password_hash,generate_password_hash
from sqlalchemy.exc import IntegrityError
from app.utils import login_required
import os

base_bp = Blueprint("base",__name__)

@base_bp.route("/",methods=["POST","GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            flash("Username and password are required", "error")
            return redirect(url_for("base.login"))
        auth = Authentication.query.filter_by(email=email).first()
        if not auth:
            flash("account linked to this email does not exist","error")
            return redirect(url_for("base.login"))
        hashed_pw = auth.password
        if check_password_hash(hashed_pw,password):
            flash("login succesful","success")
            if auth.administrator:
                role = "admin"
            elif auth.team_leader:
                role = "team_leader"
            elif auth.employee:
                role = "employee"
            
            session.clear()
            session["user_id"] = auth.id
            session["role"] = role
            session["email"] = auth.email
            if role == "employee":
                return redirect(url_for("employee.home"))
            elif role == "team_leader":
                return redirect(url_for("team_leader.home"))
            elif role == "admin":
                return redirect(url_for("admin.home"))
        flash("invalid password","error")
        return redirect(url_for("base.login"))
    return render_template("login.html")

@base_bp.route("/admin_signup",methods=["POST","GET"])
def admin_signup():
    if request.method == "POST":
        departments = [
        "HCM", "SCM", "Procurement", "Finance",
        "Administration", "Business Development", "Technical"]
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        entry_code = os.getenv("ENTRY_CODE")

        
        if not all([username, password, email]):
            flash("All fields are required", "error")
            return redirect(url_for("base.admin_signup"))

        if not entry_code:
            flash("Server configuration error", "error")
            return redirect(url_for("base.admin_signup"))

        if entry_code != entry_code:
            flash("Incorrect entry code", "error")
            return redirect(url_for("base.admin_signup"))

        if Administrator.query.all():
            flash("Admin already registered", "error")
            return redirect(url_for("base.admin_signup"))
        hashed_pw = generate_password_hash(password)
        auth = Authentication(
            email=email,
            password=hashed_pw,
            name=username,
            role="admin"
        )
        administrator = Administrator(name=username)
        auth.administrator = administrator
        db.session.add(administrator)
        
        for dep_name in departments:
            dep = Department.query.filter_by(name=dep_name).first()
            if not dep:
                dep = Department(name=dep_name)
            administrator.departments.append(dep)
        db.session.commit()
        return redirect(url_for("base.login"))
    return render_template("admin_signup.html")


@base_bp.route("/signup", methods=["GET", "POST"])
def signup():
    departments = [
        "HCM", "SCM", "Procurement", "Finance",
        "Administration", "Business Development", "Technical"
    ]

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        entry_code = os.getenv("ENTRY_CODE")

        
        if not all([username, password, email]):
            flash("All fields are required", "error")
            return redirect(url_for("base.signup"))

        if not entry_code:
            flash("Server configuration error", "error")
            return redirect(url_for("base.signup"))

        if entry_code != entry_code:
            flash("Incorrect entry code", "error")
            return redirect(url_for("base.signup"))

        if Authentication.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for("base.signup"))

        employee_info = EmployeeEmail.query.filter_by(email=email).first()
        
        if not employee_info:
            flash("Email not authorized", "error")
            return redirect(request.url)

        role = employee_info.role
        hashed_pw = generate_password_hash(password)
        auth = Authentication(
            email=email,
            password=hashed_pw,
            name=username,
            role=role
        )

        
        if role == "admin":
            administrator = Administrator(name=username)
            auth.administrator = administrator
            db.session.add(administrator)

            for dep_name in departments:
                dep = Department.query.filter_by(name=dep_name).first()
                if not dep:
                    dep = Department(name=dep_name)
                administrator.departments.append(dep)

       
        elif role == "team_leader":
            department_name = employee_info.department
            department = Department.query.filter_by(name=department_name).first()
            if not department:
                print("yes")
                department = Department(name=department_name)
                db.session.add(department)

            if TeamLeader.query.filter_by(department_id=department.id).first():
                flash("This department already has a team leader", "error")
                return redirect(url_for("base.signup"))

            leader = TeamLeader(name=username, department=department)
            auth.team_leader = leader
            db.session.add(leader)

       
        elif role == "employee":
            department_name = employee_info.department
            department = Department.query.filter_by(name=department_name).first()
            print(47)
            if not department:
                department = Department(name=department_name)
                db.session.add(department)

            employee = Employee(name=username, department=department)
            auth.employee = employee
            db.session.add(employee)

        else:
            flash("Invalid role selected", "error")
            return redirect(url_for("base.signup"))

        db.session.add(auth)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Signup failed due to duplicate or invalid data", "error")
            return redirect(url_for("base.signup"))

        flash("Signup successful", "success")
        return redirect(url_for("base.login"))

    return render_template("signup.html", departments=departments)
