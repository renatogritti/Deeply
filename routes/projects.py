from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


from config import *
from db import *

def init_app(app):

    """
    KCRUD: Kanban User CRUD Operations
    This module provides REST API endpoints for managing Kanban users.
    """
    @app.route('/api/projects', methods=['GET'])  # Corrigido: methods=['GET'] ao invés de methods['GET']
    def get_projects():
        projects = Project.query.all()
        return jsonify([project.to_dict() for project in projects])

    @app.route('/api/projects', methods=['POST'])
    def create_project():
        """Create a new project with phases."""
        try:
            data = request.json
            
            # Validações
            if not data.get('name'):
                return jsonify({"success": False, "error": "Project name is required"}), 400
            
            if not data.get('phases') or len(data['phases']) == 0:
                return jsonify({"success": False, "error": "At least one phase is required"}), 400
                
            project = Project(
                name=data['name'],
                description=data.get('description', '')
            )
            
            # Adicionar fases do projeto
            for idx, phase_data in enumerate(data['phases']):
                if not phase_data.get('name'):
                    return jsonify({"success": False, "error": f"Phase {idx+1} name is required"}), 400
                    
                phase = Phase(
                    name=phase_data['name'],
                    order=idx,
                    project=project
                )
                db.session.add(phase)
                
            db.session.add(project)
            db.session.commit()
            return jsonify({"success": True, "project": project.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/projects/<int:project_id>', methods=['PUT'])
    def update_project(project_id):
        """Update project and its phases."""
        try:
            project = Project.query.get_or_404(project_id)
            data = request.json
            
            # Validações
            if 'name' in data and not data['name']:
                return jsonify({"success": False, "error": "Project name cannot be empty"}), 400
                
            if 'phases' in data and len(data['phases']) == 0:
                return jsonify({"success": False, "error": "At least one phase is required"}), 400
            
            # Atualizar dados básicos do projeto
            if 'name' in data:
                project.name = data['name']
            if 'description' in data:
                project.description = data['description']
                
            # Atualizar fases
            if 'phases' in data:
                # Primeiro, verifique se há cards em alguma fase
                cards_count = KanbanCard.query.filter_by(project_id=project_id).count()
                if cards_count > 0:
                    return jsonify({
                        "success": False, 
                        "error": "Cannot modify phases while there are cards in the project"
                    }), 400
                
                # Se não houver cards, pode atualizar as fases
                # Remover fases antigas
                for phase in project.phases:
                    db.session.delete(phase)
                
                # Adicionar novas fases
                for idx, phase_data in enumerate(data['phases']):
                    if not phase_data.get('name'):
                        return jsonify({"success": False, "error": f"Phase {idx+1} name is required"}), 400
                        
                    phase = Phase(
                        name=phase_data['name'],
                        order=idx,
                        project=project
                    )
                    db.session.add(phase)
            
            db.session.commit()
            return jsonify({"success": True, "project": project.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/projects/<int:project_id>/phases', methods=['GET'])
    def get_project_phases(project_id):
        try:
            project = Project.query.get_or_404(project_id)
            return jsonify([phase.to_dict() for phase in project.phases])
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 404

    @app.route('/api/projects/<int:project_id>', methods=['DELETE'])
    def delete_project(project_id):
        try:
            project = Project.query.get_or_404(project_id)
            db.session.delete(project)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    # Atualize ou adicione esta rota
    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        """Get a specific project by ID."""
        try:
            project = Project.query.get_or_404(project_id)
            return jsonify(project.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 404

    @app.route('/api/cards/phases/<int:project_id>', methods=['GET'])
    def get_phases_for_card(project_id):
        """Get phases for a specific project for card creation/editing."""
        try:
            project = Project.query.get_or_404(project_id)
            phases = [phase.to_dict() for phase in project.phases]
            return jsonify({"success": True, "phases": phases})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 404
