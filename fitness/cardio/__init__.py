

# fitness/cardio/__init__.py

from flask import Blueprint

# Define the blueprint
cardio_bp = Blueprint(
    'cardio_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Import routes after blueprint creation
from fitness.cardio.routes import cardio_routes,activity_routes
