import logging
from flask import render_template, request, jsonify, Blueprint

# Configure logging
logger = logging.getLogger(__name__)

# Create UI blueprint
ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@ui_bp.route('/status')
def status():
    """Return the status of the dashboard."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0"
    })

def init_routes(app):
    """
    Initialize UI routes for the dashboard.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(ui_bp)
    logger.info("UI routes initialized") 