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

