from functools import wraps
from flask import session, redirect, url_for, flash, request

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
            return redirect(request.url)
        return view(*args, **kwargs)
    return wrapped

def team_leader_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "team_leader":
            flash("Page can only be accessed by team leaders","error")
            return redirect(request.url)
        return view(*args, **kwargs)
    return wrapped


def employee_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "employee":
            flash("Page can only be accessed by users","error")
            return redirect(request.url)
        return view(*args, **kwargs)
    return wrapped

