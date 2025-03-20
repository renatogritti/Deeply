from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
from models.db import db, Channel, Message, Team
from auth.authorization import login_required

def init_app(app):
    @app.route('/messenger')
    @login_required
    def messenger():
        """Render messenger page with user data"""
        user_id = session.get('user_id')
        return render_template('messenger.html', user_id=user_id)

    @app.route('/api/channels', methods=['GET'])
    @login_required
    def get_channels():
        """Get all channels for current user"""
        user_id = session.get('user_id')
        user = Team.query.get(user_id)
        channels = user.channels
        return jsonify([channel.to_dict() for channel in channels])

    @app.route('/api/channels', methods=['POST'])
    @login_required
    def create_channel():
        """Create new channel"""
        data = request.json
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"success": False, "error": "User not authenticated"}), 401
        
        try:
            # Verifica se já existe um canal com este nome
            existing_channel = Channel.query.filter_by(name=data['name']).first()
            if existing_channel:
                return jsonify({"success": False, "error": "Channel name already exists"}), 400

            # Cria o novo canal
            new_channel = Channel(
                name=data['name'],
                description=data.get('description', ''),
                is_private=data.get('is_private', False),
                created_by=user_id
            )

            # Adiciona o criador como membro
            creator = Team.query.get(user_id)
            if creator:
                new_channel.members.append(creator)

            # Adiciona outros membros selecionados
            if 'member_ids' in data:
                for member_id in data['member_ids']:
                    member = Team.query.get(member_id)
                    if member and member.id != user_id:  # Evita duplicar o criador
                        new_channel.members.append(member)

            db.session.add(new_channel)
            db.session.commit()
            
            return jsonify({
                "success": True, 
                "channel": new_channel.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating channel: {str(e)}")  # Log do erro
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/channels/<int:channel_id>', methods=['GET'])
    @login_required
    def get_channel(channel_id):
        """Get channel details"""
        channel = Channel.query.get_or_404(channel_id)
        return jsonify(channel.to_dict())

    @app.route('/api/channels/<int:channel_id>', methods=['PUT'])
    @login_required
    def update_channel(channel_id):
        """Update channel"""
        user_id = session.get('user_id')
        channel = Channel.query.get_or_404(channel_id)
        
        # Verifica se o usuário é o criador ou membro do canal
        if channel.created_by != user_id and user_id not in [member.id for member in channel.members]:
            return jsonify({"success": False, "error": "Permission denied"}), 403
        
        try:
            data = request.json
            channel.name = data['name']
            channel.description = data.get('description', '')
            
            # Garante que o criador permaneça como membro
            creator = Team.query.get(channel.created_by)
            members = [creator] if creator else []
            
            # Atualiza outros membros
            for member_id in data['member_ids']:
                member = Team.query.get(member_id)
                if member and member.id != channel.created_by:  # Evita duplicar o criador
                    members.append(member)
            
            channel.members = members
            db.session.commit()
            return jsonify({"success": True, "channel": channel.to_dict()})
        except Exception as e:
            db.session.rollback()
            print(f"Error updating channel: {str(e)}")  # Log do erro
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/channels/<int:channel_id>', methods=['DELETE'])
    @login_required
    def delete_channel(channel_id):
        """Delete channel"""
        user_id = session.get('user_id')
        channel = Channel.query.get_or_404(channel_id)
        
        if channel.created_by != user_id:
            return jsonify({"success": False, "error": "Permission denied"}), 403
            
        try:
            db.session.delete(channel)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/channels/<int:channel_id>/messages', methods=['GET'])
    @login_required
    def get_messages(channel_id):
        """Get messages for a channel"""
        messages = Message.query.filter_by(channel_id=channel_id).order_by(Message.created_at).all()
        return jsonify([message.to_dict() for message in messages])

    @app.route('/api/messages', methods=['POST'])
    @login_required
    def create_message():
        """Create new message"""
        data = request.json
        user_id = session.get('user_id')
        
        try:
            # Verifica se o usuário tem acesso ao canal
            channel = Channel.query.get(data['channel_id'])
            if not channel or user_id not in [member.id for member in channel.members]:
                return jsonify({"success": False, "error": "Access denied"}), 403

            message = Message(
                content=data['content'],
                channel_id=data['channel_id'],
                user_id=user_id
            )
            db.session.add(message)
            db.session.commit()
            
            # Retorna a mensagem com os dados do usuário
            return jsonify({
                "success": True, 
                "message": {
                    **message.to_dict(),
                    "user_name": Team.query.get(user_id).name
                }
            })
        except Exception as e:
            db.session.rollback()
            print(f"Error creating message: {str(e)}")  # Log do erro
            return jsonify({"success": False, "error": str(e)}), 500
