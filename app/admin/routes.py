from flask import Blueprint,url_for,render_template,redirect,flash,get_flashed_messages,request,session,abort
from app.models import Authentication,AdminObjective,Employee,Review,AdminObjectiveBatch,AdminReview,Administrator,Objective,EmployeeEmail,TeamLeader
from app import db
from sqlalchemy.exc import IntegrityError
from app.utils import login_required,admin_required
from collections import defaultdict

admin_bp = Blueprint("admin",__name__,url_prefix="/admin")

@admin_bp.route("/",methods=["GET"])
@login_required
@admin_required
def home():
    auth_name = Authentication.query.get(session["user_id"]).name
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("home.html",state="admin",role="admin",auth_name=auth_name,auth=auth)

@admin_bp.route("/logout",methods=["POST","GET"])
@login_required
@admin_required
def logout():
    if request.method == "POST":
        session.clear()
        return redirect(url_for("base.login"))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("logout.html",state="admin",role="admin",auth=auth)

@admin_bp.route("/delete_account",methods=["POST","GET"])
@login_required
@admin_required
def delete_account():
    if request.method == "POST":
        authen = Authentication.query.get(session["user_id"])
        session.clear()
        if authen:
            db.session.delete(authen.administrator)
            db.session.delete(authen)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash("Cannot delete account. It is linked to other records.", "error")
            return redirect(url_for("base.admin_signup"))
        flash("account deleted succesfully","success")
        return redirect(url_for("base.login"))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("delete_account.html",state="admin",role="admin",auth=auth)

@admin_bp.route("/add_recipients")
@login_required
@admin_required
def recipients():
    current_user_id = session["user_id"]
    names_auth = Authentication.query.filter(Authentication.id != current_user_id).order_by(Authentication.name.asc()).all()
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_recipients.html",names_auth=names_auth,auth=auth,role="admin")

@admin_bp.route("/select_member")
@login_required
@admin_required
def select_member():
    current_user_id = session["user_id"]
    names_auth = Authentication.query.filter(Authentication.id != current_user_id).order_by(Authentication.name.asc()).all()
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_select_member.html",names_auth=names_auth,admin_id=current_user_id,auth=auth,role="admin")


@admin_bp.route("/add_objectives",methods=["POST","GET"])
@login_required
@admin_required
def add_objective():
    authen = Authentication.query.get(session["user_id"])
    administrator = authen.administrator if authen else None
    recipients = []
    if request.method == "GET":
        recipient_ids = request.args.getlist("recipients[]")
        recipients.extend(Authentication.query.filter(Authentication.id.in_(recipient_ids)).all())
        if not recipients:
            recipient_ids = request.args.get("recipient_id", type=int)
            recipients.append(Authentication.query.get(recipient_ids))
        auth = Authentication.query.get(session.get("user_id"))
        return render_template("admin_add_objective.html", recipients=recipients,state="admin",auth=auth,role="admin")



    if request.method == "POST":
        recipient_ids = request.form.getlist("recipients[]")
        if recipient_ids:
            recipients.extend(Authentication.query.filter(Authentication.id.in_(recipient_ids)).all())
        if not recipients:
            recipient_ids = request.args.get("recipient_id", type=int)
            recipients.extend(Authentication.query.get(recipient_ids))
        title = request.form.get("title")
        year = int(request.form.get("year"))

        objectives = request.form.getlist("objectives[]")
        categories = request.form.getlist("categories[]")
        weights = request.form.getlist("weights[]")
        score_range = 5

       
        batch = AdminObjectiveBatch(title=title, year=year)
        db.session.add(batch)
        db.session.flush()  

        
        for obj, cat, weight in zip(
            objectives, categories, weights
        ):
            for recipient in recipients:
                objective = AdminObjective(
                    objective=obj,
                    category=cat,
                    weight=int(weight),
                    score_range=int(score_range),
                    assigned_to=recipient,          
                    assigned_by=administrator,
                    admin_batch=batch
                )
                db.session.add(objective)
        db.session.commit()
        flash("Objective(s) created successfully", "success")
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("admin.objectives",auth_id=recipients[0].id,auth=auth))

    

    employees = []
    team_leaders = []

    if administrator:
        for department in administrator.departments:
            for emp in department.employees:
                if emp.authentication:
                    employees.append(emp.authentication)

            if department.team_leader and department.team_leader.authentication:
                team_leaders.append(department.team_leader.authentication)
    auth = Authentication.query.get(session.get("user_id"))
    return render_template(
        "admin_add_objective.html",
        employees=employees,
        team_leaders=team_leaders,
        state="admin",
        auth=auth,role="admin")

