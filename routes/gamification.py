from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g, Blueprint
from auth.authorization import login_required
from models.db import db, PomodoroLog, Team
from datetime import datetime, timedelta
from sqlalchemy import func, case

gamification_bp = Blueprint('gamification', __name__, url_prefix='/gamification')

def init_app(app):
    app.register_blueprint(gamification_bp)

@gamification_bp.route('/')
@login_required
def gamification_page():
    return render_template('gamification.html')

@gamification_bp.route('/api/stats/<period>')
@login_required
def get_stats(period):
    user_id = session.get('user_id')
    today = datetime.now()
    
    if period == 'week':
        start_date = today - timedelta(days=6)
    else:  # month
        start_date = today - timedelta(days=29)

    # Query para o gráfico
    stats = db.session.query(
        func.date(PomodoroLog.start_time).label('date'),
        func.sum(PomodoroLog.duration).label('total_duration')
    ).filter(
        PomodoroLog.user_id == user_id,
        PomodoroLog.timer_type == 'work'
    ).group_by(
        func.date(PomodoroLog.start_time)
    ).order_by(
        func.date(PomodoroLog.start_time)
    ).all()

    # Processamento do gráfico
    stats_dict = {str(stat.date): round(stat.total_duration / 60) for stat in stats}
    
    labels = []
    values = []
    current = start_date
    while current <= today:
        data_str = str(current.date())
        labels.append(current.strftime('%d/%m'))
        values.append(stats_dict.get(data_str, 0))
        current += timedelta(days=1)

    # Query do ranking
    ranking_query = db.session.query(
        PomodoroLog.user_id,
        func.sum(PomodoroLog.duration).label('total_duration')
    ).filter(
        PomodoroLog.timer_type == 'work'
    ).group_by(
        PomodoroLog.user_id
    ).order_by(
        func.sum(PomodoroLog.duration).desc()
    )

    ranking_results = ranking_query.all()
    ranking = []
    
    for rank in ranking_results:
        user = Team.query.get(rank.user_id)
        if user:
            minutes = round(rank.total_duration / 60)
            # Ofusca o nome se não for o usuário atual
            display_name = user.name if user.id == user_id else f"Usuário {len(ranking) + 1}"
            ranking.append({
                'id': user.id,
                'name': display_name,
                'minutes': minutes,
                'is_current_user': user.id == user_id
            })
    
    return jsonify({
        'labels': labels,
        'values': values,
        'ranking': ranking
    })
