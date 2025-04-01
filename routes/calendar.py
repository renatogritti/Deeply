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


def init_app(app):
    @app.route('/calendar')
    @login_required
    def calendar():
        """Render the calendar view page."""
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        
        if is_admin:
            # Admin vê todos os projetos
            projects = Project.query.all()
        else:
            # Usuários normais veem apenas projetos com acesso
            projects = Project.query\
                .join(project_access)\
                .filter(project_access.c.team_id == user_id)\
                .all()

        cards_with_deadline = KanbanCard.query.filter(
            KanbanCard.deadline.isnot(None)
        ).order_by(KanbanCard.deadline).all()
        
        cards_without_deadline = KanbanCard.query.filter(
            KanbanCard.deadline.is_(None)
        ).all()
        
        return render_template('calendar.html',
                             cards_with_deadline=cards_with_deadline,
                             cards_without_deadline=cards_without_deadline,
                             projects=projects)