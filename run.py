"""
Kanban Board Application

"""

from app import app
from routes import init_app
from models.db import db
import secrets
from datetime import timedelta

# Configurações de segurança
app.config.update(
    SECRET_KEY=secrets.token_hex(32),
    SESSION_COOKIE_SECURE=True,  # Requer HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Previne acesso via JavaScript
    SESSION_COOKIE_SAMESITE='Lax',  # Proteção contra CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)  # Tempo máximo da sessão
)

# Inicializa as rotas e o banco de dados
init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
