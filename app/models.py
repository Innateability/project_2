from app import db

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    employees = db.relationship("Employee",back_populates="department",cascade="all, delete-orphan")
    departmenthead = db.relationship("DepartmentHead",back_populates="department",uselist=False,cascade="all, delete-orphan")

class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    dept_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", back_populates="employees")
    objectives = db.relationship("Objective", back_populates="assigned_to")
    authentication = db.relationship("Authentication",back_populates="employee",uselist=False,cascade="all, delete-orphan")

class DepartmentHead(db.Model):
    __tablename__ = "departmentheads"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    dept_id = db.Column(db.Integer, db.ForeignKey("departments.id"), unique=True)
    department = db.relationship("Department", back_populates="departmenthead")
    objectives = db.relationship("Objective",back_populates="assigned_by",cascade="all, delete-orphan")
    authentication = db.relationship("Authentication",back_populates="department_head",uselist=False,cascade="all, delete-orphan")

class Authentication(db.Model):
    __tablename__ = "authentications"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(300))
    name = db.Column(db.String(200))
    employee_id = db.Column(db.Integer,db.ForeignKey("employees.id", ondelete="CASCADE"),unique=True,nullable=True)
    employee = db.relationship("Employee",back_populates="authentication")
    department_head_id = db.Column(db.Integer,db.ForeignKey("departmentheads.id", ondelete="CASCADE"),unique=True,nullable=True)
    department_head = db.relationship("DepartmentHead",back_populates="authentication")

class Objective(db.Model):
    __tablename__ = "objectives"

    id = db.Column(db.Integer, primary_key=True)
    objective = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    score_range = db.Column(db.Integer, nullable=False)

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("objective_batches.id")
    )

    assigned_by_id = db.Column(db.Integer, db.ForeignKey("departmentheads.id"))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("employees.id"))

    batch = db.relationship("ObjectiveBatch", back_populates="objectives")
    assigned_by = db.relationship("DepartmentHead", back_populates="objectives")
    assigned_to = db.relationship("Employee", back_populates="objectives")
    reviews = db.relationship("Review", back_populates="objective", uselist=False)
    
class ObjectiveBatch(db.Model):
    __tablename__ = "objective_batches"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    assigned_by_id = db.Column(
        db.Integer,
        db.ForeignKey("departmentheads.id")
    )

    assigned_by = db.relationship("DepartmentHead")
    objectives = db.relationship(
        "Objective",
        back_populates="batch",
        cascade="all, delete-orphan"
    )


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer,primary_key=True)
    review = db.Column(db.String(500),nullable=False)
    score = db.Column(db.Integer, nullable=False)
    weighted_score = db.Column(db.Float, nullable=False)
    objective_id = db.Column(db.Integer,db.ForeignKey("objectives.id"),unique=True)
    objective = db.relationship("Objective",back_populates="reviews")
    feedbacks = db.relationship("Feedback",back_populates="review",uselist=False)

class Feedback(db.Model):
    __tablename__ = "feedbacks"
    id = db.Column(db.Integer,primary_key=True)
    feedback = db.Column(db.String(500),nullable=False)
    review_id = db.Column(db.Integer,db.ForeignKey("reviews.id"),unique=True)
    review = db.relationship("Review",back_populates="feedbacks")
    