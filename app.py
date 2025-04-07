import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
login_manager.login_view = 'login'

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a_secure_secret_key_for_development"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database to use SQLite instead
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employee_management.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'uploads')
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload size

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register routes after db and login_manager initialization
with app.app_context():
    # Import models and create tables
    from models import User, EmployeeProfile, EmployerProfile, Document, FamilyMember, NewsUpdate, PasswordResetToken
    db.drop_all()  # Drop all tables
    db.create_all()  # Create all tables with current schema
    
    # Import routes
    import routes
    import routes_document_center
    import routes_admin_employer

# Only for local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)