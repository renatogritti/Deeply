from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


from app import *
from models.db import *

def init_app(app):

    """
    KCRUD: Kanban Card CRUD Operations
    This module provides REST API endpoints for managing Kanban cards.
    """

    @app.route('/api/cards', methods=['GET'])
    def get_cards():
        """Get all Kanban cards or filter by project_id."""
        project_id = request.args.get('project_id')
        
        if project_id:
            cards = KanbanCard.query.filter_by(project_id=project_id).all()
        else:
            cards = KanbanCard.query.all()
        
        return jsonify([card.to_dict() for card in cards])

    @app.route('/api/cards', methods=['POST'])
    def create_card():
        """
        Create a new Kanban card.
        
        Expected JSON payload:
            id: string
            title: string
            description: string
            tempo: string
            phase_id: integer
            team_id: integer (optional)
        
        Returns:
            JSON: Success status and created card data
        """
        try:
            data = request.json
            
            # Convert deadline string to datetime if provided
            deadline = None
            if data.get('deadline'):
                try:
                    deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
                except ValueError:
                    return jsonify({"success": False, "error": "Invalid deadline format"}), 400
                
            card = KanbanCard(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                tempo=data['tempo'],
                deadline=deadline,
                phase_id=data['phase_id'],  # Use phase_id
                team_id=data.get('team_id'),
                project_id=data['project_id']
            )
            
            # Add tags if provided
            if 'tag_ids' in data:
                tags = Tag.query.filter(Tag.id.in_(data['tag_ids'])).all()
                card.tags = tags

            # Add selected users
            if 'user_ids' in data:
                users = Team.query.filter(Team.id.in_(data['user_ids'])).all()
                card.users = users

            db.session.add(card)
            db.session.commit()
            return jsonify({"success": True, "card": card.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/cards/<string:card_id>', methods=['PUT'])
    def update_card(card_id):
        """
        Update an existing Kanban card.
        
        Args:
            card_id: String identifier of the card to update
        
        Expected JSON payload (all fields optional):
            title: string
            description: string
            tempo: string
            team_id: integer
        
        Returns:
            JSON: Success status and updated card data
        """
        try:
            card = KanbanCard.query.get_or_404(card_id)
            data = request.json
            
            if 'title' in data:
                card.title = data['title']
            if 'description' in data:
                card.description = data['description']
            if 'tempo' in data:
                card.tempo = data['tempo']
            if 'deadline' in data:
                # Convert deadline string to datetime if provided
                card.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d') if data['deadline'] else None
            if 'phase_id' in data:  # Atualizado: usar phase_id ao invés de column
                card.phase_id = data['phase_id']
            if 'team_id' in data:
                card.team_id = data['team_id']
            if 'tag_ids' in data:
                card.tags = Tag.query.filter(Tag.id.in_(data['tag_ids'])).all()
            if 'user_ids' in data:
                users = Team.query.filter(Team.id.in_(data['user_ids'])).all()
                card.users = users
                
            db.session.commit()
            return jsonify({"success": True, "card": card.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/cards/<string:card_id>', methods=['GET'])
    def get_card(card_id):
        try:
            card = KanbanCard.query.get_or_404(card_id)
            card_data = card.to_dict()
            card_data['users'] = [user.to_dict() for user in card.users]  # Adiciona explicitamente os usuários
            return jsonify(card_data)
        except Exception as e:
            print(f"Error getting card {card_id}: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 404

    @app.route('/api/cards/<string:card_id>', methods=['DELETE'])
    def delete_card(card_id):
        try:
            card = KanbanCard.query.get_or_404(card_id)
            db.session.delete(card)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400