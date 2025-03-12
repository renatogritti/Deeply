from flask import request, jsonify, session
from models.db import db, PomodoroLog
from datetime import datetime
from auth.authorization import login_required

def init_app(app):
    @app.route('/api/pomodoro/log', methods=['POST'])
    @login_required
    def log_pomodoro():
        try:
            data = request.json
            # Usando 'usuario' ao invés de 'user_id' para corresponder ao nome da sessão
            user_id = session.get('usuario')
            
            if not user_id:
                raise ValueError('User not authenticated')
                
            log = PomodoroLog(
                user_id=user_id,
                start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')),
                duration=data['duration'],
                timer_type=data['timer_type'],
                completed=data['completed']
            )
            
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'success': True, 'log': log.to_dict()})
        except Exception as e:
            db.session.rollback()
            print(f"Error logging pomodoro: {str(e)}") # Debug log
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/pomodoro/logs', methods=['GET'])
    @login_required
    def get_pomodoro_logs():
        try:
            user_id = session.get('user_id')
            logs = PomodoroLog.query.filter_by(user_id=user_id).order_by(PomodoroLog.start_time.desc()).all()
            return jsonify({'success': True, 'logs': [log.to_dict() for log in logs]})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
