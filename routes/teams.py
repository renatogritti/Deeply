from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import hashlib


from app import *
from models.db import *

def init_app(app):

    """
    KCRUD: Kanban Team CRUD Operations
    This module provides REST API endpoints for managing Kanban teams.
    """
    @app.route('/api/teams', methods=['GET'])
    def get_teams():
        teams = Team.query.all()
        return jsonify([team.to_dict() for team in teams])

    @app.route('/api/teams/<int:team_id>', methods=['GET'])
    def get_team(team_id):
        """
        Get a specific team by ID.
        
        Args:
            team_id: Integer identifier of the team
        
        Returns:
            JSON: Team data or error message
        """
        try:
            team = Team.query.get_or_404(team_id)
            return jsonify(team.to_dict())
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 404

    @app.route('/api/teams', methods=['POST'])
    def create_team():
        try:
            data = request.json
            default_password = 'admin'
            password_hash = hashlib.sha256(default_password.encode()).hexdigest()
            
            team = Team(
                name=data['name'],
                email=data.get('email', ''),
                description=data.get('description', ''),
                password_hash=password_hash,
                is_admin=data.get('is_admin', False)
            )

            if 'project_access' in data:
                projects = Project.query.filter(Project.id.in_(data['project_access'])).all()
                team.project_access = projects

            db.session.add(team)
            db.session.commit()
            return jsonify({"success": True, "team": team.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/teams/<int:team_id>', methods=['PUT'])
    def update_team(team_id):
        try:
            team = Team.query.get_or_404(team_id)
            data = request.json
            
            if 'name' in data:
                team.name = data['name']
            if 'description' in data:
                team.description = data['description']
            if 'is_admin' in data:
                team.is_admin = data['is_admin']
            if 'project_access' in data:
                projects = Project.query.filter(Project.id.in_(data['project_access'])).all()
                team.project_access = projects
                
            db.session.commit()
            return jsonify({"success": True, "team": team.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/teams/<int:team_id>', methods=['DELETE'])  # Corrigido aqui: methods=['DELETE'] ao invés de methods['DELETE']
    def delete_team(team_id):
        try:
            team = Team.query.get_or_404(team_id)
            # Update cards to remove team association
            KanbanCard.query.filter_by(team_id=team_id).update({"team_id": None})
            
            # Remova também as associações de usuários dos cards
            for card in team.assigned_cards:
                card.users.remove(team)
                
            db.session.delete(team)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

