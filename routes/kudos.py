from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from auth.authorization import login_required
from models.db import db, Kudos, KudosComment, KudosReaction, Team
from datetime import datetime

kudos_bp = Blueprint('kudos', __name__, url_prefix='/kudos')

def init_app(app):
    app.register_blueprint(kudos_bp)

@kudos_bp.route('/')
@login_required
def kudos_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    return render_template('kudos.html')

@kudos_bp.route('/api/kudos', methods=['GET'])
@login_required
def get_kudos():
    kudos = Kudos.query.order_by(Kudos.created_at.desc()).all()
    return jsonify([kudo.to_dict() for kudo in kudos])

@kudos_bp.route('/api/kudos', methods=['POST'])
@login_required
def create_kudo():
    try:
        data = request.json
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        if not all(k in data for k in ['receiver_id', 'category', 'type', 'message']):
            return jsonify({'error': 'Dados incompletos'}), 400
        
        # Verificar limite mensal
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        monthly_count = Kudos.query.filter(
            Kudos.sender_id == user_id,
            Kudos.created_at >= start_of_month
        ).count()
        
        if monthly_count >= 5:
            return jsonify({'error': 'Limite mensal de kudos atingido'}), 400
        
        new_kudo = Kudos(
            sender_id=user_id,
            receiver_id=data['receiver_id'],
            category=data['category'],
            type=data['type'],
            message=data['message']
        )
        
        db.session.add(new_kudo)
        db.session.commit()
        
        return jsonify(new_kudo.to_dict())
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar kudo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kudos_bp.route('/api/kudos/<int:kudo_id>/comment', methods=['POST'])
@login_required
def add_comment(kudo_id):
    data = request.json
    user_id = session.get('user_id')
    
    try:
        comment = KudosComment(
            kudo_id=kudo_id,
            user_id=user_id,
            content=data['content'],
            parent_id=data.get('parent_id')
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify(comment.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kudos_bp.route('/api/kudos/<int:kudo_id>/react', methods=['POST'])
@login_required
def add_reaction(kudo_id):
    data = request.json
    user_id = session.get('user_id')
    
    try:
        existing = KudosReaction.query.filter_by(
            kudo_id=kudo_id,
            user_id=user_id
        ).first()
        
        if existing:
            if existing.reaction_type == data['reaction_type']:
                db.session.delete(existing)
            else:
                existing.reaction_type = data['reaction_type']
        else:
            reaction = KudosReaction(
                kudo_id=kudo_id,
                user_id=user_id,
                reaction_type=data['reaction_type']
            )
            db.session.add(reaction)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
