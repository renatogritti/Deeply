from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
from flask import Blueprint, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import mimetypes
import shutil

from auth.authorization import login_required
from models.db import db, Project, Team, DocFolder, Document, DocumentVersion

docs_bp = Blueprint('docs', __name__, url_prefix='/docs')

# Base para armazenamento de arquivos
UPLOAD_BASE = 'Uploads'
if not os.path.exists(UPLOAD_BASE):
    os.makedirs(UPLOAD_BASE)

def get_project_path(project_id):
    return os.path.join(UPLOAD_BASE, 'Projects', str(project_id))

def init_app(app):
    app.register_blueprint(docs_bp)
    
    # Rota principal da página de documentos
    @app.route('/docs')
    @login_required
    def docs():
        """Render the documents page."""
        user_id = session.get('user_id')
        is_admin = session.get('is_admin', False)
        
        # Seleciona projetos acessíveis ao usuário
        if is_admin:
            projects = Project.query.all()
        else:
            projects = Project.query\
                .join(project_access)\
                .filter(project_access.c.team_id == user_id)\
                .all()
                
        return render_template('docs.html', projects=projects,is_admin=is_admin, user_id=user_id)
    
    # API para obter a estrutura de pastas e documentos de um projeto
    @app.route('/api/docs/structure')
    @login_required
    def get_docs_structure():
        """Obter a estrutura de pastas e documentos de um projeto"""
        project_id = request.args.get('project_id')
        folder_id = request.args.get('folder_id')
        
        if not project_id:
            return jsonify({"error": "ID do projeto é obrigatório"}), 400
            
        # Verifica acesso do usuário ao projeto
        user_id = session.get('user_id')
        is_admin = session.get('is_admin', False)
        
        if not is_admin:
            has_access = db.session.query(Project).filter(
                Project.id == project_id,
                Project.authorized_teams.any(id=user_id)
            ).first()
            
            if not has_access:
                return jsonify({"error": "Sem permissão para este projeto"}), 403
        
        # Cria o diretório do projeto se não existir
        project_path = get_project_path(project_id)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            
        # Busca pasta raiz do projeto se não foi especificado folder_id
        if folder_id:
            folder = DocFolder.query.get(folder_id)
            folders = DocFolder.query.filter_by(parent_id=folder_id).all()
            documents = Document.query.filter_by(folder_id=folder_id).all()
        else:
            # Cria pasta raiz se não existir
            root_folder = DocFolder.query.filter_by(project_id=project_id, parent_id=None).first()
            if not root_folder:
                root_folder = DocFolder(
                    name=f"Projeto {project_id}",
                    project_id=project_id,
                    parent_id=None,
                    created_by=user_id,
                    path=project_path
                )
                db.session.add(root_folder)
                db.session.commit()
                
            folders = DocFolder.query.filter_by(project_id=project_id, parent_id=None).all()
            documents = Document.query.filter_by(project_id=project_id, folder_id=root_folder.id).all()
            folder = root_folder
        
        # Constrói estrutura de pastas
        def build_folder_tree(folders_list):
            result = []
            for f in folders_list:
                result.append({
                    'id': f.id,
                    'name': f.name,
                    'description': f.description,
                    'created_by': f.creator.name,
                    'created_at': f.created_at.isoformat(),
                    'has_children': bool(DocFolder.query.filter_by(parent_id=f.id).first())
                })
            return result
            
        return jsonify({
            'folder': folder.to_dict() if folder else None,
            'subfolders': build_folder_tree(folders),
            'documents': [doc.to_dict() for doc in documents]
        })
        
    # API para criar nova pasta
    @app.route('/api/docs/folders', methods=['POST'])
    @login_required
    def create_folder():
        """Criar nova pasta"""
        data = request.json
        user_id = session.get('user_id')
        
        name = data.get('name', '').strip()
        description = data.get('description', '')
        project_id = data.get('project_id')
        parent_id = data.get('parent_id')
        
        if not name or not project_id:
            return jsonify({"error": "Nome e projeto são obrigatórios"}), 400
        
        # Verifica se a pasta pai existe
        parent = None
        if parent_id:
            parent = DocFolder.query.get(parent_id)
            if not parent:
                return jsonify({"error": "Pasta pai não encontrada"}), 404
                
            # Define o caminho da pasta
            folder_path = os.path.join(parent.path, secure_filename(name))
        else:
            # Pasta raiz no projeto
            parent_path = get_project_path(project_id)
            folder_path = os.path.join(parent_path, secure_filename(name))
        
        # Cria diretório físico
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Cria registro no banco de dados
        new_folder = DocFolder(
            name=name,
            description=description,
            project_id=project_id,
            parent_id=parent_id,
            created_by=user_id,
            path=folder_path
        )
        
        db.session.add(new_folder)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "folder": new_folder.to_dict()
        })
    
    # API para excluir pasta
    @app.route('/api/docs/folders/<int:folder_id>', methods=['DELETE'])
    @login_required
    def delete_folder(folder_id):
        """Excluir pasta e todo seu conteúdo"""
        folder = DocFolder.query.get_or_404(folder_id)
        
        # Verifica se não é a pasta raiz
        if folder.parent_id is None:
            return jsonify({"error": "Não é possível excluir a pasta raiz"}), 400
        
        try:
            # Remove diretório físico
            if os.path.exists(folder.path):
                shutil.rmtree(folder.path)
                
            # Remove registro do banco
            db.session.delete(folder)
            db.session.commit()
            
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    
    # API para criar um novo documento
    @app.route('/api/docs/documents', methods=['POST'])
    @login_required
    def create_document():
        """Criar novo documento com primeira versão"""
        try:
            user_id = session.get('user_id')
            
            # Verifica se foi enviado um arquivo
            if 'file' not in request.files:
                return jsonify({"error": "Nenhum arquivo enviado"}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "Nome do arquivo vazio"}), 400
            
            # Dados do formulário
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '')
            folder_id = request.form.get('folder_id')
            project_id = request.form.get('project_id')
            
            if not name or not folder_id or not project_id:
                return jsonify({"error": "Informações incompletas"}), 400
                
            # Busca a pasta
            folder = DocFolder.query.get(folder_id)
            if not folder:
                return jsonify({"error": "Pasta não encontrada"}), 404
            
            # Cria o documento
            new_doc = Document(
                name=name,
                description=description,
                folder_id=folder_id,
                project_id=project_id,
                created_by=user_id
            )
            
            db.session.add(new_doc)
            db.session.flush()  # Obtém ID sem commit
            
            # Cria diretório para o documento
            doc_dir = os.path.join(folder.path, f"doc_{new_doc.id}")
            os.makedirs(doc_dir, exist_ok=True)
                
            # Salva o arquivo com nome seguro
            filename = secure_filename(file.filename)
            file_path = os.path.join(doc_dir, f"1_{filename}")  # Versão 1
            
            # Garante que o arquivo seja salvo corretamente
            file.save(file_path)
            
            if not os.path.exists(file_path):
                raise Exception("Falha ao salvar o arquivo")
            
            # Cria a primeira versão
            file_size = os.path.getsize(file_path)
            file_type = mimetypes.guess_type(filename)[0]
            
            new_version = DocumentVersion(
                document_id=new_doc.id,
                version_number=1,
                file_path=file_path,
                file_name=filename,
                file_size=file_size,
                file_type=file_type,
                change_description="Versão inicial",
                uploaded_by=user_id
            )
            
            db.session.add(new_version)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "document": new_doc.to_dict()
            })

        except Exception as e:
            print(f"Erro ao criar documento: {str(e)}")  # Log do erro
            db.session.rollback()
            if os.path.exists(doc_dir):
                shutil.rmtree(doc_dir)  # Limpa arquivos em caso de erro
            return jsonify({"error": f"Erro ao criar documento: {str(e)}"}), 500
    
    # API para enviar nova versão de documento
    @app.route('/api/docs/documents/<int:doc_id>/versions', methods=['POST'])
    @login_required
    def add_document_version(doc_id):
        """Adicionar nova versão a um documento existente"""
        user_id = session.get('user_id')
        
        # Verifica se o documento existe
        document = Document.query.get_or_404(doc_id)
        
        # Verifica se foi enviado um arquivo
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nome do arquivo vazio"}), 400
        
        # Descrição da mudança
        change_description = request.form.get('change_description', '').strip()
        
        try:
            # Determina o número da próxima versão
            next_version = 1
            if document.versions:
                next_version = max([v.version_number for v in document.versions]) + 1
            
            # Cria diretório para o documento se não existir
            folder = DocFolder.query.get(document.folder_id)
            doc_dir = os.path.join(folder.path, f"doc_{document.id}")
            if not os.path.exists(doc_dir):
                os.makedirs(doc_dir)
                
            # Salva o arquivo
            filename = secure_filename(file.filename)
            file_path = os.path.join(doc_dir, f"{next_version}_{filename}")
            file.save(file_path)
            
            # Cria a nova versão
            file_size = os.path.getsize(file_path)
            file_type = mimetypes.guess_type(file_path)[0]
            
            new_version = DocumentVersion(
                document_id=document.id,
                version_number=next_version,
                file_path=file_path,
                file_name=filename,
                file_size=file_size,
                file_type=file_type,
                change_description=change_description,
                uploaded_by=user_id
            )
            
            # Atualiza a data de modificação do documento
            document.updated_at = datetime.utcnow()
            
            db.session.add(new_version)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "version": new_version.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    
    # API para obter detalhes de um documento
    @app.route('/api/docs/documents/<int:doc_id>')
    @login_required
    def get_document(doc_id):
        """Obter detalhes de um documento, opcionalmente com histórico de versões"""
        include_versions = request.args.get('include_versions', 'false').lower() == 'true'
        
        document = Document.query.get_or_404(doc_id)
        
        return jsonify(document.to_dict(include_versions=include_versions))
    
    # API para baixar uma versão específica
    @app.route('/api/docs/documents/<int:doc_id>/versions/<int:version_id>/download')
    @login_required
    def download_version(doc_id, version_id):
        """Download de versão específica"""
        version = DocumentVersion.query.filter_by(
            id=version_id, 
            document_id=doc_id
        ).first_or_404()
        
        # Verifica se o arquivo existe
        if not os.path.exists(version.file_path):
            return jsonify({"error": "Arquivo não encontrado"}), 404
        
        return send_file(
            version.file_path, 
            download_name=version.file_name,
            as_attachment=True
        )
        
    # API para baixar a versão mais recente
    @app.route('/api/docs/documents/<int:doc_id>/download')
    @login_required
    def download_latest_version(doc_id):
        """Download da versão mais recente do documento"""
        document = Document.query.get_or_404(doc_id)
        
        if not document.versions:
            return jsonify({"error": "Documento não tem versões"}), 404
        
        version = document.versions[0]  # Versão mais recente
        
        # Verifica se o arquivo existe
        if not os.path.exists(version.file_path):
            return jsonify({"error": "Arquivo não encontrado"}), 404
        
        return send_file(
            version.file_path, 
            download_name=version.file_name,
            as_attachment=True
        )
        
    # API para excluir um documento
    @app.route('/api/docs/documents/<int:doc_id>', methods=['DELETE'])
    @login_required
    def delete_document(doc_id):
        """Excluir documento e todas suas versões"""
        document = Document.query.get_or_404(doc_id)
        
        try:
            # Identifica diretório do documento
            folder = DocFolder.query.get(document.folder_id)
            doc_dir = os.path.join(folder.path, f"doc_{document.id}")
            
            # Remove diretório físico se existir
            if os.path.exists(doc_dir):
                shutil.rmtree(doc_dir)
                
            # Remove registro do banco
            db.session.delete(document)
            db.session.commit()
            
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    
    @app.route('/logout')
    def logout():
        """Logout user and clear session"""
        session.clear()
        return redirect(url_for('index'))

