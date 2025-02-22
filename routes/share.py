import mailbox
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import json


from app import *
from models.db import *

mail = Mail(app)

def init_app(app):


    """
    share_kanban: Compartilhar o quadro Kanban
    Esta rota permite compartilhar o quadro Kanban com outro usuário.
    Método: POST
    Parâmetros de entrada:
    - email: O email do usuário que deseja compartilhar o quadro.
    """

    @app.route('/api/share', methods=['POST'])
    def share_kanban():
        try:
            data = request.json
            email = data.get('email')
            message = data.get('message', '')
            
            if not email:
                return jsonify({"success": False, "error": "Email é obrigatório"}), 400

            # Salva o registro de compartilhamento
            share = Share(email=email, message=message)
            db.session.add(share)
            
            # Captura o estado atual do quadro
            cards = KanbanCard.query.all()
            cards_data = [card.to_dict() for card in cards]
            
            # Cria o email
            msg = Message(
                subject='Kanban Board Compartilhado',
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            
            # Cria o conteúdo do email
            board_summary = "\n".join([
                f"Card: {card['title']}\n"
                f"Descrição: {card['description']}\n"
                f"-------------------"
                for card in cards_data
            ])
            
            if message:
                board_summary = f"Mensagem: {message}\n\n{board_summary}"
            
            msg.body = f"""
            Olá!
            
            Alguém compartilhou um quadro Kanban com você.
            
            {board_summary}
            
            Acesse o quadro em: http://seu-dominio/
            
            Atenciosamente,
            Equipe Kanban
            """
            
            mail.send(msg)
            db.session.commit()
            return jsonify({"success": True, "message": "Email enviado com sucesso!"})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/shares', methods=['GET'])
    def get_shares():
        """Get all shares history"""
        try:
            shares = Share.query.order_by(Share.created_at.desc()).all()
            return jsonify([share.to_dict() for share in shares])
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/share/<int:share_id>/resend', methods=['POST'])
    def resend_share(share_id):
        try:
            share = Share.query.get_or_404(share_id)
            
            # Reenviar o email
            msg = Message(
                subject='Kanban Board Compartilhado (Reenvio)',
                sender=app.config['MAIL_USERNAME'],
                recipients=[share.email]
            )
            
            # Captura o estado atual do quadro
            cards = KanbanCard.query.all()
            cards_data = [card.to_dict() for card in cards]
            
            # Cria o conteúdo do email
            board_summary = "\n".join([
                f"Card: {card['title']}\n"
                f"Descrição: {card['description']}\n"
                f"-------------------"
                for card in cards_data
            ])
            
            if share.message:
                board_summary = f"Mensagem: {share.message}\n\n{board_summary}"
            
            msg.body = f"""
            Olá!
            
            Este é um reenvio do compartilhamento do quadro Kanban.
            
            {board_summary}
            
            Acesse o quadro em: http://seu-dominio/
            
            Atenciosamente,
            Equipe Kanban
            """
            
            mail.send(msg)
            return jsonify({"success": True, "message": "Share resent successfully!"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route('/api/share/<int:share_id>', methods=['DELETE'])
    def revoke_share(share_id):
        try:
            share = Share.query.get_or_404(share_id)
            db.session.delete(share)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400