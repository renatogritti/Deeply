from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g, Blueprint
from auth.authorization import login_required
from models.db import db, Kudos, KudosComment, KudosReaction, Team
from datetime import datetime, timedelta

kudos_bp = Blueprint('kudos', __name__, url_prefix='/kudos')

def init_app(app):
    app.register_blueprint(kudos_bp)

@kudos_bp.route('/')
@login_required
def kudos_page():
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    if not user_id:
        return redirect(url_for('index'))
    return render_template('kudos.html',is_admin=is_admin)

@kudos_bp.route('/api/kudos', methods=['GET'])
@login_required
def get_kudos():
    kudos = Kudos.query.order_by(Kudos.created_at.desc()).all()
    return jsonify([kudo.to_dict() for kudo in kudos])

@kudos_bp.route('/api/kudos/remaining', methods=['GET'])
@login_required
def get_remaining_kudos():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_count = Kudos.query.filter(
        Kudos.sender_id == user_id,
        Kudos.created_at >= start_of_month
    ).count()
    
    remaining = max(0, 5 - monthly_count)
    return jsonify({
        'remaining': remaining,
        'total': 5,
        'used': monthly_count
    })

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
        
        # Validações fora da transação
        if user_id == data['receiver_id']:
            return jsonify({'error': 'Não é possível enviar kudos para si mesmo'}), 400
        
        if not Team.query.get(data['receiver_id']):
            return jsonify({'error': 'Destinatário não encontrado'}), 404
            
        # Verificações com lock
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_count = db.session.query(Kudos).filter(
            Kudos.sender_id == user_id,
            Kudos.created_at >= start_of_month
        ).count()
        
        if monthly_count >= 5:
            return jsonify({'error': 'Limite mensal de kudos atingido (máximo 5)'}), 400
            
        last_minute = datetime.utcnow() - timedelta(minutes=1)
        recent_duplicate = db.session.query(Kudos).filter(
            Kudos.sender_id == user_id,
            Kudos.receiver_id == data['receiver_id'],
            Kudos.created_at >= last_minute
        ).first()
        
        if recent_duplicate:
            return jsonify({'error': 'Você já enviou um kudo para este usuário nos últimos 60 segundos'}), 400
        
        # Criar novo kudo em uma única transação
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