@admin_bp.route("/add_member", methods=["POST", "GET"])
@login_required
@admin_required
def add_member():
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        department = request.form.get("department")
        replace = request.form.get("replace")

        existing_email = EmployeeEmail.query.filter_by(email=email).first()

        if existing_email and existing_email.department != department:
            flash("This email is already enrolled in another department.", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return render_template("admin_add_member.html", state="admin",auth=auth,role="admin")

        if existing_email and existing_email.role == role and existing_email.department == department:
            if role == "team_leader":
                role = "team leader"
            flash(f"This email is already enrolled as {role} in this department.", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return render_template("admin_add_member.html", state="admin",auth=auth,role="admin")
        if existing_email and existing_email.role == "team_leader" and existing_email.department == department:
            role = "team leader"
            flash(f"This email is already enrolled as {role} in this department.", "error")
            auth = Authentication.query.get(session.get("user_id"))
            return render_template("admin_add_member.html", state="admin",auth=auth,role="admin")

        if role == "team_leader":
            existing_tl = EmployeeEmail.query.filter_by(
                role="team_leader", department=department
            ).first()

            if existing_tl and existing_tl.email != email and replace != "yes":
                auth = Authentication.query.get(session.get("user_id"))
                return render_template(
                    "admin_add_member.html",
                    state="admin",
                    confirm_replace=True,
                    existing_tl_email=existing_tl.email,
                    form_email=email,
                    form_role=role,
                    form_department=department,
                    auth=auth,role="admin"
                )

            if existing_tl and existing_tl.email != email and replace == "yes":
                existing_tl.role = "employee"

                old_auth = Authentication.query.filter_by(email=existing_tl.email).first()
                if old_auth and old_auth.team_leader:
                    old_tl = old_auth.team_leader
                    dept = old_tl.department
                    new_emp = Employee(name=old_auth.name, department=dept)
                    old_auth.role = "employee"
                    old_auth.employee = new_emp
                    db.session.add(new_emp)
                    db.session.delete(old_tl)

                db.session.flush()

            if existing_email and existing_email.role == "employee":
                existing_email.role = "team_leader"

                emp_auth = Authentication.query.filter_by(email=email).first()
                if emp_auth and emp_auth.employee:
                    old_emp = emp_auth.employee
                    dept = old_emp.department
                    new_tl = TeamLeader(name=emp_auth.name, department=dept)
                    emp_auth.role = "team_leader"
                    emp_auth.team_leader = new_tl
                    db.session.add(new_tl)
                    db.session.delete(old_emp)

                db.session.commit()
                flash(f"{email} has been promoted to team leader.", "success")
                auth = Authentication.query.get(session.get("user_id"))
                return redirect(url_for("admin.home",auth=auth))

        if not existing_email:
            new_entry = EmployeeEmail(email=email, role=role, department=department)
            db.session.add(new_entry)
            db.session.commit()
            flash("Member enrolled successfully.", "success")
            auth = Authentication.query.get(session.get("user_id"))
            return redirect(url_for("admin.home",auth=auth))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_add_member.html", state="admin",auth=auth,role="admin")

@admin_bp.route("/edit_objectives/<int:objective_id>", methods=["POST", "GET"])
@login_required
@admin_required
def edit_objective(objective_id):
    admin_email = session.get("email")
    auth = Authentication.query.filter_by(email=admin_email).first()
    administrator = auth.administrator
    
    objective = AdminObjective.query.filter_by(id=objective_id).first()
    if request.method == "POST":
        admin_objective = AdminObjective.query.filter_by(id=objective_id).first()
        title = request.form.get("title")
        year = request.form.get("year")
        objective = request.form.get("objective")
        category = request.form.get("category")
        weight = request.form.get("weight")
        score_range = request.form.get("score_range")
        emp_name = request.form.get("assigned_to")
        assigned_to = admin_objective.assigned_to
        admin_batch = AdminObjectiveBatch.query.filter_by(title=title,year=year).first()
        if admin_batch:
            obj = AdminObjective.query.filter_by(id=objective_id).first()
        else:
            admin_batch = AdminObjectiveBatch(title=title,year=year)
            obj = AdminObjective.query.filter_by(id=objective_id).first()
            obj.admin_batch = admin_batch
        db.session.add(obj)
        
        obj.admin_batch.title = title
        obj.admin_batch.year = year
        obj.objective = objective
        obj.admin_batch.year = year
        obj.category = category
        obj.weight = weight
        obj.score_range = score_range
        obj.admin_batch = admin_batch
        db.session.commit()
        flash(f"Objective {title} edited successfully", "success")
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("admin.objectives",auth_id=assigned_to.id,auth=auth))
    
    authen = Authentication.query.get(session["user_id"])
    administrator = authen.administrator
    departments = administrator.departments
    
    employee_names = []
    team_leader_names = []
    
    for department in departments:
        for emp in department.employees:
            if emp.authentication:
                employee_names.append(emp.authentication.name)
        if department.team_leader and department.team_leader.authentication:
            team_leader_names.append(department.team_leader.authentication.name)
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_edit_objective.html",employee_names=employee_names,objective=objective,team_leader_names=team_leader_names,Title="EDIT OBJECTIVES",state='admin',auth=auth,role="admin")


@admin_bp.route("/objectives/<int:auth_id>")
@login_required
@admin_required
def objectives(auth_id):
    auth = Authentication.query.get(auth_id)
    admin_auth =  Authentication.query.get(session.get("user_id"))
    if auth.administrator:
        mode = "See All"
        grouped = defaultdict(list)
        admin_objectives = AdminObjective.query.filter_by(assigned_by=admin_auth).all()
        for obj in admin_objectives:
            key = (obj.admin_batch.title, obj.assigned_to_id)
            grouped[key].append(obj)
        username = auth.name
    if auth.employee or auth.team_leader:
        mode = "See Objective"
        grouped = defaultdict(list)
        for obj in auth.admin_objectives:
            key = (obj.admin_batch.title)
            grouped[key].append(obj)
        username = auth.name
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_objectives.html",grouped_objectives=grouped,state='admin',name=username,mode=mode,auth=auth,role="admin")

@admin_bp.route("/review/<int:objective_id>", methods=["POST", "GET"])
@login_required
@admin_required
def review_objective(objective_id):
    objective = AdminObjective.query.get(objective_id)
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
        r = AdminReview(
            review=review_text,
            score=score,
            weighted_score=weighted_score)
        objective.admin_review= r
        db.session.commit()
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("admin.objective_overview", objective_id=objective.id,auth=auth))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_review.html", objective=objective,state='admin',auth=auth,role="admin")

