from flask import Blueprint,render_template,request,url_for,redirect,session,flash,get_flashed_messages
from app.utils import login_required,employee_required
from app.models import Authentication,Objective,DepartmentHead,Employee,Feedback
from app import db
from sqlalchemy.exc import IntegrityError

employee_bp = Blueprint("employee",__name__,url_prefix="/employee")

@employee_bp.route("/")
@login_required
@employee_required
def home():
    return render_template("home.html",state="employee",role="employee")

@employee_bp.route("/logout",methods=["POST","GET"])
@login_required
@employee_required
def logout():
    if request.method == "POST":
        session.pop("role",None)
        session.pop("user_id",None)
        session.pop("email",None)
        return redirect(url_for("base.login"))
    return render_template("logout.html",state="employee",role="employee")

@employee_bp.route("/delete_account",methods=["POST","GET"])
@login_required
@employee_required
def delete_account():
    if request.method == "POST":
        user_id = session.get("user_id")
        user = Authentication.query.filter_by(id=user_id).first()
        session.pop("role",None)
        session.pop("user_id",None)
        session.pop("email",None)
        db.session.delete(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash("username does not exist","error")
            db.session.rollback()
            return redirect(url_for("base.signup"))
        session.clear()
        flash("account deleted succesfully","success")
        return redirect(url_for("base.login"))
    return render_template("delete_account.html",state="employee",role="employee")

from collections import defaultdict

@employee_bp.route("/objectives")
@login_required
@employee_required
def objectives():
    auth = Authentication.query.get(session["user_id"])
    grouped = defaultdict(list)

    for obj in auth.employee.objectives:
        key = (obj.batch.title, obj.batch.id)
        grouped[key].append(obj)

    return render_template(
        "objectives.html",
        grouped_objectives=grouped,
        role="employee",
        state="employee"
    )

@employee_bp.route("/feedback/<int:objective_id>", methods=["GET", "POST"])
@login_required
@employee_required
def feedback(objective_id):
    objective = Objective.query.get_or_404(objective_id)

    # Security check
    if objective.assigned_to.authentication.id != session["user_id"]:
        flash("Unauthorized", "error")
        return redirect(url_for("employee.objectives"))

    if request.method == "POST":
        feedback_text = request.form.get("feedback")

        if not feedback_text:
            flash("Feedback is required", "error")
            return redirect(request.url)

        fb = Feedback(feedback=feedback_text)
        objective.reviews.feedbacks = fb

        db.session.add(fb)
        db.session.commit()

        return redirect(
            url_for("employee.objective_overview", objective_id=objective.id)
        )

    return render_template(
        "feedback.html",
        objective=objective,
        role="employee",
        state="employee"
    )

@employee_bp.route("/objective_overview/<int:objective_id>")
@login_required
@employee_required
def objective_overview(objective_id):
    objective = Objective.query.get_or_404(objective_id)

    batch = objective.batch
    employee = objective.assigned_to

    # SECURITY CHECK
    if employee.authentication.id != session["user_id"]:
        flash("Unauthorized access", "error")
        return redirect(url_for("employee.objectives"))

    objectives = Objective.query.filter_by(
        batch_id=batch.id,
        assigned_to_id=employee.id
    ).all()
    total_weighted = 0
    for obj in objectives:
        if obj.reviews:  # ensure there is a review
            total_weighted += obj.reviews.weighted_score

    return render_template(
        "objective_overview.html",
        batch=batch,
        employee=employee,
        objectives=objectives,
        total_weighted=total_weighted,
        role="employee",
        state="employee"
    )
