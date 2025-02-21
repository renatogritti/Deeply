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

@app.route('/projects')
def projects():
    """Render the projects management page."""
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)

@app.route('/teams')
def teams():
    """Render the teams management page."""
    teams = Team.query.all()
    return render_template('teams.html', teams=teams)

@app.route('/tags')
def tags():
    """Render the tags management page."""
    tags = Tag.query.all()
    return render_template('tags.html', tags=tags)

@app.route('/share')
def share():
    """Render the share management page."""
    return render_template('share.html')

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
        message = data.get('message', '')
        
        if not email:
            return jsonify({"success": False, "error": "Email é obrigatório"}), 400

        # Salva o registro de compartilhamento
        share = Share(email=email, message=message)
        db.session.add(share)
        
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
            f"Descrição: {card['description']}\n"
            f"-------------------"
            for card in cards_data
        ])
        
        if message:
            board_summary = f"Mensagem: {message}\n\n{board_summary}"
        
        msg.body = f"""
        Olá!
        
        Alguém compartilhou um quadro Kanban com você.
        
        {board_summary}
        
        Acesse o quadro em: http://seu-dominio/
        
        Atenciosamente,
        Equipe Kanban
        """
        
        mail.send(msg)
        db.session.commit()
        return jsonify({"success": True, "message": "Email enviado com sucesso!"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/shares', methods=['GET'])
def get_shares():
    """Get all shares history"""
    try:
        shares = Share.query.order_by(Share.created_at.desc()).all()
        return jsonify([share.to_dict() for share in shares])
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/share/<int:share_id>/resend', methods=['POST'])
def resend_share(share_id):
    try:
        share = Share.query.get_or_404(share_id)
        
        # Reenviar o email
        msg = Message(
            subject='Kanban Board Compartilhado (Reenvio)',
            sender=app.config['MAIL_USERNAME'],
            recipients=[share.email]
        )
        
        # Captura o estado atual do quadro
        cards = KanbanCard.query.all()
        cards_data = [card.to_dict() for card in cards]
        
        # Cria o conteúdo do email
        board_summary = "\n".join([
            f"Card: {card['title']}\n"
            f"Descrição: {card['description']}\n"
            f"-------------------"
            for card in cards_data
        ])
        
        if share.message:
            board_summary = f"Mensagem: {share.message}\n\n{board_summary}"
        
        msg.body = f"""
        Olá!
        
        Este é um reenvio do compartilhamento do quadro Kanban.
        
        {board_summary}
        
        Acesse o quadro em: http://seu-dominio/
        
        Atenciosamente,
        Equipe Kanban
        """
        
        mail.send(msg)
        return jsonify({"success": True, "message": "Share resent successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/share/<int:share_id>', methods=['DELETE'])
def revoke_share(share_id):
    try:
        share = Share.query.get_or_404(share_id)
        db.session.delete(share)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
