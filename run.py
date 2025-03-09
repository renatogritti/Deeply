"""
Kanban Board Application

"""

from app import *
from routes import *
from models.db import *
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

# Create database and tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
