"""
Kanban Board Application

This module defines the database models for the Kanban Board application.
It includes models for Kanban cards, teams, tags, and projects.

"""


from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

# Adicione esta nova tabela de associação após as importações existentes
card_users = db.Table('card_users',
    db.Column('card_id', db.String(50), db.ForeignKey('kanban_card.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True)
)

# Nova tabela para controle de acesso aos projetos
project_access = db.Table('project_access',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
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

    # Novos campos para perfil
    pais = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    idioma = db.Column(db.String(20), default='pt-BR')
    fuso_horario = db.Column(db.String(50), default='America/Sao_Paulo')
    cargo = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    organizacao = db.Column(db.String(100))
    linkedin = db.Column(db.String(200))
    contexto_trabalho = db.Column(db.Text)
    foto = db.Column(db.String(200))  # Caminho para a foto
    is_admin = db.Column(db.Boolean, default=False)  # Novo flag para administrador
    project_access = db.relationship('Project', secondary='project_access', lazy='subquery',
                                   backref=db.backref('authorized_teams', lazy=True))

    def to_dict(self):
        """Convert team object to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,  # Incluído email no retorno
            'description': self.description,
            'pais': self.pais,
            'cidade': self.cidade,
            'telefone': self.telefone,
            'idioma': self.idioma,
            'fuso_horario': self.fuso_horario,
            'cargo': self.cargo,
            'departamento': self.departamento,
            'organizacao': self.organizacao,
            'linkedin': self.linkedin,
            'contexto_trabalho': self.contexto_trabalho,
            'foto': self.foto,
            'is_admin': self.is_admin,
            'project_access': [p.id for p in self.project_access]
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
    # Novos campos
    start_date = db.Column(db.DateTime, nullable=True)
    percentage = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text)
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
                'start_date': self.start_date.isoformat() if self.start_date else None,
                'percentage': self.percentage,
                'comments': self.comments,
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

class TodoList(db.Model):
    """Lista de tarefas do usuário"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)  # Para ordenação das listas
    user_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('TodoTask', backref='list', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'order': self.order,
            'tasks': [task.to_dict() for task in self.tasks]
        }

class TodoTask(db.Model):
    """Tarefas da lista"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(10), default='Media')  # Alta, Media, Baixa
    completed = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)  # Para ordenação dentro da lista
    list_id = db.Column(db.Integer, db.ForeignKey('todo_list.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'completed': self.completed,
            'order': self.order,
            'list_id': self.list_id
        }

class Channel(db.Model):
    """Canal de comunicação"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    members = db.relationship('Team', secondary='channel_members', lazy='subquery',
                            backref=db.backref('channels', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'members': [member.to_dict() for member in self.members]
        }

class Message(db.Model):
    """Mensagens nos canais"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Adiciona relacionamento com o usuário
    user = db.relationship('Team', backref='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'user_name': self.user.name,  # Agora podemos acessar o nome do usuário diretamente
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Tabela de associação entre canais e membros
channel_members = db.Table('channel_members',
    db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True)
)

class PomodoroLog(db.Model):
    """Registros do Pomodoro Timer"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # duração em segundos
    timer_type = db.Column(db.String(10), nullable=False)  # 'work' ou 'break'
    completed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """Convert log object to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration': self.duration,
            'timer_type': self.timer_type,
            'completed': self.completed
        }

class Kudos(db.Model):
    """Kudos entre usuários"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # reconhecimento, premio, mensagem
    type = db.Column(db.String(50), nullable=False)      # trabalho_equipe, inovacao, ajuda
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('Team', foreign_keys=[sender_id], backref='sent_kudos')
    receiver = db.relationship('Team', foreign_keys=[receiver_id], backref='received_kudos')
    comments = db.relationship('KudosComment', backref='kudo', lazy='dynamic')
    reactions = db.relationship('KudosReaction', backref='kudo', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender.to_dict(),
            'receiver': self.receiver.to_dict(),
            'category': self.category,
            'type': self.type,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'comments': [comment.to_dict() for comment in self.comments],
            'reactions': [reaction.to_dict() for reaction in self.reactions]
        }

class KudosComment(db.Model):
    """Comentários em Kudos"""
    id = db.Column(db.Integer, primary_key=True)
    kudo_id = db.Column(db.Integer, db.ForeignKey('kudos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('kudos_comment.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('Team', backref='kudos_comments')
    replies = db.relationship('KudosComment', backref=db.backref('parent', remote_side=[id]))

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'user': self.user.to_dict(),
            'replies': [reply.to_dict() for reply in self.replies]
        }

class KudosReaction(db.Model):
    """Reações em Kudos"""
    id = db.Column(db.Integer, primary_key=True)
    kudo_id = db.Column(db.Integer, db.ForeignKey('kudos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # like, heart
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('Team', backref='kudos_reactions')

    def to_dict(self):
        return {
            'id': self.id,
            'reaction_type': self.reaction_type,
            'user': self.user.to_dict()
        }
