from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g, Blueprint
import requests
from app import OLLAMA_API_BASE, OLLAMA_MODEL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from auth.authorization import login_required
import re

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
    # Recebe os parâmetros da URL
    projeto_id = request.args.get('projeto')
    acao = request.args.get('acao')
    json_data = request.args.get('json')
    
    return render_template('ai.html', projeto_id=projeto_id, acao=acao, json_data=json_data)

@ai_bp.route('/chat', methods=['POST'])
@login_required 
def chat():
    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        response = http.post(
            f"{OLLAMA_API_BASE}/api/generate",  # Alterado para generate em vez de chat
            json={
                "model": OLLAMA_MODEL,
                "prompt": message,
                "system": """Instruções:
- Voce e Deeply, um assistente especializado em trabalho colaborativo, agilidade empresarial, social kudos e deep work.
Seu foco e ajudar equipes a trabalharem melhor juntas, reconhecer conquistas e manter a produtividade profunda.
- Responda sempre em português do Brasil
- Seja direto e objetivo
- Use frases curtas
- Evite introduções desnecessárias
- Use tópicos quando apropriado
- Forneça exemplos práticos quando solicitado
- Foque no essencial""",
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
            bot_response = response_data.get('response', '').strip()
            
            if not bot_response:
                return jsonify({'error': 'Resposta vazia do modelo'}), 500
                
            formatted_response = format_response(bot_response)
            return jsonify({'response': formatted_response})
            
        return jsonify({'error': f"Erro na API: {response.status_code}"}), 500
            
    except Exception as e:
        print(f"Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500