from flask import Blueprint,render_template,request,url_for,redirect,session,flash,get_flashed_messages,abort
from app.utils import login_required,employee_required
from app.models import Authentication,Objective,TeamLeader,Employee,Feedback,AdminObjective,AdminReviewFeedback,TeamLeaderFeedback
from app import db
from sqlalchemy.exc import IntegrityError
from collections import defaultdict

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
        user = Authentication.query.get(session["user_id"])
        session.clear()
        db.session.delete(user.employee)
        db.session.delete(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("there is a problem","error")
            return redirect(url_for("base.signup"))
        session.clear()
        flash("account deleted succesfully","success")
        return redirect(url_for("base.login"))
    return render_template("delete_account.html",state="employee",role="employee")

@employee_bp.route("/objectives")
@login_required
@employee_required
def objectives():
    auth = Authentication.query.get(session["user_id"])
    grouped = defaultdict(list)
    admin_grouped = defaultdict(list)

    for obj in auth.objectives:
        key = (obj.batch.title, obj.batch.id)
        grouped[key].append(obj)

    for admin_obj in auth.admin_objectives:
        key = (admin_obj.admin_batch.title, admin_obj.admin_batch.id)
        admin_grouped[key].append(admin_obj)

    return render_template(
        "employee_objectives.html",
        grouped_objectives=grouped,
        admin_grouped_objectives=admin_grouped,
        role="employee",
        state="employee"
    )

@employee_bp.route("/feedback/<int:objective_id>/<role>", methods=["GET", "POST"])
@login_required
@employee_required
def feedback(objective_id, role):
    if role == "admin":
        objective = AdminObjective.query.get(objective_id)
        review = objective.admin_review
        FeedbackModel = AdminReviewFeedback
        feedback_attr = "employee_feedback"

    elif role == "team_leader":
        objective = Objective.query.get(objective_id)
        review = objective.review
        FeedbackModel = Feedback
        feedback_attr = "feedback"

    else:
        abort(400)

    if request.method == "POST":
        feedback_text = request.form.get("feedback")

        if not feedback_text:
            flash("Feedback is required", "error")
            return redirect(request.url)

        if not review:
            abort(400)

        fb = FeedbackModel(feedback=feedback_text)
        db.session.add(fb)

        setattr(review, feedback_attr, fb)

        db.session.commit()

        return redirect(
            url_for(
                "employee.objective_overview",
                objective_id=objective.id,
                assigned_by_id=objective.assigned_by.id
            )
        )

    return render_template(
        "employee_feedback.html",
        objective=objective,
        role=role,
        state="employee",
        Title="Feedback"
    )

@employee_bp.route("/edit_feedback/<int:objective_id>/<role>", methods=["GET", "POST"])
@login_required
@employee_required
def edit_feedback(objective_id, role):

    objective = None
    review = None
    admin_review = None

  
    if role == "team_leader":
        objective = Objective.query.get(objective_id)

        if objective.assigned_to.id != session["user_id"]:
            flash("Unauthorized", "error")
            return redirect(url_for("employee.objectives"))

        review = objective.review
        if not review:
            flash("No review yet", "error")
            return redirect(url_for("employee.objectives"))

        feedback_text = (
            review.feedback.feedback
            if review.feedback
            else ""
        )

   
    elif role == "admin":
        objective = AdminObjective.query.get(objective_id)

        if objective.assigned_to.id != session["user_id"]:
            flash("Unauthorized", "error")
            return redirect(url_for("employee.objectives"))

        admin_review = objective.admin_review
        if not admin_review:
            flash("No review yet", "error")
            return redirect(url_for("employee.objectives"))

        feedback_text = (
            admin_review.employee_feedback.feedback
            if admin_review.employee_feedback
            else ""
        )

    else:
        abort(404)

  
    if request.method == "POST":
        feedback_text = request.form.get("feedback")

        if not feedback_text:
            flash("Feedback is required", "error")
            return redirect(request.url)

        if role == "admin":
            if not admin_review.employee_feedback:
                admin_review.employee_feedback = AdminReviewFeedback(
                    feedback=feedback_text
                )
            else:
                admin_review.employee_feedback.feedback = feedback_text

        elif role == "team_leader":
            if not review.feedback:
                review.feedback = Feedback(
                    feedback=feedback_text
                )
            else:
                review.feedback.feedback = feedback_text

        db.session.commit()

        return redirect(
            url_for("employee.objectives_overview", objective_id=objective.id)
        )

   
    return render_template(
        "employee_feedback.html",
        objective=objective,
        feedback=feedback_text,
        role="employee",
        state="employee",
        Title="Edit Feedback",
    )


@employee_bp.route("/objectives_overview/<int:objective_id>")
@login_required
@employee_required
def objectives_overview(objective_id):
    objective = Objective.query.get(objective_id)
    admin_objective = AdminObjective.query.get(objective_id)
    if objective:
        batch = objective.batch
        employee = objective.assigned_to
        if employee.id != session["user_id"]:
            flash("Unauthorized access", "error")
            return redirect(url_for("employee.objectives"))
        objectives = Objective.query.filter_by(batch_id=batch.id,assigned_to_id=employee.id).all()
        total_weighted = 0
        for obj in objectives:
            if obj.review: 
                total_weighted += obj.review.weighted_score
    elif admin_objective:
        batch = admin_objective.admin_batch
        employee = admin_objective.assigned_to
        if employee.id != session["user_id"]:
            flash("Unauthorized access", "error")
            return redirect(url_for("employee.objectives"))
        
        objectives = AdminObjective.query.filter_by(admin_batch_id=batch.id,assigned_to_id=employee.id).all()
        total_weighted = 0
        for obj in objectives:
            if obj.admin_review: 
                total_weighted += obj.admin_review.weighted_score


    return render_template(
        "employee_objectives_overview.html",
        batch=batch,
        employee=employee,
        objectives=objectives,
        total_weighted=total_weighted,
        role="employee",
        state="employee"
    )

@employee_bp.route("/objective_overview/<int:objective_id>/<int:assigned_by_id>",methods=["GET","HEAD"])
@login_required
@employee_required
def objective_overview(objective_id, assigned_by_id):
    print(1)
    assigned_by = Authentication.query.get(assigned_by_id)
    if hasattr(assigned_by, "objectives"):
        print(2)
        objective = Objective.query.get(objective_id)
        batch = objective.batch

    elif hasattr(assigned_by, "admin_objectives"):
        print(4)
        objective = AdminObjective.query.get(objective_id)
        batch = objective.admin_batch
        print(objective.admin_batch)

    title = batch.title
    year = batch.year
    employee = objective.assigned_to.name

    return render_template(
        "employee_objective_overview.html",
        year=year,
        title=title,
        employee=employee,
        role="employee",
        state="employee",
        objective=objective
    )
