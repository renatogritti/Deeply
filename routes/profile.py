from flask import Blueprint, render_template, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
import os
import hashlib
from models.db import db, Team
from auth.authorization import login_required

app = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_project_param(url):
    """Adiciona o parâmetro do projeto à URL se existir na query string"""
    project_id = request.args.get('projeto')
    if project_id:
        return f"{url}?projeto={project_id}"
    return url

def init_app(app):
    @app.route('/profile')
    @login_required
    def profile():
        user = Team.query.filter_by(email=session['usuario']).first()
        return render_template('profile.html', user=user, add_project_param=add_project_param)

    @app.route('/api/profile', methods=['PUT'])
    @login_required
    def update_profile():
        try:
            user = Team.query.filter_by(email=session['usuario']).first()
            data = request.json

            user.name = data.get('name', user.name)
            user.pais = data.get('pais')
            user.cidade = data.get('cidade')
            user.telefone = data.get('telefone')
            user.idioma = data.get('idioma')
            user.fuso_horario = data.get('fuso_horario')
            user.cargo = data.get('cargo')
            user.departamento = data.get('departamento')
            user.organizacao = data.get('organizacao')
            user.linkedin = data.get('linkedin')
            user.contexto_trabalho = data.get('contexto_trabalho')

            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)})

    @app.route('/api/profile/password', methods=['PUT'])
    @login_required
    def change_password():
        try:
            user = Team.query.filter_by(email=session['usuario']).first()
            data = request.json

            current_password = data.get('current_password')
            new_password = data.get('new_password')

            if not user.verify_password(current_password):
                return jsonify({"success": False, "message": "Senha atual incorreta"})

            user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            db.session.commit()

            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)})

    @app.route('/api/profile/photo', methods=['POST'])
    @login_required
    def upload_photo():
        try:
            if 'photo' not in request.files:
                return jsonify({"success": False, "message": "Nenhum arquivo enviado"})

            file = request.files['photo']
            if file.filename == '':
                return jsonify({"success": False, "message": "Nenhum arquivo selecionado"})

            if file and allowed_file(file.filename):
                filename = secure_filename(f"profile_{session['user_id']}_{file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profile_photos')
                
                # Criar diretório se não existir
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                # Atualizar caminho da foto no banco de dados
                user = Team.query.filter_by(email=session['usuario']).first()
                user.foto = f'/static/uploads/profile_photos/{filename}'
                db.session.commit()

                return jsonify({
                    "success": True,
                    "photo_url": user.foto
                })

            return jsonify({"success": False, "message": "Tipo de arquivo não permitido"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)})
