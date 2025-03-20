"""
Kanban Board Application

Config File for the Kanban Board Application.
This file contains configuration settings for the Kanban Board application.
It includes database connection details, email configuration, and other settings.

"""

from flask import Flask
from flask_session import Session

app = Flask(__name__)
app.secret_key = "uma_chave_muito_segura_aqui"  # Troque por uma chave segura!

# Configuração do Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração da Sessão
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuração do Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu-email@gmail.com'  # Substitua pelo seu email
app.config['MAIL_PASSWORD'] = 'sua-senha-de-app'     # Substitua pela sua senha de app do Gmail

# Configuração de Cookies
app.config['SESSION_COOKIE_NAME'] = 'kanban_session'
app.config['SESSION_COOKIE_SECURE'] = True  # Apenas via HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Apenas acessível via HTTP, não JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Proteção contra CSRF

# Configuração da AI
OLLAMA_API_BASE = "http://127.0.0.1:11434"
OLLAMA_MODEL = "gemma3:4b"  # Alterado para Gemma 3B gemma3:1b
