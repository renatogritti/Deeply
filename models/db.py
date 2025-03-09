"""
Kanban Board Application

This module defines the database models for the Kanban Board application.
It includes models for Kanban cards, teams, tags, and projects.

"""


from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import *
import hashlib

db = SQLAlchemy(app)

# Adicione esta nova tabela de associação após as importações existentes
card_users = db.Table('card_users',
    db.Column('card_id', db.String(50), db.ForeignKey('kanban_card.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True)
)

class Team(db.Model):
    """
    Team Model
    
    Represents a team in the Kanban board application.
    Teams can have multiple cards assigned to them.
    
    Attributes:
        id (int): Primary key
        name (str): Team name, must be unique
        description (str): Team description
        created_at (datetime): Team creation timestamp
        email (str): Team email, must be unique
        password_hash (str): Hashed password for the team
        cards (relationship): Relationship with KanbanCard model
    """
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Adicionado campo email
    password_hash = db.Column(db.String(256))  # Adicionado campo password_hash
    cards = db.relationship('KanbanCard', backref='team', lazy=True)

    def to_dict(self):
        """Convert team object to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,  # Incluído email no retorno
            'description': self.description
        }
    
    def verify_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado"""
        provided_hash = hashlib.sha256(password.encode()).hexdigest()
        return provided_hash == self.password_hash

class Project(db.Model):
    """
    Project Model
    
    Represents a project/board in the Kanban application.
    Each project can have multiple cards.
    
    Attributes:
        id (int): Primary key
        name (str): Project name, must be unique
        description (str): Project description
        created_at (datetime): Project creation timestamp
        cards (relationship): Relationship with KanbanCard model
    """
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cards = db.relationship('KanbanCard', backref='project', lazy=True)
    phases = db.relationship('Phase', backref='project', lazy=True, 
                           order_by="Phase.order",
                           cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'phases': [phase.to_dict() for phase in self.phases]
        }

class Tag(db.Model):
    """
    Tag Model
    
    Represents a tag that can be applied to cards
    
    Attributes:
        id (int): Primary key
        name (str): Tag name, must be unique
        color (str): Color code for the tag
        created_at (datetime): Tag creation timestamp
    """
    
    id = db.Column(db.Integer, primary_key=True)  # Corrigido aqui: removido o espaço entre primary e key
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=False, default="#1a73e8")  # Format: #RRGGBB
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

# Card-Tag association table
card_tags = db.Table('card_tags',
    db.Column('card_id', db.String(50), db.ForeignKey('kanban_card.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Phase(db.Model):
    """
    Phase Model
    
    Represents a phase/column in a project's Kanban board
    
    Attributes:
        id (int): Primary key
        name (str): Phase name
        order (int): Order of the phase in the project
        project_id (int): Foreign key to Project model
        created_at (datetime): Phase creation timestamp
    """
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'project_id': self.project_id
        }

class KanbanCard(db.Model):
    """
    KanbanCard Model
    
    Represents a card on the Kanban board.
    Cards can be assigned to teams and moved between columns.
    
    Attributes:
        id (str): Primary key, unique identifier
        title (str): Card title
        description (str): Card description
        tempo (str): Time estimate for the card
        deadline (DateTime): Optional deadline for the card
        team_id (int): Foreign key to Team model
        project_id (int): Foreign key to Project model
        created_at (datetime): Card creation timestamp
    """
    
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tempo = db.Column(db.String(20), nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)  # Add this line
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))  # Mantenha para compatibilidade
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('Tag', secondary=card_tags, lazy='subquery',
                         backref=db.backref('cards', lazy=True))
    users = db.relationship('Team', secondary=card_users, lazy='subquery',
                          backref=db.backref('assigned_cards', lazy=True))
    phase_id = db.Column(db.Integer, db.ForeignKey('phase.id'), nullable=False)
    phase = db.relationship('Phase', backref='cards', lazy=True)

    def to_dict(self):
        """Convert card object to dictionary for JSON serialization."""
        try:
            return {
                'id': self.id,
                'title': self.title,
                'description': self.description,
                'tempo': self.tempo,
                'deadline': self.deadline.isoformat() if self.deadline else None,  # Add this line
                'phase_id': self.phase_id,
                'team_id': self.team_id,
                'project_id': self.project_id,
                'team': {'id': self.team.id, 'name': self.team.name} if self.team else None,
                'tags': [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in self.tags],
                'users': [{'id': user.id, 'name': user.name} for user in self.users],
            }
        except Exception as e:
            print(f"Error serializing card {self.id}: {str(e)}")
            return {}

class Share(db.Model):
    """
    Share Model
    
    Represents a share record in the Kanban board application.
    
    Attributes:
        id (int): Primary key
        email (str): Email address of the recipient
        message (str): Optional message included with the share
        created_at (datetime): Share creation timestamp
    """
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }
