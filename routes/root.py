from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import hashlib, secrets
from functools import wraps

from auth.authorization import login_required  # Importa o decorador de autenticação

from app import *
from models.db import *

# Dicionário para controlar tentativas de login
login_attempts = {}
MAX_ATTEMPTS = 3
BLOCK_TIME = 300  # 5 minutos em segundos

def check_brute_force(ip):
    """Verifica tentativas de força bruta"""
    current_time = datetime.now().timestamp()
    if ip in login_attempts:
        attempts, blocked_until = login_attempts[ip]
        if blocked_until and current_time < blocked_until:
            return False
        if attempts >= MAX_ATTEMPTS:
            login_attempts[ip] = (attempts, current_time + BLOCK_TIME)
            return False
    return True

load_dotenv()

def regenerate_session():
    """Regenera a sessão de forma segura"""
    old_session = dict(session)
    session.clear()
    session.update(old_session)
    session.modified = True

def init_app(app):
    @app.before_request
    def check_session_timeout():
        if 'usuario' in session:
            last_activity = session.get('last_activity', 0)
            now = datetime.now().timestamp()
            
            if now - last_activity > 1800:  # 30 minutos
                session.clear()
                return redirect(url_for('index'))
            
            session['last_activity'] = now

    @app.route('/')
    def index():
        """Render the login page"""
        return render_template('login.html')

    @app.route('/validate_login', methods=['POST'])
    def validate_login():
        """Validate login credentials"""
        ip = request.remote_addr
        
        if not check_brute_force(ip):
            return jsonify({
                "success": False, 
                "message": "Muitas tentativas. Tente novamente em 5 minutos."
            }), 429

        data = request.json

        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"success": False, "message": "Dados inválidos"}), 400

        # Primeiro tenta login como admin master
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        if (data['username'] == os.getenv('ADMIN_USER') and 
            password_hash == os.getenv('ADMIN_PASSWORD_HASH')):
            
            if ip in login_attempts:
                del login_attempts[ip]
            
            regenerate_session()
            session['usuario'] = 'admin'
            session['csrf_token'] = secrets.token_hex(32)
            session['last_activity'] = datetime.now().timestamp()
            
            return jsonify({"success": True})
        
        # Se não for admin, tenta login como usuário normal
        try:
            user = Team.query.filter_by(email=data['username']).first()
            
            if user and user.verify_password(data['password']):
                if ip in login_attempts:
                    del login_attempts[ip]
                
                regenerate_session()
                session['usuario'] = user.email
                session['user_id'] = user.id
                session['csrf_token'] = secrets.token_hex(32)
                session['last_activity'] = datetime.now().timestamp()
                
                return jsonify({"success": True})
        except Exception as e:
            print(f"Erro ao verificar usuário: {str(e)}")
            db.session.rollback()  # Adiciona rollback em caso de erro
            return jsonify({"success": False, "message": f"Erro ao verificar usuário: {str(e)}"}), 500

        # Incrementa contador de tentativas
        attempts, _ = login_attempts.get(ip, (0, None))
        login_attempts[ip] = (attempts + 1, None)
        
        return jsonify({"success": False, "message": "Usuário ou senha inválidos"}), 401

    @app.route('/kanban')
    @login_required
    def kanban():
        """Render the main Kanban board page."""
        cards = [card.to_dict() for card in KanbanCard.query.all()]
        teams = [team.to_dict() for team in Team.query.all()]
        tags = [tag.to_dict() for tag in Tag.query.all()]
        projects = [project.to_dict() for project in Project.query.all()]
        
        return render_template('kanban.html', cards=cards, teams=teams, tags=tags, projects=projects)

    @app.route('/projects')
    @login_required
    def projects():
        """Render the projects management page."""
        projects = Project.query.all()
        return render_template('projects.html', projects=projects)

    @app.route('/teams')
    @login_required
    def teams():
        """Render the teams management page."""
        teams = Team.query.all()
        return render_template('teams.html', teams=teams)

    @app.route('/tags')
    @login_required
    def tags():
        """Render the tags management page."""
        tags = Tag.query.all()
        return render_template('tags.html', tags=tags)

    @app.route('/share')
    @login_required
    def share():
        """Render the share management page."""
        return render_template('share.html')

    @app.route('/calendar')
    @login_required
    def calendar():
        """Render the calendar view page."""
        cards_with_deadline = KanbanCard.query.filter(
            KanbanCard.deadline.isnot(None)
        ).order_by(KanbanCard.deadline).all()
        
        cards_without_deadline = KanbanCard.query.filter(
            KanbanCard.deadline.is_(None)
        ).all()
        
        projects = Project.query.all()
        
        return render_template('calendar.html',
                             cards_with_deadline=cards_with_deadline,
                             cards_without_deadline=cards_without_deadline,
                             projects=projects)

    @app.route('/docs')
    @login_required
    def docs():
        """Render the documents page."""
        projects = Project.query.all()
        return render_template('docs.html', projects=projects)

    @app.route('/api/docs/<project_id>/structure')
    @login_required
    def get_docs_structure(project_id):
        """Get the document structure for a project."""
        import os
        
        base_path = f'Docs/Projects/{project_id}'
        folder_path = request.args.get('folder', '')
        
        # Define o caminho atual para listagem de arquivos
        current_path = os.path.join(base_path, folder_path) if folder_path else base_path
        
        # Cria diretório se não existir
        if not os.path.exists(current_path):
            os.makedirs(current_path)
        
        # Lista arquivos do diretório atual
        files = []
        if os.path.exists(current_path):
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isfile(item_path):
                    files.append({
                        'name': item,
                        'path': item_path
                    })
        
        # Escaneia toda a estrutura de pastas do projeto
        def scan_folders(path, relative_path=''):
            folders = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    relative_item = os.path.join(relative_path, item) if relative_path else item
                    folders.append({
                        'name': item,
                        'path': relative_item,
                        'subfolders': scan_folders(item_path, relative_item)
                    })
            return folders

        folders = scan_folders(base_path) if os.path.exists(base_path) else []
        
        return jsonify({
            'folders': folders,
            'files': files
        })

    @app.route('/api/docs/upload', methods=['POST'])
    @login_required
    def upload_docs():
        """Upload documents."""
        files = request.files.getlist('files[]')
        path = request.form.get('path')
        
        for file in files:
            file.save(os.path.join(path, file.filename))
        
        return jsonify({'success': True})

    @app.route('/api/docs/download')
    @login_required
    def download_doc():
        """Download a document."""
        path = request.args.get('path')
        return send_file(path, as_attachment=True)

    @app.route('/api/docs/folder', methods=['POST'])
    @login_required
    def create_folder():
        """Create a new folder."""
        data = request.json
        path = os.path.join(data['path'], data['name'])
        
        if not os.path.exists(path):
            os.makedirs(path)
        
        return jsonify({'success': True})

    @app.route('/api/docs/file', methods=['DELETE'])
    @login_required
    def delete_file():
        """Delete a file."""
        path = request.json['path']
        os.remove(path)
        return jsonify({'success': True})

    @app.route('/logout')
    def logout():
        """Logout user and clear session"""
        session.clear()
        return redirect(url_for('index'))

