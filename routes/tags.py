from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


from app import *
from models.db import *

def init_app(app):

    """
    KCRUD: Kanban Tag CRUD Operations
    This module provides REST API endpoints for managing Kanban tags.
    """
    @app.route('/api/tags', methods=['GET'])
    def get_tags():
        tags = Tag.query.all()
        return jsonify([tag.to_dict() for tag in tags])

    @app.route('/api/tags/<int:tag_id>', methods=['GET'])
    def get_tag(tag_id):
        """Get a specific tag by ID."""
        try:
            tag = Tag.query.get_or_404(tag_id)
            return jsonify(tag.to_dict())
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 404

    @app.route('/api/tags', methods=['POST'])  # Corrigido: methods=['POST'] ao invés de methods['POST']
    def create_tag():
        try:
            data = request.json
            tag = Tag(name=data['name'], color=data.get('color', '#1a73e8'))
            db.session.add(tag)
            db.session.commit()
            return jsonify({"success": True, "tag": tag.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/tags/<int:tag_id>', methods=['PUT'])
    def update_tag(tag_id):
        try:
            tag = Tag.query.get_or_404(tag_id)
            data = request.json
            if 'name' in data:
                tag.name = data['name']
            if 'color' in data:
                tag.color = data['color']
            db.session.commit()
            return jsonify({"success": True, "tag": tag.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/tags/<int:tag_id>', methods=['DELETE'])  # Corrigido: methods=['DELETE'] ao invés de methods['DELETE']
    def delete_tag(tag_id):
        try:
            tag = Tag.query.get_or_404(tag_id)
            db.session.delete(tag)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
