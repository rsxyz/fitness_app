from flask import Blueprint
lookup_bp = Blueprint('lookup_bp', __name__, template_folder='templates')
from . import routes
