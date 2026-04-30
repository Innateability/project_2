from flask import Blueprint,render_template,request,url_for,redirect,session,flash,get_flashed_messages,abort
from app.utils import login_required,employee_required
from app.models import Authentication,Objective,TeamLeader,Employee,Feedback,AdminObjective,AdminReviewFeedback,TeamLeaderFeedback,Review,Messages,ObjectiveBatch,AuthReviewed,ReviewOpenObjective
from app import db
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
from datetime import datetime, timedelta

employee_bp = Blueprint("employee",__name__,url_prefix="/employee")

@employee_bp.route("/")
@login_required
@employee_required
def home():
    auth_name = Authentication.query.get(session["user_id"]).name
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("home.html",state="employee",role="employee",auth_name=auth_name,auth=auth)

@employee_bp.route("/logout",methods=["POST","GET"])
@login_required
@employee_required
def logout():
    auth_name = Authentication.query.get(session["user_id"]).name
    if request.method == "POST":
        session.pop("role",None)
        session.pop("user_id",None)
        session.pop("email",None)
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("base.login",auth=auth))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("logout.html",state="employee",role="employee",auth=auth)

@employee_bp.route("/delete_account",methods=["POST","GET"])
@login_required
@employee_required
def delete_account():
    auth_name = Authentication.query.get(session["user_id"]).name
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
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("base.login",auth=auth,role="employee"))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("delete_account.html",state="employee",role="employee",auth=auth)

@employee_bp.route("/select_batch",methods=["POST","GET"])
@login_required
@employee_required
def select_batch():
    batches = ObjectiveBatch.query.all()
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("select_batch.html",auth=auth,role="employee",batches=batches,state="employee")

@employee_bp.route("/choose_batch",methods=["POST","GET"])
@login_required
@employee_required
def select_batch_for_open_batch():
    batches = ObjectiveBatch.query.all()
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("select_batch_for_open_batch.html",auth=auth,role="employee",batches=batches,state="employee")

@employee_bp.route("/objective_batches",methods=["POST","GET"])
@login_required
@employee_required
def objective_batches():
    auth_name = Authentication.query.get(session["user_id"]).name
    current_user_id = session["user_id"]
    auth = Authentication.query.get(session.get("user_id"))
    batches = ObjectiveBatch.query.order_by(ObjectiveBatch.year.desc()).all()
    now = datetime.now()
    return render_template("objective_batches.html",auth=auth,role="employee",state="employee",batches=batches,now=now)


@employee_bp.route("/objectives")
@login_required
@employee_required
def objectives():
    auth_name = Authentication.query.get(session["user_id"]).name
    auth = Authentication.query.get(session.get("user_id"))
    grouped = defaultdict(list)
    admin_grouped = defaultdict(list)

    for obj in auth.objectives:
        key = (obj.batch.title, obj.batch.id)
        grouped[key].append(obj)

    for admin_obj in auth.admin_objectives:
        key = (admin_obj.batch.title, admin_obj.batch.id)
        admin_grouped[key].append(admin_obj)
    auth = Authentication.query.get(session.get("user_id"))
    # batch = ObjectiveBatch.query.get(batch_id)
    # active = batch.active
    return render_template(
        "employee_objectives.html",
        grouped_objectives=grouped,
        admin_grouped_objectives=admin_grouped,
        role="employee",
        state="employee",
        auth=auth
    )

@employee_bp.route("/feedback/<int:objective_id>/<role>", methods=["GET", "POST"])
@login_required
@employee_required
def feedback(objective_id, role):
    auth_name = Authentication.query.get(session["user_id"]).name
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
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(
            url_for(
                "employee.objective_overview",
                objective_id=objective.id,
                assigned_by_id=objective.assigned_by.authentication.id,
                auth=auth
            )
        )
    auth = Authentication.query.get(session.get("user_id"))
    active = objective.batch.active
    now = datetime.now()
    return render_template(
        "employee_feedback.html",
        objective=objective,
        role="employee",
        state="employee",
        Title="Feedback",
        auth=auth,
        active=active,
        now=now
    )

