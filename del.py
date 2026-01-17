from flask import Blueprint,url_for,render_template,redirect,flash,get_flashed_messages,request,session,abort
from app.models import Authentication,AdminObjective,Employee,Review,AdminObjectiveBatch,AdminReview,Administrator,Objective,EmployeeEmail
from app import db
from sqlalchemy.exc import IntegrityError
from app.utils import login_required,admin_required
from collections import defaultdict
from app import delete

app = delete()

if __name__=="__main__":
    app.run(debug=True)
