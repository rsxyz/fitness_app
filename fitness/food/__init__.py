
# fitness/food/__init__.py

from flask import Blueprint

# Define the blueprint
food_bp = Blueprint(
    'food_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Import routes after blueprint creation
from fitness.food.routes import food_routes,meal_types_routes
