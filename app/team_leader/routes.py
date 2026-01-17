from flask import Blueprint,url_for,render_template,redirect,flash,get_flashed_messages,request,session,abort
from app.models import Authentication,Objective,TeamLeader,Employee,Review,ObjectiveBatch,AdminObjective,Feedback,TeamLeaderFeedback,TeamLeaderFeedback
from app import db
from sqlalchemy.exc import IntegrityError
from app.utils import login_required,team_leader_required
from collections import defaultdict

team_leader_bp = Blueprint("team_leader",__name__,url_prefix="/Team-Leader")

@team_leader_bp.route("/",methods=["GET"])
@login_required
@team_leader_required
def home():
    return render_template("home.html",state="team_leader",role="team_leader")

@team_leader_bp.route("/logout",methods=["POST","GET"])
@login_required
@team_leader_required
def logout():
    if request.method == "POST":
        session.pop("role",None)
        session.pop("user_id",None)
        return redirect(url_for("base.login"))
    return render_template("logout.html",state="team_leader",role="team_leader")

@team_leader_bp.route("/delete_account",methods=["POST","GET"])
@login_required
@team_leader_required
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
    return render_template("delete_account.html",state="team_leader",role="team_leader")

@team_leader_bp.route("/add_recipients")
@login_required
@team_leader_required
def recipients():
    current_auth = Authentication.query.get(session["user_id"])
    current_employee = current_auth.team_leader
    department_id = current_employee.department_id
    names_auth = Authentication.query.join(Employee).filter(Employee.department_id == department_id,Authentication.id != current_auth.id).order_by(Authentication.name.asc()).all()
    print(names_auth)
    return render_template("team_leader_recipients.html",names_auth=names_auth)


@team_leader_bp.route("/add_objectives",methods=["POST","GET"])
@login_required
@team_leader_required
def add_objective():
    authen = Authentication.query.get(session["user_id"])
    team_leader = authen.team_leader if authen else None

    if request.method == "GET":
        
        recipient_ids = request.args.getlist("recipients[]")
        recipients = Authentication.query.filter(Authentication.id.in_(recipient_ids)).all()
        print("yes")
        print(recipients)
        return render_template("team_leader_add_objective.html", recipients=recipients)



    if request.method == "POST":
        recipient_ids = request.form.getlist("recipients[]")
        recipients = Authentication.query.filter(Authentication.id.in_(recipient_ids)).all()
        title = request.form.get("title")
        year = int(request.form.get("year"))
        print(recipients)
        objectives = request.form.getlist("objectives[]")
        categories = request.form.getlist("categories[]")
        weights = request.form.getlist("weights[]")
        score_ranges = request.form.getlist("score_ranges[]")

       

       
        batch = ObjectiveBatch(title=title, year=year)
        db.session.add(batch)
        db.session.flush()  # get batch.id

       
        for obj, cat, weight, score_range in zip(
            objectives, categories, weights, score_ranges
        ):
            for recipient in recipients:
                objective = Objective(
                    objective=obj,
                    category=cat,
                    weight=int(weight),
                    score_range=int(score_range),
                    assigned_to=recipient,         
                    assigned_by=team_leader,
                    batch=batch
                )
                db.session.add(objective)

        db.session.commit()
        flash("Objectives created successfully", "success")
        return redirect(url_for("team_leader.objectives"))

    # ================= GET REQUEST =================

    # employees = []

    # if administrator:
    #     for department in administrator.departments:
    #         for emp in department.employees:
    #             if emp.authentication:
    #                 employees.append(emp.authentication)

    # return render_template(
    #     "team_leader_add_objective.html",
    #     employees=employees,
    #     state="team_leader",)

