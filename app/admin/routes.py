from flask import Blueprint,url_for,render_template,redirect,flash,get_flashed_messages,request,session
from app.models import Authentication,Objective,DepartmentHead,Employee,Review,ObjectiveBatch
from app import db
from sqlalchemy.exc import IntegrityError
from app.utils import login_required,admin_required

admin_bp = Blueprint("admin",__name__,url_prefix="/admin")

@admin_bp.route("/",methods=["GET"])
@login_required
@admin_required
def home():
    return render_template("home.html",state="admin",role="admin")

@admin_bp.route("/logout",methods=["POST","GET"])
@login_required
@admin_required
def logout():
    if request.method == "POST":
        session.pop("role",None)
        session.pop("user_id",None)
        return redirect(url_for("base.login"))
    return render_template("logout.html",state="admin",role="admin")

@admin_bp.route("/delete_account",methods=["POST","GET"])
@login_required
@admin_required
def delete_account():
    if request.method == "POST":
        user_id = session.get("user_id")
        user = Authentication.query.filter_by(id=user_id).first()
        session.pop("role",None)
        session.pop("user_id",None)
        db.session.delete(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash("username does not exist","error")
            db.session.rollback()
            return redirect(url_for("base.signup"))
        flash("account deleted succesfully","success")
        return redirect(url_for("base.login"))
    return render_template("delete_account.html",state="admin",role="admin")

@admin_bp.route("/add_objectives", methods=["POST", "GET"])
@login_required
@admin_required
def add_objective():
    admin_email = session.get("email")
    department_head = Authentication.query.filter_by(email=admin_email).first().department_head
    if request.method == "POST":
        title = request.form.get("title")
        year = request.form.get("year")

        objectives = request.form.getlist("objectives[]")
        categories = request.form.getlist("categories[]")
        weights = request.form.getlist("weights[]")
        score_ranges = request.form.getlist("score_ranges[]")
        assigned_tos = request.form.getlist("assigned_tos[]")

        # ✅ CREATE ONE BATCH
        batch = ObjectiveBatch(
            title=title,
            year=year,
            assigned_by=department_head
        )
        db.session.add(batch)
        db.session.flush()  # get batch.id

        for obj, cat, weight, score_range in zip(
            objectives, categories, weights, score_ranges
        ):
            for emp_name in assigned_tos:
                emp_auth = Authentication.query.filter_by(
                    name=emp_name
                ).first()

                objective = Objective(
                    objective=obj,
                    category=cat,
                    year=year,
                    weight=weight,
                    score_range=score_range,
                    assigned_to=emp_auth.employee,
                    assigned_by=department_head,
                    batch=batch
                )

                db.session.add(objective)

        db.session.commit()
        flash("Objectives created successfully", "success")
        return redirect(url_for("admin.objectives"))

    department = department_head.department
    employees = department.employees

    employee_names = [emp.authentication.name for emp in employees]

    return render_template(
        "add_objective.html",
        role="admin",
        state="admin",
        employee_names=employee_names
    )


from collections import defaultdict

@admin_bp.route("/objectives")
@login_required
@admin_required
def objectives():
    auth = Authentication.query.get(session["user_id"])
    grouped = defaultdict(list)

    for obj in auth.department_head.objectives:
        key = (obj.batch.title, obj.assigned_to_id)

        grouped[key].append(obj)

    return render_template(
        "objectives.html",
        grouped_objectives=grouped,
        role="admin",
        state="admin"
    )

# REVIEW OBJECTIVE
@admin_bp.route("/review/<int:objective_id>", methods=["POST", "GET"])
@login_required
@admin_required
def review_objective(objective_id):
    objective = Objective.query.get_or_404(objective_id)
    if request.method == "POST":
        review_text = request.form.get("review")
        score_raw = request.form.get("score")
        if not all([review_text, score_raw]):
            flash("Both Review and Score are needed", "error")
            return redirect(request.url)
        try:
            score = int(score_raw)
        except ValueError:
            flash("Score must be a number", "error")
            return redirect(request.url)
        weighted_score = (score * objective.weight) / objective.score_range
        r = Review(
            review=review_text,
            score=score,
            weighted_score=weighted_score
        )
        objective.reviews = r
        db.session.commit()
        return redirect(url_for("admin.objective_overview", objective_id=objective.id))
    return render_template("review.html", objective=objective, role="admin", state="admin")


@admin_bp.route("/objective_overview/<int:objective_id>")
@login_required
@admin_required
def objective_overview(objective_id):
    # Get the objective
    objective = Objective.query.get_or_404(objective_id)
    
    # Get batch and employee
    batch = objective.batch
    employee = objective.assigned_to

    # Get all objectives for this batch and employee
    objectives = Objective.query.filter_by(batch_id=batch.id, assigned_to_id=employee.id).all()

    # Precompute total weighted score safely
    total_weighted = 0
    for obj in objectives:
        if obj.reviews:  # ensure there is a review
            total_weighted += obj.reviews.weighted_score

    return render_template("objective_overview.html",batch=batch,employee=employee,objectives=objectives,total_weighted=total_weighted,role="admin",state="admin")


# DELETE OBJECTIVE
@admin_bp.route("/delete_objective/<int:objective_id>", methods=["POST", "GET"])
@login_required
@admin_required
def delete_objective(objective_id):
    objective = Objective.query.get_or_404(objective_id)
    if request.method == "POST":
        db.session.delete(objective)
        db.session.commit()
        flash(f"Objective '{objective.objective}' deleted successfully", "success")
        return redirect(url_for("admin.objectives"))
    return render_template("delete_objective.html", objective=objective, role="admin", state="admin")
