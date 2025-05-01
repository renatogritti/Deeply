from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g, Blueprint
import requests
import json
from app import (
    OLLAMA_API_BASE, OLLAMA_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_API_URL, ANTHROPIC_MODEL,
    AI_MODEL_TYPE
)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from auth.authorization import login_required
import re
from models.db import db, KanbanCard, Project, TodoList, TodoTask, Message, Channel, Kudos, Team, card_users
from datetime import datetime, timedelta
from sqlalchemy import func, case

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# Configuração de retry para requests
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)
http.mount("https://", adapter)

def format_response(text):
    # Formata blocos de código
    text = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="language-\1">\2</code></pre>', text, flags=re.DOTALL)
    
    # Formata texto em negrito
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Formata texto em itálico
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Converte quebras de linha em <br>
    text = text.replace('\n', '<br>')
    
    return text

def init_app(app):
    app.register_blueprint(ai_bp)

@ai_bp.route('/')
@login_required
def ai_page():
    is_admin = session.get('is_admin')
    # Recebe os parâmetros da URL
    projeto_id = request.args.get('projeto')
    acao = request.args.get('acao')
    json_data = request.args.get('json')
    
    return render_template('ai.html', projeto_id=projeto_id, acao=acao, json_data=json_data,is_admin=is_admin)

def get_response_from_local_model(message, system_prompt):
    """Obter resposta do modelo local Ollama"""
    try:
        response = http.post(
            f"{OLLAMA_API_BASE}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": message,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            },
            timeout=240
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get('response', '').strip()
        else:
            raise Exception(f"Erro na API Ollama: {response.status_code}")
    except Exception as e:
        raise Exception(f"Erro ao acessar modelo local: {str(e)}")

def get_response_from_anthropic(message, system_prompt):
    """Obter resposta do Claude Haiku da Anthropic"""
    if not ANTHROPIC_API_KEY:
        raise Exception("Chave da API Anthropic não configurada")
        
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": ANTHROPIC_MODEL,
            "messages": [
                {"role": "user", "content": message}
            ],
            "system": system_prompt,
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        response = http.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get('content', [{}])[0].get('text', '').strip()
        else:
            error_message = f"Erro na API Anthropic: {response.status_code}"
            try:
                error_details = response.json()
                error_message += f" - {json.dumps(error_details)}"
            except:
                pass
            raise Exception(error_message)
    except Exception as e:
        raise Exception(f"Erro ao acessar API Anthropic: {str(e)}")

