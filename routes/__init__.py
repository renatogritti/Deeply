from models.db import db
from routes import (
    root,
    teams,
    tags,
    projects,
    cards,
    todo,
    messenger,
    pomodoro,
    kudos,
    docs,
    gamification,
    ai  # Nova importação
)

def init_app(app):
    # Inicializa o banco de dados
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Registra as rotas
    root.init_app(app)
    teams.init_app(app)
    tags.init_app(app)
    projects.init_app(app)
    cards.init_app(app)
    todo.init_app(app)
    messenger.init_app(app)
    docs.init_app(app)
    pomodoro.init_app(app)
    kudos.init_app(app)  # Registra as rotas do kudos
    gamification.init_app(app)  # Registra as rotas de gamificação
    ai.init_app(app)  # Registra as rotas de AI

    return app