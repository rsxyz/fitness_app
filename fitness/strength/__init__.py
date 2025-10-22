# fitness/strength/__init__.py

from flask import Blueprint

# Define the blueprint
strength_bp = Blueprint(
    'strength_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Import routes after blueprint creation
from fitness.strength.routes import strength_routes
