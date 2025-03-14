"""
VOT1 Dashboard Routes

This module defines the routes for the dashboard web application.
"""

import os
import logging
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for

# Configure logging
logger = logging.getLogger(__name__)

# Create UI blueprint
ui_bp = Blueprint('ui', __name__)

# Create Dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Create routes blueprint
routes_bp = Blueprint('routes', __name__)

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
    app.register_blueprint(routes_bp)
    logger.info("UI routes initialized")
    logger.info("Cyberpunk dashboard routes initialized")
    logger.info("Routes initialized")

@routes_bp.route('/')
def index():
    """Dashboard home page"""
    return render_template('index.html')

@routes_bp.route('/memory')
def memory():
    """Memory management page"""
    return render_template('memory.html')

@routes_bp.route('/visualization')
def visualization():
    """Visualization page"""
    return render_template('visualization.html')

@routes_bp.route('/chat')
def chat():
    """Chat interface page"""
    return render_template('chat.html')

@routes_bp.route('/wallet')
def wallet():
    """Wallet integration page"""
    return render_template('wallet.html')

@routes_bp.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html') 