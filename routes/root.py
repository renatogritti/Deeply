from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
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
                session['is_admin'] = user.is_admin
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
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        
        if is_admin:
            # Admin vê todos os projetos
            projects = [project.to_dict() for project in Project.query.all()]
        else:
            # Usuários normais veem apenas projetos com acesso
            projects = [
                project.to_dict() for project in Project.query
                .join(project_access)
                .filter(project_access.c.team_id == user_id)
                .all()
            ]

        cards = [card.to_dict() for card in KanbanCard.query.all()]
        teams = [team.to_dict() for team in Team.query.all()]
        tags = [tag.to_dict() for tag in Tag.query.all()]
        
        return render_template('kanban.html', 
                             cards=cards, 
                             teams=teams, 
                             tags=tags, 
                             projects=projects,
                             user_id=user_id,
                             is_admin=is_admin)

    @app.route('/calendar')
    @login_required
    def calendar():
        """Render the calendar view page."""
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        project_id = request.args.get('projeto')  # Mudou de 'project' para 'projeto'
        
        # Filtra os projetos baseado nas permissões
        if is_admin:
            projects = Project.query.all()
        else:
            projects = Project.query\
                .join(project_access)\
                .filter(project_access.c.team_id == user_id)\
                .all()

        # Base query para os cards
        cards_query = KanbanCard.query

        # Aplica filtro de projeto se especificado
        if project_id:
            cards_query = cards_query.filter(KanbanCard.project_id == project_id)
            
        # Aplica filtro de acesso se não for admin
        if not is_admin:
            cards_query = cards_query.join(Project)\
                .join(project_access)\
                .filter(project_access.c.team_id == user_id)

        # Separa cards com e sem deadline
        cards_with_deadline = cards_query.filter(
            KanbanCard.deadline.isnot(None)
        ).order_by(KanbanCard.deadline).all()
        
        cards_without_deadline = cards_query.filter(
            KanbanCard.deadline.is_(None)
        ).all()
        
        return render_template('calendar.html',
                             cards_with_deadline=cards_with_deadline,
                             cards_without_deadline=cards_without_deadline,
                             projects=projects)

    @app.route('/api/calendar/cards')
    @login_required
    def get_calendar_cards():
        """Get cards for calendar view with optional project filter."""
        project_id = request.args.get('project_id')
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')

        query = KanbanCard.query

        if project_id:
            query = query.filter(KanbanCard.project_id == project_id)
        
        if not is_admin:
            # Filtra apenas cartões de projetos que o usuário tem acesso
            query = query.join(Project)\
                .join(project_access)\
                .filter(project_access.c.team_id == user_id)

        cards = query.all()
        return jsonify([card.to_dict() for card in cards])

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

