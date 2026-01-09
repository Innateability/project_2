from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("please login first","error")
            return redirect(url_for("base.login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Page can only be accessed by admins","error")
            return redirect(url_for("employee.home"))
        return view(*args, **kwargs)
    return wrapped

def employee_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "employee":
            flash("Page can only be accessed by users","error")
            return redirect(url_for("admin.home"))
        return view(*args, **kwargs)
    return wrapped

