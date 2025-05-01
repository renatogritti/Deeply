let isProcessing = false;

// Adiciona mensagem de boas-vindas ou realiza análise do projeto ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    const params = new URLSearchParams(window.location.search);
    acao = params.get('acao');
    if (acao === 'analise') {
        try {
            const jsonData = atob(params.get('json'));
            const projectData = JSON.parse(jsonData);
            
            // Criar um prompt aprimorado
            const prompt = `Por favor, faça uma análise detalhada do board do Kanban do projeto "${projectData.projectName}" com as seguintes considerações especiais:

1. TAREFAS ATRASADAS: Identifique e destaque tarefas com prazo vencido (deadline anterior a hoje) e não concluídas (percentual < 100%). Para cada atividade atrasada:
   - Indique o título da atividade, responsável e quanto está atrasada
   - Sugira um plano de ação específico com passos concretos
   - Recomende um replanejamento com nova deadline estimada
   - Proponha ações para mitigar atrasos semelhantes no futuro

2. TAREFAS MUITO GRANDES: Analise tarefas com estimativas acima de 16 horas, recomendando que sejam divididas em atividades menores conforme as boas práticas ágeis.

3. GARGALOS DE RECURSOS: Identifique membros da equipe que estão com mais de 3 tarefas em andamento simultaneamente, o que pode indicar sobrecarga.

4. ANÁLISE DO WIP (Work in Progress): Avalie a distribuição de tarefas entre as colunas e identifique possíveis gargalos no fluxo de trabalho.

5. RECOMENDAÇÕES: Com base nessas análises, forneça recomendações práticas para melhorar o andamento do projeto.

Dados do board: ${jsonData}`;
            
            // Adicionamos apenas uma mensagem, não duas
            // addMessage("Analisando o Projeto...", 'ai');
            
            fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: prompt })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                // Remove a mensagem "Analisando o Projeto..."
                const messages = document.getElementById('chat-messages');
                messages.removeChild(messages.lastChild);
                
                // Adiciona a resposta da análise
                addMessage(data.response, 'ai');
            })
            .catch(error => {
                console.error('Erro:', error);
                const messages = document.getElementById('chat-messages');
                if (messages.lastChild) {
                    messages.removeChild(messages.lastChild);
                }
                addMessage('Erro ao processar análise: ' + error.message, 'error');
            });

        } catch (error) {
            console.error('Erro ao processar JSON:', error);
            addMessage('Erro ao processar dados do board para análise.', 'error');
        }
    } else if (acao === 'report') {
        // ...resto do código
    } else if (acao !== 'login') {
        const welcomeMessage = `Olá! Sou Deeply, seu assistente especializado em trabalho colaborativo. 
        Posso ajudar com:
        • Métodos de trabalho profundo (Deep Work)
        • Práticas ágeis e colaborativas
        • Reconhecimento social (Kudos)
        
        Como posso ajudar você hoje?`;
        
        addMessage(welcomeMessage, 'ai');
    }
});

document.getElementById('userInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    if (isProcessing) return;

    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage(message, 'user');
    input.value = '';
    
    // Adiciona mensagem de loading
    const loadingMessage = `<div class="loading-dots">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    </div>`;
    addMessage(loadingMessage, 'ai');
    
    isProcessing = true;
    
    fetch('/ai/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        // Remove mensagem de loading
        const messages = document.getElementById('chat-messages');
        messages.removeChild(messages.lastChild);
        
        // Cria elemento para a resposta
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        messages.appendChild(messageDiv);
        
        // Inicia a animação de digitação
        typeWriter(data.response, messageDiv, 0, 30);
    })
    .catch(error => {
        const messages = document.getElementById('chat-messages');
        messages.removeChild(messages.lastChild);
        addMessage('Erro ao processar mensagem: ' + error.message, 'error');
        console.error('Erro detalhado:', error);
    })
    .finally(() => {
        isProcessing = false;
    });
}

function typeWriter(text, element, index, speed) {
    if (index < text.length) {
        // Se encontrar uma tag HTML, pula até o fechamento
        if (text.charAt(index) === '<') {
            const endIndex = text.indexOf('>', index);
            element.innerHTML = text.substring(0, endIndex + 1);
            index = endIndex + 1;
        } else {
            element.innerHTML = text.substring(0, index + 1);
            index++;
        }
        
        // Ajusta velocidade para pausas naturais (reduzidas para 1/3)
        let currentSpeed = speed;
        if (text.charAt(index - 1) === '.') {
            currentSpeed = speed * 1.6; // Era 5, agora 1.6
        } else if (text.charAt(index - 1) === ',') {
            currentSpeed = speed; // Era 3, agora 1
        }
        
        // Mantém o scroll atualizado durante a digitação
        const messages = document.getElementById('chat-messages');
        messages.scrollTop = messages.scrollHeight;
        
        setTimeout(() => typeWriter(text, element, index, speed), currentSpeed);
    }
}

// Atualiza a animação de loading para o caso de análise
function addMessage(content, type) {
    const messages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const params = new URLSearchParams(window.location.search);
    
    if (type === 'ai' && content === 'Analisando o Projeto...') {
        messageDiv.innerHTML = `
            <div class="analyzing-message">
                <div class="analyzing-text">${content}</div>
                <div class="analyzing-animation">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>`;
        messages.appendChild(messageDiv);
    } else if (type === 'ai' && !content.includes('loading-dots')) {
        messageDiv.innerHTML = '';
        messages.appendChild(messageDiv);
        typeWriter(content, messageDiv, 0, 10);
    } else {
        messageDiv.innerHTML = content;
        messages.appendChild(messageDiv);
    }
    
    messages.scrollTop = messages.scrollHeight;
}
