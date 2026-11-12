
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Import application routes
    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.billing import billing_bp
    from app.routes.reports import reports_bp
    from app.routes.main import main_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(main_bp)

    # Create database tables and bootstrap initial admin
    with app.app_context():
        db.create_all()

        from app.models import User

        admin_username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME')
        admin_password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD')

        if admin_username and admin_password:
            existing_admin = User.query.filter_by(
                username=admin_username
            ).first()

            if not existing_admin:
                admin = User(
                    username=admin_username,
                    role='admin'
                )
                admin.set_password(admin_password)

                db.session.add(admin)
                db.session.commit()

    return app