@ai_bp.route('/chat', methods=['POST'])
@login_required 
def chat():
    try:
        data = request.json
        message = data.get('message')
        action = data.get('action')
        
        if not message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        # Se a ação for para obter resumo após login
        if action == "login_summary":
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Usuário não autenticado'}), 401
                
            # Busca o usuário
            user = Team.query.get(user_id)
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            
            # Data atual para filtrar cards
            current_date = datetime.now().date()
            
            # Busca cards diretamente da tabela KanbanCard
            cards = (KanbanCard.query
                    .join(card_users, KanbanCard.id == card_users.c.card_id)
                    .join(Project, KanbanCard.project_id == Project.id)  # Join com Project
                    .filter(
                        card_users.c.team_id == user_id,
                        KanbanCard.percentage < 100,
                        (KanbanCard.start_date == None) | (KanbanCard.start_date.cast(db.Date) <= current_date)
                    )
                    .order_by(Project.name, KanbanCard.deadline.asc())  # Ordena por projeto e deadline
                    .all())
            
            # Separa atividades atrasadas e não atrasadas
            overdue_cards = {}
            pending_cards = {}
            
            for card in cards:
                project = Project.query.get(card.project_id)
                project_name = project.name if project else "Projeto Desconhecido"
                
                card_data = {
                    "title": card.title,
                    "due_date": card.deadline.strftime('%d/%m/%Y') if card.deadline else "Sem prazo",
                    "percentage": card.percentage,
                    "description": card.description,
                    "days_overdue": None  # Inicializa campo para dias de atraso
                }
                
                # Verifica se está atrasado (deadline no passado e não concluído)
                is_overdue = False
                if card.deadline and card.percentage < 100:
                    is_overdue = card.deadline.date() < current_date
                    if is_overdue:
                        # Calcula dias de atraso
                        days_overdue = (current_date - card.deadline.date()).days
                        card_data["days_overdue"] = days_overdue
                
                # Adiciona ao dicionário apropriado
                if is_overdue:
                    if project_name not in overdue_cards:
                        overdue_cards[project_name] = []
                    overdue_cards[project_name].append(card_data)
                else:
                    if project_name not in pending_cards:
                        pending_cards[project_name] = []
                    pending_cards[project_name].append(card_data)
            
            # Ordena cards atrasados por dias de atraso (mais atrasados primeiro)
            for project in overdue_cards:
                overdue_cards[project] = sorted(
                    overdue_cards[project], 
                    key=lambda x: x.get("days_overdue", 0) or 0, 
                    reverse=True
                )
            
            # Busca TODOs do usuário
            todo_lists = TodoList.query.filter_by(user_id=user_id).all()
            todos_by_list = {}
            for todo_list in todo_lists:
                todos = TodoTask.query.filter_by(list_id=todo_list.id, completed=False).all()
                if todos:
                    todos_by_list[todo_list.name] = [{"title": todo.title} for todo in todos]
            
            # Busca mensagens recentes
            channels = user.channels
            messages = []
            for channel in channels:
                channel_messages = Message.query.filter_by(channel_id=channel.id).order_by(Message.created_at.desc()).limit(3).all()
                for msg in channel_messages:
                    sender = Team.query.get(msg.user_id)
                    messages.append({
                        "content": msg.content,
                        "sender": sender.name if sender else "Usuário Desconhecido",
                        "channel": channel.name,
                        "created_at": msg.created_at.strftime('%d/%m/%Y %H:%M')
                    })
            
            # Ordena as mensagens por data (mais recentes primeiro)
            messages.sort(key=lambda x: datetime.strptime(x["created_at"], '%d/%m/%Y %H:%M'), reverse=True)
            
            # Limita a 3 mensagens
            messages = messages[:3]
            
            # Busca kudos recentes
            kudos = Kudos.query.order_by(Kudos.created_at.desc()).limit(3).all()
            
            # Cria o resumo
            summary = {
                "user_name": user.name,
                "overdue_activities": {  # Nova seção para atividades atrasadas
                    "title": "Atividades atrasadas (PRIORIDADE)",
                    "projects": [
                        {
                            "name": project_name,
                            "cards": cards_list
                        } for project_name, cards_list in overdue_cards.items()
                    ]
                },
                "activities": {
                    "title": "Atividades pendentes no Kanban",
                    "projects": [
                        {
                            "name": project_name,
                            "cards": cards_list
                        } for project_name, cards_list in pending_cards.items()
                    ]
                },
                "todos": todos_by_list,
                "messages": messages,
                "kudos": [{"message": k.message, "category": k.category, "sender": k.sender.name, 
                          "receiver": k.receiver.name, "created_at": k.created_at.strftime('%d/%m/%Y')} for k in kudos]
            }
            
            # Atualiza o prompt para incluir a seção de atividades atrasadas
            prompt = f"""
O usuário {summary['user_name']} acabou de fazer login. Monte um resumo personalizado com as informações abaixo:

ATIVIDADES ATRASADAS (PRIORIDADE):
{json.dumps(summary['overdue_activities'], ensure_ascii=False, indent=2)}

ATIVIDADES PENDENTES NO KANBAN:
{json.dumps(summary['activities'], ensure_ascii=False, indent=2)}

TODOs PESSOAIS:
{json.dumps(summary['todos'], ensure_ascii=False, indent=2)}

MENSAGENS RECENTES:
{json.dumps(summary['messages'], ensure_ascii=False, indent=2)}

RECONHECIMENTOS RECENTES:
{json.dumps(summary['kudos'], ensure_ascii=False, indent=2)}

Formatação esperada:
- Saudação casual e personalizada (bom dia/tarde/noite + nome do usuário)

<div class="level-0 bullet-main"><a href='/kanban' class="alert-link">Atividades atrasadas (PRIORIDADE)</a></div>
<div class="level-1 bullet-sub">Projeto X</div>
<div class="level-2 bullet-item important">Card Y (atrasado há Z dias) - W% concluído</div>
<div class="level-3 bullet-action">⚠️ Estas atividades devem ser priorizadas e replanejadas junto à gestão.</div>

<div class="level-0 bullet-main"><a href='/kanban'>Atividades pendentes no Kanban</a></div>
<div class="level-1 bullet-sub">Projeto X</div>
<div class="level-2 bullet-item">Card Y (data de vencimento) - Z% concluído</div>

<div class="level-0 bullet-main"><a href='/todo'>TODOs pessoais</a></div>
<div class="level-1 bullet-sub">Lista X</div>
<div class="level-2 bullet-item">Item da lista</div>

<div class="level-0 bullet-main"><a href='/messenger'>Mensagens recentes</a></div>
<div class="level-2 bullet-item">Canal X: mensagem (enviada por Y)</div>

<div class="level-0 bullet-main"><a href='/kudos'>Reconhecimentos recentes</a></div>
<div class="level-2 bullet-item">De X para Y: mensagem</div>

Instruções:
- Use os caracteres especificados através das classes CSS
- Mantenha exatamente esta estrutura HTML e as classes
- Use linguagem casual e concisa
- Destaque atividades atrasadas com formatação em negrito e cor vermelha
- Se não houver atividades atrasadas, omita esta seção
- Adicione uma mensagem de alerta sobre a necessidade de priorizar e replanejar atividades atrasadas
"""

            system_prompt = """Instruções:
- Você é Deeply, um assistente especializado em trabalho colaborativo
- Responda sempre em português do Brasil
- Seja direto e objetivo com tom acolhedor mas conciso
- Mantenha o texto compacto e bem organizado
- Destaque com ênfase visual as atividades atrasadas (usando negrito e símbolos de alerta)
- Enfatize a importância de priorizar atividades atrasadas e conversar com a gestão
- Use apenas os links principais para cada seção
- Seja motivador mas breve
- Ajude o usuário a ter uma visão rápida do seu dia"""

            if AI_MODEL_TYPE.lower() == "anthropic":
                bot_response = get_response_from_anthropic(prompt, system_prompt)
            else:  # default: local
                bot_response = get_response_from_local_model(prompt, system_prompt)
                
            if not bot_response:
                return jsonify({'error': 'Resposta vazia do modelo'}), 500
                    
            formatted_response = format_response(bot_response)
            return jsonify({'response': formatted_response})
        
        # Caso normal, sem ação especial
        system_prompt = """Instruções:
- Voce e Deeply, um assistente especializado em trabalho colaborativo, agilidade empresarial, social kudos e deep work.
Seu foco e ajudar equipes a trabalharem melhor juntas, reconhecer conquistas e manter a produtividade profunda.
- Responda sempre em português do Brasil
- Seja direto e objetivo
- Use frases curtas
- Evite introduções desnecessárias
- Use tópicos quando apropriado
- Forneça exemplos práticos quando solicitado
- Foque no essencial"""

        if AI_MODEL_TYPE.lower() == "anthropic":
            bot_response = get_response_from_anthropic(message, system_prompt)
        else:  # default: local
            bot_response = get_response_from_local_model(message, system_prompt)
            
        if not bot_response:
            return jsonify({'error': 'Resposta vazia do modelo'}), 500
                
        formatted_response = format_response(bot_response)
        return jsonify({'response': formatted_response})
            
    except Exception as e:
        print(f"Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500