@team_leader_bp.route("/edit_objectives/<int:objective_id>", methods=["POST", "GET"])
@login_required
@team_leader_required
def edit_objective(objective_id):
    team_leader_email = session.get("email")
    department_head = Authentication.query.filter_by(email=team_leader_email).first().team_leader
    obj = Objective.query.filter_by(id=objective_id).first()
    if obj.assigned_by != department_head:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title")
        year = int(request.form.get("year"))
        objective_text = request.form.get("objective")
        category = request.form.get("category")
        weight = int(request.form.get("weight"))
        score_range = int(request.form.get("score_range"))
        obj.batch.title = title
        obj.batch.year = year
        obj.objective = objective_text
        obj.category = category
        obj.weight = weight
        obj.score_range = score_range

        db.session.commit()
        flash(f"Objective {title} edited successfully", "success")
        return redirect(url_for("team_leader.objectives"))

    department = department_head.department
    employees = department.employees
    objective = Objective.query.filter_by(id=objective_id).first()
    employee_names = [emp.authentication.name for emp in employees]
    return render_template("team_leader_edit_objective.html",role="team_leader",state="team_leader",employee_names=employee_names,objective=objective,Title="EDIT OBJECTIVES")

@team_leader_bp.route("/objectives")
@login_required
@team_leader_required
def objectives():
    auth = Authentication.query.get(session["user_id"])

   
    team_leader = auth.team_leader
    if not team_leader:
        flash("Unauthorized access", "error")
        return redirect(url_for("auth.logout"))

   
    assigned_objectives = (
        Objective.query
        .filter_by(assigned_by=team_leader)
        .all()
    )

    
    received_objectives = (
        AdminObjective.query
        .filter_by(assigned_to=auth)
        .all()
    )

    grouped = defaultdict(list)
    admin_grouped = defaultdict(list)

    
    for obj in assigned_objectives:
        key = (obj.batch.title, obj.assigned_to_id)
        grouped[key].append(obj)

    
    for obj in received_objectives:
        key = (obj.admin_batch.title, obj.assigned_by_id)
        admin_grouped[key].append(obj)

    return render_template(
        "team_leader_objectives.html",
        grouped_objectives=grouped,
        admin_grouped_objectives=admin_grouped,
        role="team_leader",
        state="team_leader"
    )

@team_leader_bp.route("/review/<int:objective_id>", methods=["POST", "GET"])
@login_required
@team_leader_required
def review_objective(objective_id):
    objective = Objective.query.get(objective_id)
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
        objective.review = r
        db.session.commit()
        flash("reviewed successfully","success")
        return redirect(url_for("team_leader.objectives_overview", objective_id=objective.id))
    return render_template("team_leader_review.html", objective=objective, role="team_leader", state="team_leader")

@team_leader_bp.route("/edit_review/<int:objective_id>", methods=["POST", "GET"])
@login_required
@team_leader_required
def edit_review(objective_id):
    objective = Objective.query.get(objective_id)
    review = objective.review
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

        review.review = review_text
        review.score = score
        review.weighted_score = weighted_score
        db.session.commit()
        return redirect(url_for("team_leader.objectives_overview", objective_id=objective.id))
    return render_template("team_leader_edit_review.html", objective=objective,review=review)


@team_leader_bp.route("/objectives_overview/<int:objective_id>")
@login_required
@team_leader_required
def objectives_overview(objective_id):
    objective = Objective.query.get(objective_id)   
    total_weighted = 0
    if objective:
        employee = objective.assigned_to
        batch = objective.batch
        objectives = Objective.query.filter_by(batch_id=batch.id, assigned_to_id=employee.id).all()
        for obj in objectives:
            if obj.review:
                total_weighted += obj.review.weighted_score
    else:
        objective = AdminObjective.query.get(objective_id)
        employee = objective.assigned_to
        batch = objective.admin_batch
        objectives = AdminObjective.query.filter_by(admin_batch_id=batch.id, assigned_to_id=employee.id).all()
        for obj in objectives:
            if obj.admin_review:
                total_weighted += obj.admin_review.weighted_score
    return render_template("team_leader_objectives_overview.html",batch=batch,employee=employee,objectives=objectives,total_weighted=total_weighted,role="team_leader",state="team_leader",objective=objective)