@employee_bp.route("/edit_feedback/<int:objective_id>/<role>", methods=["GET", "POST"])
@login_required
@employee_required
def edit_feedback(objective_id, role):
    now = datetime.now()
    auth_name = Authentication.query.get(session["user_id"]).name

    objective = None
    review = None
    admin_review = None

  
    if role == "team_leader":
        objective = Objective.query.get(objective_id)

        if objective.assigned_to.id != session["user_id"]:
            flash("Unauthorized", "error")
            auth = Authentication.query.get(session.get("user_id")) 
            return redirect(url_for("employee.objectives",auth=auth,role="employee"))

        review = objective.review
        if not review:
            flash("No review yet", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(url_for("employee.objectives",auth=auth,role="employee"))

        feedback_text = (
            review.feedback.feedback
            if review.feedback
            else ""
        )

   
    elif role == "admin":
        objective = AdminObjective.query.get(objective_id)

        if objective.assigned_to.id != session["user_id"]:
            flash("Unauthorized", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(url_for("employee.objectives",auth=auth,role="employee"))

        admin_review = objective.admin_review
        if not admin_review:
            flash("No review yet", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(url_for("employee.objectives",auth=auth,role="employee"))

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
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(request.url,auth=auth,role="employee")

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
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(
            url_for("employee.objectives_overview", objective_id=objective.id,auth=auth,role="employee")
        )
    auth = Authentication.query.get(session.get("user_id"))   
    active = objective.batch.active
    return render_template(
        "employee_feedback.html",
        objective=objective,
        feedback=feedback_text,
        role="employee",
        state="employee",
        Title="Edit Feedback",
        auth=auth,
        active=active,
        now=now
    )


@employee_bp.route("/objectives_overview/<int:objective_id>")
@login_required
@employee_required
def objectives_overview(objective_id):
    now = datetime.now()
    auth_name = Authentication.query.get(session["user_id"]).name
    objective = Objective.query.get(objective_id)
    admin_objective = AdminObjective.query.get(objective_id)
    if objective:
        batch = objective.batch
        employee = objective.assigned_to
        if employee.id != session["user_id"]:
            flash("Unauthorized access", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(url_for("employee.objectives",auth=auth,role="employee"))
        objectives = Objective.query.filter_by(batch_id=batch.id,assigned_to_id=employee.id).all()
        total_weighted = 0
        for obj in objectives:
            if obj.review: 
                total_weighted += obj.review.weighted_score
    elif admin_objective:
        batch = admin_objective.batch
        employee = admin_objective.assigned_to
        if employee.id != session["user_id"]:
            flash("Unauthorized access", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(url_for("employee.objectives",auth=auth,role="employee"))
        
        objectives = AdminObjective.query.filter_by(batch_id=batch.id,assigned_to_id=employee.id).all()
        total_weighted = 0
        for obj in objectives:
            if obj.admin_review: 
                total_weighted += obj.admin_review.weighted_score

    auth = Authentication.query.get(session.get("user_id"))
    active = batch.active
    return render_template(
        "employee_objectives_overview.html",
        batch=batch,
        employee=employee,
        objectives=objectives,
        total_weighted=total_weighted,
        role="employee",
        state="employee",
        auth=auth,
        active=active,
        now=now
    )

@employee_bp.route("/objective_overview/<int:objective_id>/<int:assigned_by_id>",methods=["POST","GET"])
@login_required
@employee_required
def objective_overview(objective_id, assigned_by_id):
    now = datetime.now()
    if request.method == "POST":
        message = request.form.get("message")
        if message:
            now = datetime.now()
            new_message = Messages(message=message,status="employee",timestamp=now,objective_id=objective_id)
            db.session.add(new_message)
            db.session.commit()
            return redirect(url_for("employee.objective_overview", objective_id=objective_id,assigned_by_id=assigned_by_id))
    messages = Messages.query.filter_by(objective_id=objective_id).order_by(Messages.timestamp.asc()).all()
    auth_name = Authentication.query.get(session["user_id"]).name
    assigned_by = Authentication.query.get(assigned_by_id)
    if assigned_by.role == "team_leader":
        objective = Objective.query.get(objective_id)
        batch = objective.batch
        title = batch.title
        year = batch.year
        employee = objective.assigned_to.name
    elif assigned_by.role == "admin":
        objective = AdminObjective.query.get(objective_id)
        batch = objective.batch
        title = batch.title
        year = batch.year
        employee = objective.assigned_to.name
    auth = Authentication.query.get(session.get("user_id"))
    active = batch.active
    return render_template(
        "employee_objective_overview.html",
        year=year,
        title=title,
        employee=employee,
        role="employee",
        state="employee",
        objective=objective,
        messages=messages,
        auth=auth,
        active=active,
        now=now)

@employee_bp.route("/review/<int:objective_id>", methods=["POST", "GET"])
@login_required
@employee_required
def review_objective(objective_id):
    objective = Objective.query.get(objective_id)
    active = objective.batch.active
    now = datetime.now()
    if request.method == "POST":
        review_text = request.form.get("review")
        score_raw = request.form.get("score")
        if not all([review_text, score_raw]):
            flash("Both Review and Score are needed", "error")
            return redirect(request.url)
        try:
            score = round(float(score_raw), 1)
        except ValueError:
            flash("Score must be a number", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(request.url,auth=auth)
        weighted_score = (score * objective.weight) / objective.score_range
        r = Review(
            review=review_text,
            score=score,
            weighted_score=weighted_score
        )
        objective.review = r
        db.session.commit()
        flash("reviewed successfully","success")
        auth = Authentication.query.get(session.get("user_id"))
        flash("Reviewed Edited Successfully","success")
        return redirect(url_for("employee.home", objective_id=objective.id, auth=auth, mode=""))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("employee_review.html", objective=objective, role="employee", state="employee",auth=auth,active=active,now=now)

@employee_bp.route("/open_objectives/<int:batch_id>",methods=["POST","GET"])
@login_required
@employee_required
def open_objectives(batch_id):
    auth = Authentication.query.get(session.get("user_id"))
    objs = defaultdict(list)
    open_objectives = AdminObjective.query.filter(AdminObjective.batch_id == batch_id,AdminObjective.private != True,AdminObjective.assigned_to_id != auth.id).all() + Objective.query.filter(Objective.batch_id == batch_id,Objective.private != True,Objective.assigned_to_id != auth.id).all()
    now = datetime.now()
    for open_objective in open_objectives:
        key = (open_objective.assigned_to,open_objective.batch)
        objs[key] = open_objective

    open_objective = []
    for key,obj in objs.items():
        if isinstance(obj, Objective):
            mode = "t"
        else:
            mode = "a"
        open_objective.append((obj, mode))
    batch = ObjectiveBatch.query.get(batch_id)
    return render_template("open_objectives.html",open_objectives=open_objective,state="employee",role="employee",batch=batch,now=now)


@employee_bp.route("/open_objectives_overview/<int:batch_id>/<int:objective_id>/<mode>",methods=["POST","GET"])
@login_required
@employee_required
def open_objectives_overview(batch_id,objective_id,mode):
    auth = Authentication.query.get(session["user_id"])
    auth_name = auth.name
    auth_id = auth.id
    if mode == "a":
        auth_reviewed = AuthReviewed.query.filter_by(admin_objective_id=objective_id,auth_id=auth_id).all()
        objective = AdminObjective.query.get(objective_id)
        batch = objective.batch
        employee = objective.assigned_to
        objectives = AdminObjective.query.filter_by(batch_id=batch_id, assigned_to_id=employee.id, private=False).all()
    else:
        auth_reviewed = AuthReviewed.query.filter_by(objective_id=objective_id,auth_id=auth_id).all()
        objective = Objective.query.get(objective_id)
        batch = objective.batch
        employee = objective.assigned_to
        objectives = Objective.query.filter_by(batch_id=batch_id, assigned_to_id=employee.id, private=False).all()
    total_weighted = 0
    objs = {}
    for obj in objectives:
        if mode == "a":
            auth_reviewed = AuthReviewed.query.filter_by(admin_objective_id=obj.id,auth_id=auth_id).first()
        else:
            auth_reviewed = AuthReviewed.query.filter_by(objective_id=obj.id,auth_id=auth_id).first()
        if hasattr(obj, "open_objectives_review"):  
            if obj.open_objectives_review:
                key = (obj,auth_reviewed)
                objs[key] = obj.open_objectives_review.weighted_score
                total_weighted += obj.open_objectives_review.weighted_score
    auth = Authentication.query.get(session.get("user_id"))
    now = datetime.now()
    return render_template("open_objectives_overview.html",employee=employee,objectives=objs,objective=objectives,total_weighted=total_weighted,batch=batch,state='employee',auth=auth,role="employee",now=now,mode=mode,auth_reviewed=auth_reviewed)

@employee_bp.route("/open_objective_overview/<int:objective_id>/<int:assigned_by_id>/<mode>", methods=["POST","GET"])
@login_required
@employee_required
def open_objective_overview(objective_id, assigned_by_id, mode):
    auth_id = session.get("user_id")
    if mode == "t":
        auth_reviewed = AuthReviewed.query.filter_by(objective_id=objective_id,auth_id=auth_id).all()
    else:
        auth_reviewed = AuthReviewed.query.filter_by(admin_objective_id=objective_id,auth_id=auth_id).all()
    assigned_by_auth = Authentication.query.get(assigned_by_id)
    if assigned_by_auth.role == "team_leader":
        assigned_by = assigned_by_auth.team_leader
        objective = Objective.query.get(objective_id)
        batch = objective.batch
    elif assigned_by_auth.role == "admin":
        assigned_by = assigned_by_auth.administrator
        objective = AdminObjective.query.get(objective_id)
        batch = objective.batch
    else:
        abort(404)
    title = batch.title
    year = batch.year
    employee = objective.assigned_to.name
    auth = Authentication.query.get(session.get("user_id"))
    now = datetime.now()
    return render_template(
        "open_objective_overview.html",
        year=year,
        title=title,
        objective=objective,
        employee=employee,
        role="employee",
        state="employee",
        mode=mode,
        auth = Authentication.query.get(session.get("user_id")),
        auth_reviewed=auth_reviewed,
        now=now)


@employee_bp.route("/review_open_objective/<int:objective_id>/<mode>", methods=["POST", "GET"])
@login_required
@employee_required
def review_open_objective(objective_id,mode):
    now = datetime.now()
    auth_id = session.get("user_id")
    if mode == "t":
        auth_reviewed = AuthReviewed.query.filter_by(objective_id=objective_id,auth_id=auth_id).all()
    else:
        auth_reviewed = AuthReviewed.query.filter_by(admin_objective_id=objective_id,auth_id=auth_id).all()
    objective = Objective.query.get(objective_id) if mode == "t" else AdminObjective.query.get(objective_id)
    active = objective.batch.active
    if request.method == "POST":
        review_text = request.form.get("review")
        score_raw = request.form.get("score")
        if not all([review_text, score_raw]):
            flash("Both Review and Score are needed", "error")
            return redirect(request.url)
        try:
            score = round(float(score_raw), 1)
        except ValueError:
            flash("Score must be a number", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(request.url,auth=auth)
        weighted_score = (score * objective.weight) / objective.score_range
        obj = objective.open_objectives_review
        batch = objective.batch
        if obj and obj.weighted_score:
            weighted_scores = obj.weighted_score
        else:
            weighted_scores = 0
        
        if obj and obj.number_reviews:
            number = obj.number_reviews
        else:
            number = 0
        new_number = number + 1
        new_weighted_score = ((weighted_scores * number) + weighted_score)/new_number
        if obj:
            obj.weighted_score = new_weighted_score
            obj.number_reviews = new_number
            obj.score = score
            obj.review = review_text
        else:
            obj = ReviewOpenObjective(
                review=review_text,
                score=score,
                weighted_score=new_weighted_score,
                number_reviews=new_number)
            objective.open_objectives_review = obj
        if isinstance(objective, Objective):
            auth_review = AuthReviewed(
                score=score,
                auth_id=auth_id,
                objective_id = objective_id)
        else:
            auth_review = AuthReviewed(
                score=score,
                auth_id=auth_id,
                admin_objective_id = objective_id)
        db.session.add(auth_review)
        db.session.commit()
        flash("reviewed successfully","success")
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("employee.open_objectives_overview", objective_id=objective.id, auth=auth, mode=mode, batch_id=batch.id))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_review.html", objective=objective, role="employee", state="employee",auth=auth, mode=mode, auth_reviewed=auth_reviewed,active=active,now=now)


@employee_bp.route("/edit_review/<int:objective_id>/<mode>", methods=["POST", "GET"])
@login_required
@employee_required
def edit_review(objective_id,mode):
    if mode == "a":
        objective = AdminObjective.query.get(objective_id)
        review = objective.admin_review
    else:
        objective = Objective.query.get(objective_id)
        review = objective.review
    active = objective.batch.active
    if request.method == "POST":
        review_text = request.form.get("review")
        score_raw = request.form.get("score")
        if not all([review_text, score_raw]):
            flash("Both Review and Score are needed", "error")
            return redirect(request.url)
        try:
            score = round(float(score_raw), 1)
        except ValueError:
            flash("Score must be a number", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(request.url,auth=auth)
        weighted_score = (score * objective.weight) / objective.score_range

        review.review = review_text
        review.score = score
        review.weighted_score = weighted_score
        db.session.commit()
        auth = Authentication.query.get(session.get("user_id"))
        flash("Reviewed Edited Successfully","success")
        return redirect(url_for("employee.home", objective_id=objective.id, auth=auth, mode=""))
    auth = Authentication.query.get(session.get("user_id"))
    now = datetime.now()
    return render_template("employee_edit_review.html", objective=objective,review=review,state="employee",auth=auth,role="employee",active=active,now=now)
