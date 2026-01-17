from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
import os
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app,db)

    logging.basicConfig(level=logging.INFO)
    from app.admin import admin_bp
    from app.employee import employee_bp
    from app.base import base_bp
    from app.team_leader import team_leader_bp


    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(base_bp)
    app.register_blueprint(team_leader_bp)
    return app