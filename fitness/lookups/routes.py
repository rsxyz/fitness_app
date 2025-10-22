from flask import render_template
from . import lookup_bp

@lookup_bp.route('/')
def index():
    return render_template('lookup_index.html')
