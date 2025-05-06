from flask import Blueprint

# Create blueprints
main = Blueprint('main', __name__)
images = Blueprint('images', __name__)
auth = Blueprint('auth', __name__)
admin = Blueprint('admin', __name__)
admin_employer = Blueprint('admin_employer', __name__)
clients = Blueprint('clients', __name__)

# Import routes after creating blueprints to avoid circular imports
from . import routes
from . import routes_images
from . import routes_auth
from . import routes_admin
from . import routes_admin_employer
from . import client_routes