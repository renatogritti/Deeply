from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


from app import *
from  models.db import *

def init_app(app):
    @app.route('/')
    def index():
        """
        Render the main Kanban board page.
        """
        cards = [card.to_dict() for card in KanbanCard.query.all()]  # Converte cards para dicionários
        teams = [team.to_dict() for team in Team.query.all()]        # Converte teams para dicionários
        tags = [tag.to_dict() for tag in Tag.query.all()]           # Converte tags para dicionários
        projects = [project.to_dict() for project in Project.query.all()]  # Converte projects para dicionários
        
        return render_template('kanban.html', cards=cards, teams=teams, tags=tags, projects=projects)

    @app.route('/projects')
    def projects():
        """Render the projects management page."""
        projects = Project.query.all()
        return render_template('projects.html', projects=projects)

    @app.route('/teams')
    def teams():
        """Render the teams management page."""
        teams = Team.query.all()
        return render_template('teams.html', teams=teams)

    @app.route('/tags')
    def tags():
        """Render the tags management page."""
        tags = Tag.query.all()
        return render_template('tags.html', tags=tags)

    @app.route('/share')
    def share():
        """Render the share management page."""
        return render_template('share.html')

