from app import db

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    administrator_id = db.Column(
        db.Integer,
        db.ForeignKey("administrators.id", ondelete="SET NULL"),
        nullable=True
    )

    administrator = db.relationship("Administrator", back_populates="departments")
    employees = db.relationship(
        "Employee",
        back_populates="department",
        cascade="all"
    )
    team_leader = db.relationship(
        "TeamLeader",
        back_populates="department",
        uselist=False,
        cascade="all, delete-orphan"
    )

class EmployeeEmail(db.Model):
    __tablename__ = "employee_emails"

    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(150),  nullable=False)
    department = db.Column(db.String(150), nullable=False)

class Authentication(db.Model):
    __tablename__ = "authentications"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    employee = db.relationship("Employee", back_populates="authentication", uselist=False)
    team_leader = db.relationship("TeamLeader", back_populates="authentication", uselist=False)
    administrator = db.relationship("Administrator", back_populates="authentication", uselist=False)

    objectives = db.relationship(
        "Objective",
        back_populates="assigned_to",
        cascade="all, delete-orphan"
    )

    admin_objectives = db.relationship(
        "AdminObjective",
        back_populates="assigned_to",
        cascade="all, delete-orphan"
    )

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False
    )

    authentication_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    department = db.relationship("Department", back_populates="employees")
    authentication = db.relationship("Authentication", back_populates="employee")

class TeamLeader(db.Model):
    __tablename__ = "team_leaders"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    authentication_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    department = db.relationship("Department", back_populates="team_leader")
    authentication = db.relationship("Authentication", back_populates="team_leader")

    objectives = db.relationship(
        "Objective",
        back_populates="assigned_by",
        cascade="all, delete-orphan"
    )

class AdminReview(db.Model):
    __tablename__ = "admin_reviews"

    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(500), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    weighted_score = db.Column(db.Float, nullable=False)

    admin_objective_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_objectives.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    admin_objective = db.relationship("AdminObjective", back_populates="admin_review")

    employee_feedback = db.relationship(
        "AdminReviewFeedback",
        back_populates="admin_review",
        uselist=False,
        cascade="all, delete-orphan")

    team_leader_feedback = db.relationship(
        "TeamLeaderFeedback",
        back_populates="admin_review",
        uselist=False,
        cascade="all, delete-orphan"
    )



class Administrator(db.Model):
    __tablename__ = "administrators"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    authentication_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    authentication = db.relationship("Authentication", back_populates="administrator")

    departments = db.relationship("Department", back_populates="administrator")

    admin_objectives = db.relationship(
        "AdminObjective",
        back_populates="assigned_by",
        cascade="all, delete-orphan"
    )

class AdminObjectiveBatch(db.Model):
    __tablename__ = "admin_objective_batches"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    admin_objectives = db.relationship(
        "AdminObjective",
        back_populates="admin_batch",
        cascade="all, delete-orphan"
    )


class AdminObjective(db.Model):
    __tablename__ = "admin_objectives"

    id = db.Column(db.Integer, primary_key=True)
    objective = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    score_range = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)

    admin_batch_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_objective_batches.id", ondelete="CASCADE"),
        nullable=False
    )

    assigned_by_id = db.Column(
        db.Integer,
        db.ForeignKey("administrators.id", ondelete="CASCADE"),
        nullable=False
    )

    assigned_to_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        nullable=False
    )

    admin_batch = db.relationship("AdminObjectiveBatch", back_populates="admin_objectives")
    assigned_by = db.relationship("Administrator", back_populates="admin_objectives")
    assigned_to = db.relationship("Authentication", back_populates="admin_objectives")

    admin_review = db.relationship(
        "AdminReview",
        back_populates="admin_objective",
        uselist=False,
        cascade="all, delete-orphan"
    )

class AdminReviewFeedback(db.Model):
    __tablename__ = "admin_review_feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.String(500), nullable=False)

    admin_review_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    admin_review = db.relationship(
        "AdminReview",
        back_populates="employee_feedback"
    )


class ObjectiveBatch(db.Model):
    __tablename__ = "objective_batches"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    objectives = db.relationship(
        "Objective",
        back_populates="batch",
        cascade="all, delete-orphan"
    )



class Objective(db.Model):
    __tablename__ = "objectives"

    id = db.Column(db.Integer, primary_key=True)
    objective = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    score_range = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)

    assigned_by_id = db.Column(
        db.Integer,
        db.ForeignKey("team_leaders.id", ondelete="CASCADE"),
        nullable=False
    )

    assigned_to_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        nullable=False
    )

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("objective_batches.id", ondelete="CASCADE"),
        nullable=False
    )

    assigned_by = db.relationship("TeamLeader", back_populates="objectives")
    assigned_to = db.relationship("Authentication", back_populates="objectives")
    batch = db.relationship("ObjectiveBatch", back_populates="objectives")

    review = db.relationship(
        "Review",
        back_populates="objective",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(500), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    weighted_score = db.Column(db.Float, nullable=False)

    objective_id = db.Column(
        db.Integer,
        db.ForeignKey("objectives.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    objective = db.relationship("Objective", back_populates="review")

    feedback = db.relationship(
        "Feedback",
        back_populates="review",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.String(500), nullable=False)

    review_id = db.Column(
        db.Integer,
        db.ForeignKey("reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    review = db.relationship("Review", back_populates="feedback")
    


class TeamLeaderFeedback(db.Model):
    __tablename__ = "team_leader_feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.String(500), nullable=False)

    admin_review_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    admin_review = db.relationship("AdminReview", back_populates="team_leader_feedback")

