import logging
from flask import render_template, request, jsonify, Blueprint

# Configure logging
logger = logging.getLogger(__name__)

# Create UI blueprint
ui_bp = Blueprint('ui', __name__)

# Create Dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

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

# New Cyberpunk Dashboard Routes
@dashboard_bp.route('/')
def index():
    """Render the cyberpunk-themed dashboard home page."""
    return render_template('dashboard_cyberpunk.html')

@dashboard_bp.route('/memory')
def memory():
    """Render the cyberpunk-themed memory visualization page."""
    return render_template('memory_cyberpunk.html')

@dashboard_bp.route('/cyberpunk-chat')
def cyberpunk_chat():
    """Render the cyberpunk-themed AI chat interface."""
    return render_template('cyberpunk-chat.html')

@dashboard_bp.route('/visualization')
def visualization():
    """Render the cyberpunk-themed visualization page."""
    return render_template('visualization_cyberpunk.html')

@dashboard_bp.route('/settings')
def settings():
    """Render the cyberpunk-themed settings page."""
    return render_template('settings_cyberpunk.html')

def init_routes(app):
    """
    Initialize UI routes for the dashboard.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(ui_bp)
    app.register_blueprint(dashboard_bp)
    logger.info("UI routes initialized")
    logger.info("Cyberpunk dashboard routes initialized") 