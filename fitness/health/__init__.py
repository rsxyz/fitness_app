
# fitness/health/__init__.py

from flask import Blueprint

# Define the blueprint
health_bp = Blueprint(
    'health_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Import routes after blueprint creation
from fitness.health.routes import health_routes
