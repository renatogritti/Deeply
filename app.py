"""
Kanban Board Application

This module implements a Kanban board with team management functionality using Flask.
It provides REST API endpoints for managing cards and teams, and uses SQLite as the database.
"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import json
from config import *
from db import *

mail = Mail(app)

# Create database and tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """
    Render the main Kanban board page.
    """
    cards = [card.to_dict() for card in KanbanCard.query.all()]  # Converte cards para dicionários
    teams = [team.to_dict() for team in Team.query.all()]        # Converte teams para dicionários
    tags = [tag.to_dict() for tag in Tag.query.all()]           # Converte tags para dicionários
    projects = [project.to_dict() for project in Project.query.all()]  # Converte projects para dicionários
    
    return render_template('kanban.html', cards=cards, teams=teams, tags=tags, projects=projects)


"""
KCRUD: Kanban Card CRUD Operations
This module provides REST API endpoints for managing Kanban cards.
"""

@app.route('/api/cards', methods=['GET'])
def get_cards():
    """
    Get all Kanban cards.
    
    Returns:
        JSON: List of all cards in the system
    """
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
        column: string
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
            deadline=deadline,  # Add this line
            column=data['column'],
            team_id=data.get('team_id'),  # Mantenha para compatibilidade
            project_id=data['project_id']  # Adicione esta linha
        )
        
        # Add tags if provided
        if 'tag_ids' in data:
            tags = Tag.query.filter(Tag.id.in_(data['tag_ids'])).all()
            card.tags = tags

        # Adicione os usuários selecionados
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
        column: string
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
        if 'column' in data:
            card.column = data['column']
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
        return jsonify(card.to_dict())
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
        team = Team(
            name=data['name'],
            description=data.get('description', '')
        )
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

@app.route('/api/tags', methods=['POST'])
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

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    try:
        tag = Tag.query.get_or_404(tag_id)
        db.session.delete(tag)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400







"""
KCRUD: Kanban User CRUD Operations
This module provides REST API endpoints for managing Kanban users.
"""
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.json
        project = Project(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({"success": True, "project": project.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        data = request.json
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        db.session.commit()
        return jsonify({"success": True, "project": project.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    

"""
share_kanban: Compartilhar o quadro Kanban
Esta rota permite compartilhar o quadro Kanban com outro usuário.
Método: POST
Parâmetros de entrada:
- email: O email do usuário que deseja compartilhar o quadro.
"""

@app.route('/api/share', methods=['POST'])
def share_kanban():
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({"success": False, "error": "Email é obrigatório"}), 400

        # Captura o estado atual do quadro
        cards = KanbanCard.query.all()
        cards_data = [card.to_dict() for card in cards]
        
        # Cria o email
        msg = Message(
            subject='Kanban Board Compartilhado',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        
        # Cria o conteúdo do email
        board_summary = "\n".join([
            f"Card: {card['title']}\n"
            f"Status: {card['column']}\n"
            f"Descrição: {card['description']}\n"
            f"-------------------"
            for card in cards_data
        ])
        
        msg.body = f"""
        Olá!
        
        Alguém compartilhou um quadro Kanban com você.
        
        Resumo do quadro:
        
        {board_summary}
        
        Acesse o quadro em: http://seu-dominio/
        
        Atenciosamente,
        Equipe Kanban
        """
        
        mail.send(msg)
        return jsonify({"success": True, "message": "Email enviado com sucesso!"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
