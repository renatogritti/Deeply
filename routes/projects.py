from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from openpyxl import Workbook, load_workbook
import os
from werkzeug.utils import secure_filename
import tempfile
import uuid  # Adicionar esta importação no topo do arquivo

from app import *
from models.db import *

def init_app(app):

    """
    KCRUD: Kanban User CRUD Operations
    This module provides REST API endpoints for managing Kanban users.
    """
    @app.route('/api/projects', methods=['GET'])  # Corrigido: methods=['GET'] ao invés de methods['GET']
    def get_projects():
        projects = Project.query.all()
        return jsonify([project.to_dict() for project in projects])

    @app.route('/api/projects', methods=['POST'])
    def create_project():
        """Create a new project with phases."""
        try:
            data = request.json
            
            # Validações
            if not data.get('name'):
                return jsonify({"success": False, "error": "Project name is required"}), 400
            
            if not data.get('phases') or len(data['phases']) == 0:
                return jsonify({"success": False, "error": "At least one phase is required"}), 400
                
            project = Project(
                name=data['name'],
                description=data.get('description', '')
            )
            
            # Adicionar fases do projeto
            for idx, phase_data in enumerate(data['phases']):
                if not phase_data.get('name'):
                    return jsonify({"success": False, "error": f"Phase {idx+1} name is required"}), 400
                    
                phase = Phase(
                    name=phase_data['name'],
                    order=idx,
                    project=project
                )
                db.session.add(phase)
                
            db.session.add(project)
            db.session.commit()
            return jsonify({"success": True, "project": project.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/projects/<int:project_id>', methods=['PUT'])
    def update_project(project_id):
        """Update project and its phases."""
        try:
            project = Project.query.get_or_404(project_id)
            data = request.json
            
            # Validações
            if 'name' in data and not data['name']:
                return jsonify({"success": False, "error": "Project name cannot be empty"}), 400
                
            if 'phases' in data and len(data['phases']) == 0:
                return jsonify({"success": False, "error": "At least one phase is required"}), 400
            
            # Atualizar dados básicos do projeto
            if 'name' in data:
                project.name = data['name']
            if 'description' in data:
                project.description = data['description']
                
            # Atualizar fases
            if 'phases' in data:
                # Primeiro, verifique se há cards em alguma fase
                cards_count = KanbanCard.query.filter_by(project_id=project_id).count()
                if cards_count > 0:
                    return jsonify({
                        "success": False, 
                        "error": "Cannot modify phases while there are cards in the project"
                    }), 400
                
                # Se não houver cards, pode atualizar as fases
                # Remover fases antigas
                for phase in project.phases:
                    db.session.delete(phase)
                
                # Adicionar novas fases
                for idx, phase_data in enumerate(data['phases']):
                    if not phase_data.get('name'):
                        return jsonify({"success": False, "error": f"Phase {idx+1} name is required"}), 400
                        
                    phase = Phase(
                        name=phase_data['name'],
                        order=idx,
                        project=project
                    )
                    db.session.add(phase)
            
            db.session.commit()
            return jsonify({"success": True, "project": project.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/projects/<int:project_id>/phases', methods=['GET'])
    def get_project_phases(project_id):
        try:
            project = Project.query.get_or_404(project_id)
            return jsonify([phase.to_dict() for phase in project.phases])
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 404

    @app.route('/api/projects/<int:project_id>', methods=['DELETE'])
    def delete_project(project_id):
        try:
            project = Project.query.get_or_404(project_id)
            db.session.delete(project)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    # Atualize ou adicione esta rota
    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        """Get a specific project by ID."""
        try:
            project = Project.query.get_or_404(project_id)
            return jsonify(project.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 404

    @app.route('/api/cards/phases/<int:project_id>', methods=['GET'])
    def get_phases_for_card(project_id):
        """Get phases for a specific project for card creation/editing."""
        try:
            project = Project.query.get_or_404(project_id)
            phases = [phase.to_dict() for phase in project.phases]
            return jsonify({"success": True, "phases": phases})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 404

    @app.route('/api/projects/<int:project_id>/export', methods=['GET'])
    def export_project(project_id):
        try:
            project = Project.query.get_or_404(project_id)
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Project Export"
            
            headers = ['Phase', 'Card Title', 'Description', 'Time', 'Deadline', 'Users', 'Tags']
            ws.append(headers)
            
            for phase in project.phases:
                for card in phase.cards:
                    users = ";".join([user.email for user in card.users])
                    tags = ";".join([tag.name for tag in card.tags])
                    deadline = card.deadline.strftime('%Y-%m-%d') if card.deadline else ''
                    
                    row = [
                        phase.name,
                        card.title,
                        card.description,
                        card.tempo,  # Alterado para usar o atributo 'tempo'
                        deadline,
                        users,
                        tags
                    ]
                    ws.append(row)
            
            # Ajustar largura das colunas
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Salvar temporariamente
            filename = f"project_export_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            wb.save(filepath)
            
            # Enviar arquivo
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/projects/<int:project_id>/import', methods=['POST'])
    def import_project(project_id):
        temp_log = None
        try:
            if 'file' not in request.files:
                return jsonify({"success": False, "error": "No file uploaded"}), 400
                
            file = request.files['file']
            if not file.filename.endswith('.xlsx'):
                return jsonify({"success": False, "error": "Invalid file format"}), 400

            project = Project.query.get_or_404(project_id)
            
            # Criar arquivo temporário para log de erros
            error_log = []
            temp_log = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
            
            try:
                wb = load_workbook(file)
                ws = wb.active
                headers = [cell.value for cell in ws[1]]
                
                with db.session.no_autoflush:
                    for row in ws.iter_rows(min_row=2):
                        try:
                            row_data = dict(zip(headers, [cell.value for cell in row]))
                            if not row_data['Card Title']:
                                continue
                            
                            # Validar fase
                            phase = next((p for p in project.phases if p.name == row_data['Phase']), None)
                            if not phase:
                                raise ValueError(f"Phase not found: {row_data['Phase']}")
                            
                            # Verificar se o card existe
                            card_title = row_data['Card Title'].strip()
                            existing_card = KanbanCard.query.filter_by(
                                project_id=project_id,
                                title=card_title
                            ).first()

                            # Preparar dados do card
                            try:
                                deadline = datetime.strptime(row_data['Deadline'], '%Y-%m-%d') if row_data['Deadline'] and row_data['Deadline'].strip() else None
                            except ValueError:
                                deadline = None

                            # Processar usuários e tags
                            users = []
                            if row_data['Users']:
                                for email in row_data['Users'].split(';'):
                                    user = Team.query.filter_by(email=email.strip()).first()
                                    if not user:
                                        raise ValueError(f"User not found: {email}")
                                    users.append(user)
                                    
                            tags = []
                            if row_data['Tags']:
                                for tag_name in row_data['Tags'].split(';'):
                                    tag = Tag.query.filter_by(name=tag_name.strip()).first()
                                    if not tag:
                                        raise ValueError(f"Tag not found: {tag_name}")
                                    tags.append(tag)

                            if existing_card:
                                # Atualizar card existente
                                existing_card.description = row_data['Description']
                                existing_card.tempo = row_data['Time']
                                existing_card.deadline = deadline
                                existing_card.phase_id = phase.id
                                existing_card.users = users
                                existing_card.tags = tags
                            else:
                                # Gerar ID único para o novo card
                                card_id = str(uuid.uuid4())
                                
                                # Criar novo card com ID gerado
                                new_card = KanbanCard(
                                    id=card_id,  # Adicionar o ID gerado
                                    project_id=project_id,
                                    phase_id=phase.id,
                                    title=card_title,
                                    description=row_data['Description'],
                                    tempo=row_data['Time'],
                                    deadline=deadline,
                                    users=users,
                                    tags=tags
                                )
                                db.session.add(new_card)
                            
                            db.session.flush()
                                
                        except Exception as e:
                            error_log.append(f"Error in row {row[0].row}: {str(e)}")

                    if error_log:
                        db.session.rollback()
                        for error in error_log:
                            temp_log.write(error + '\n')
                        temp_log.close()
                        return jsonify({"success": False, "error_log": True}), 400
                    
                    db.session.commit()
                    return jsonify({"success": True})
                    
            finally:
                wb.close()
                if temp_log and not temp_log.closed:
                    temp_log.close()
                if error_log:
                    session['error_log_path'] = temp_log.name
                
        except Exception as e:
            if temp_log and not temp_log.closed:
                temp_log.close()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/projects/<int:project_id>/error_log')
    def download_error_log(project_id):
        if 'error_log_path' not in session:
            return jsonify({"error": "No error log found"}), 404
            
        error_file = session['error_log_path']
        try:
            # Enviar o arquivo
            response = send_file(
                error_file,
                as_attachment=True,
                download_name=f"import_errors_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            # Adicionar callback para remover o arquivo após o envio
            @response.call_on_close
            def remove_file():
                try:
                    if os.path.exists(error_file):
                        os.unlink(error_file)
                except Exception as e:
                    print(f"Error removing temp file: {e}")
                finally:
                    session.pop('error_log_path', None)
                    
            return response
            
        except Exception as e:
            session.pop('error_log_path', None)
            return jsonify({"error": str(e)}), 500