@admin_bp.route("/edit_review/<int:objective_id>", methods=["POST", "GET"])
@login_required
@admin_required
def edit_review(objective_id):
    objective = AdminObjective.query.get(objective_id)
    review = objective.admin_review
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
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("admin.objective_overview", objective_id=objective.id,auth=auth))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_edit_review.html", objective=objective,review=review, role="admin", state="admin",Title="Edit Review",auth=auth)


@admin_bp.route("/objectives_overview/<int:objective_id>")
@login_required
@admin_required
def objectives_overview(objective_id):
    objective = AdminObjective.query.get(objective_id)
    batch = objective.admin_batch
    employee = objective.assigned_to
    objectives = AdminObjective.query.filter_by(admin_batch_id=batch.id, assigned_to_id=employee.id).all()
    total_weighted = 0
    for obj in objectives:
        if obj.admin_review:  
            total_weighted += obj.admin_review.weighted_score
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_objectives_overview.html",employee=employee,objectives=objectives,total_weighted=total_weighted,batch=batch,state='admin',objective=objective,auth=auth,role="admin")

@admin_bp.route("/objective_overview/<int:objective_id>")
@login_required
@admin_required
def objective_overview(objective_id):
    objective = AdminObjective.query.get(objective_id)
    batch = objective.admin_batch
    title = batch.title
    year = batch.year
    employee = objective.assigned_to.name
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("admin_objective_overview.html",year=year,title=title,employee=employee,objective=objective,state='admin',auth=auth,role="admin")


@admin_bp.route("/delete_objective/<int:objective_id>", methods=["POST", "GET"])
@login_required
@admin_required
def delete_objective(objective_id):
    objective = AdminObjective.query.get(objective_id)
    batch = objective.admin_batch
    employee = objective.assigned_to
    objectives = AdminObjective.query.filter_by(admin_batch_id=batch.id, assigned_to_id=employee.id).all()
    if request.method == "POST":
        for obj in objectives:
            db.session.delete(obj)
        db.session.commit()
        flash(f"Objective '{objective.objective}' deleted successfully", "success")
        auth = Authentication.query.get(session.get("user_id"))
        return redirect(url_for("admin.objectives",auth_id=auth.id))
    auth = Authentication.query.get(session.get("user_id"))
    return render_template("delete_objective.html", objective=objective,state='admin',auth=auth,role="admin")