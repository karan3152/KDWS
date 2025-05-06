import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager, csrf, migrate, Base, init_extensions
from config import Config
from blueprints import main, images, auth, admin, admin_employer, clients
from blueprints.document_management import document_management

from flask_wtf.csrf import CSRFError
from flask import flash, redirect, url_for

def create_app(config_class=Config):
    # create the app
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)

    # Fix for proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(images)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(admin_employer, url_prefix='/employer')
    app.register_blueprint(clients, url_prefix='/clients')
    app.register_blueprint(document_management, url_prefix='/documents')

    # Ensure the instance path exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Add custom Jinja filters
    @app.template_filter('has_attr')
    def has_attr_filter(obj, attr):
        return hasattr(obj, attr)

    @app.template_filter('get_attr')
    def get_attr_filter(obj, attr):
        return getattr(obj, attr, None)

    # Create database tables
    with app.app_context():
        from models import User, EmployeeProfile, EmployerProfile, Document, FamilyMember, PasswordResetToken, OTP
        db.create_all()

        # Add new columns to User table if they don't exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        # Check if we need to add the new columns
        if 'is_temporary_password' not in columns or 'initial_password' not in columns:
            print("Adding new columns to User table...")
            if 'is_temporary_password' not in columns:
                db.session.execute('ALTER TABLE user ADD COLUMN is_temporary_password BOOLEAN DEFAULT 1')
            if 'initial_password' not in columns:
                db.session.execute('ALTER TABLE user ADD COLUMN initial_password VARCHAR(64)')
            db.session.commit()
            print("Columns added successfully.")

    # CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('The form you submitted is invalid or expired. Please try again.', 'danger')
        return redirect(url_for('main.document_center'))

    # Add GET route for /delete-all-documents to redirect to confirmation page
    @app.route('/documents/delete-all-documents', methods=['GET'])
    def delete_all_documents_get():
        return redirect(url_for('document_management.confirm_delete_all_documents'))

    return app

# Create the app instance
app = create_app()

# Only for local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)