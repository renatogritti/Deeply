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
    @app.route('/docs')
    @login_required
    def docs():
        """Render the documents page."""
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