@team_leader_bp.route("/objective_overview/<int:objective_id>/<int:assigned_by_id>")
@login_required
@team_leader_required
def objective_overview(objective_id, assigned_by_id):
    assigned_by_auth = Authentication.query.get(assigned_by_id)
    if assigned_by_auth.role == "team_leader":
        assigned_by = assigned_by_auth.team_leader
        objective = Objective.query.get(objective_id)
        batch = objective.batch
    elif assigned_by_auth.role == "admin":
        assigned_by = assigned_by_auth.administrator
        objective = AdminObjective.query.get(objective_id)
        batch = objective.admin_batch
    else:
        abort(404)
    title = batch.title
    year = batch.year
    employee = objective.assigned_to.name

    return render_template(
        "team_leader_objective_overview.html",
        year=year,
        title=title,
        objective=objective,
        employee=employee,
        role="team_leader",
        state="team_leader"
    )


@team_leader_bp.route("/delete_objective/<int:objective_id>/<int:assigned_by_id>", methods=["POST", "GET"])
@login_required
@team_leader_required
def delete_objective(objective_id,assigned_by_id):
    assigned_by_auth = Authentication.query.get(assigned_by_id)
    if assigned_by_auth.role == "team_leader":
        assigned_by = assigned_by_auth.team_leader
        objective = Objective.query.get(objective_id)
    elif assigned_by_auth.role == "admin":
        assigned_by = assigned_by_auth.administrator
        objective = AdminObjective.query.get(objective_id)
    else:
        abort(404)
    if request.method == "POST":
        db.session.delete(objective)
        db.session.commit()
        flash(f"Objective '{objective.objective}' deleted successfully", "success")
        return redirect(url_for("team_leader.objectives"))
    return render_template("delete_objective.html", objective=objective, role="team_leader", state="team_leader")

@team_leader_bp.route("/feedback/<int:objective_id>", methods=["GET", "POST"])
@login_required
@team_leader_required
def feedback(objective_id):
    admin_objective = AdminObjective.query.get(objective_id)
    
    if request.method == "POST":
        feedback_text = request.form.get("feedback")

        if not feedback_text:
            flash("Feedback is required", "error")
            return redirect(request.url)

        fb = TeamLeaderFeedback(feedback=feedback_text)
        admin_objective.admin_review.team_leader_feedback = fb
        db.session.commit()

        return redirect(
            url_for("team_leader.objective_overview", objective_id=admin_objective.id)
        )

    return render_template(
        "feedback.html",
        objective=admin_objective,
        role="employee",
        state="employee",
        Title="Feedback"
    )

@team_leader_bp.route("/edit_feedback/<int:objective_id>", methods=["GET", "POST"])
@login_required
@team_leader_required
def edit_feedback(objective_id):
    objective = AdminObjective.query.get(objective_id)

    
    if objective.assigned_to.authentication.id != session["user_id"]:
        flash("Unauthorized", "error")
        return redirect(url_for("team_leader.objectives"))

    admin_review = objective.admin_review
    if not admin_review:
        flash("No admin review yet", "error")
        return redirect(url_for("team_leader.objectives"))

    if request.method == "POST":
        feedback_text = request.form.get("feedback")
        if not feedback_text:
            flash("Feedback is required", "error")
            return redirect(request.url)

        if not admin_review.team_leader_feedback:
            admin_review.team_leader_feedback = TeamLeaderFeedback(
                feedback=feedback_text
            )
        else:
            admin_review.team_leader_feedback.feedback = feedback_text

        db.session.commit()
        return redirect(
            url_for("team_leader.objective_overview", objective_id=objective.id)
        )

    feedback_text = (
        admin_review.team_leader_feedback.feedback
        if admin_review.team_leader_feedback
        else ""
    )

    return render_template(
        "feedback.html",
        objective=objective,
        feedback=feedback_text,
        role="team_leader"
    )

