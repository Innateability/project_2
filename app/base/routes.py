from flask import Blueprint,request,url_for,session,flash,get_flashed_messages,render_template,redirect
from app.models import Employee,Authentication,DepartmentHead,Department
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
            if auth.employee:
                role = "employee"
            else:
                role = "admin"
            session.clear()
            session["user_id"] = auth.id
            session["role"] = role
            session["email"] = auth.email
            if role == "employee":
                return redirect(url_for("employee.home"))
            else:
                return redirect(url_for("admin.home"))
        flash("invalid password","error")
        return redirect(url_for("base.login"))
    return render_template("login.html")

@base_bp.route("/signup",methods=["POST","GET"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        entered_entry_code = request.form.get("entry_code")
        entry_code = os.getenv("ENTRY_CODE")
        if not entered_entry_code == entry_code:
            flash("incorrect entry code","error")
            return redirect(request.url)
        department = request.form.get("department")
        is_admin = "role" in request.form
        if not all([username, password]):
            flash("Username and password are required", "error")
            return redirect(url_for("base.signup"))
        if is_admin:
            role = "admin"
            user = DepartmentHead(name=username)
            dpt = Department.query.filter_by(name=department).first()
            if not dpt:
                dept = Department(name=department)
                user.department = dept
            else:
                user.department = dpt
            hashed_pw = generate_password_hash(password)
            auth = Authentication(email=email,password=hashed_pw,name=username)
            auth.department_head = user
        else:
            role = "employee"
            user = Employee(name=username)
            dpt = Department.query.filter_by(name=department).first()
            if not dpt:
                dept = Department(name=department)
                user.department = dept
            else:
                user.department = dpt
            hashed_pw = generate_password_hash(password)
            auth = Authentication(email=email,password=hashed_pw,name=username)
            auth.employee = user
        db.session.add(auth)
        try:
            db.session.commit()
        except IntegrityError:
            flash("username already exists","error")
            db.session.rollback()
            return redirect(url_for("base.signup"))
        flash("signup succesful","success")
        return redirect(url_for("base.login"))
    return render_template("signup.html")
