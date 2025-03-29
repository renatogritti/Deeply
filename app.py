"""
Kanban Board Application

Config File for the Kanban Board Application.
This file contains configuration settings for the Kanban Board application.
It includes database connection details, email configuration, and other settings.

"""

import os
from flask import Flask, request, g, session
from flask_session import Session
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do UPLOAD_FOLDER
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "uma_chave_muito_segura_aqui")

# Configuração do Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI", 'sqlite:///kanban.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração da Sessão
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuração do Email
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", 'seu-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", 'sua-senha-de-app')

# Configuração de Cookies
app.config['SESSION_COOKIE_NAME'] = 'kanban_session'
app.config['SESSION_COOKIE_SECURE'] = True  # Apenas via HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Apenas acessível via HTTP, não JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Proteção contra CSRF

# Configuração da AI - Modelo Local Ollama
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

# Configuração da AI - Anthropic Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

# Configuração do Modelo AI a ser usado
# Opções: "local" ou "anthropic"
AI_MODEL_TYPE = os.getenv("AI_MODEL_TYPE", "local")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.context_processor
def utility_processor():
    def get_current_project():
        # Tenta obter da URL, depois da sessão
        projeto_id = request.args.get('projeto') or session.get('projeto_id')
        return projeto_id
        
    def add_project_param(url):
        projeto_id = get_current_project()
        if not projeto_id:
            return url
        if '?' in url:
            return f"{url}&projeto={projeto_id}"
        return f"{url}?projeto={projeto_id}"
    
    return dict(get_current_project=get_current_project, 
               add_project_param=add_project_param)

@app.before_request
def before_request():
    # Pega o projeto da URL
    projeto_id = request.args.get('projeto')
    
    # Se existe projeto na URL, atualiza a sessão
    if projeto_id:
        session['projeto_id'] = projeto_id
    # Se não existe na URL mas existe na sessão, mantém o da sessão
    elif 'projeto_id' in session:
        g.projeto_id = session['projeto_id']
    else:
        g.projeto_id = None

def create_app():
    app = Flask(__name__)
    
    # Configurações básicas
    app.secret_key = os.getenv("SECRET_KEY", "uma_chave_muito_segura_aqui")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI", 'sqlite:///kanban.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensões
    Session(app)
    
    # Registrar blueprints e outras configurações
    from routes import projects, ai, kanban
    projects.init_app(app)
    ai.init_app(app)
    kanban.init_app(app)
    
    return app
