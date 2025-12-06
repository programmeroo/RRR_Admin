"""Admin blueprint module"""
from .admin_routes import admin_bp
from .workflow_routes import workflow_bp

blueprints = [admin_bp, workflow_bp]
