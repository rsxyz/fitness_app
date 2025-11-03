

from flask import Flask, render_template
from fitness.db.db import init_db
from fitness.cardio import cardio_bp
from fitness.food import food_bp
from fitness.health import health_bp
from fitness.strength import strength_bp

import os
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__,
             template_folder="fitness/templates",   # ✅ tell Flask where global templates are
             static_folder="fitness/static")        # optional if you use static assets

app.secret_key = "supersecret"

# tell Flask how many proxies to trust (set to 1 for single nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Register Blueprints
app.register_blueprint(cardio_bp, url_prefix="/cardio")
app.register_blueprint(food_bp, url_prefix="/food")
app.register_blueprint(health_bp, url_prefix="/health")
app.register_blueprint(strength_bp, url_prefix="/strength")

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
