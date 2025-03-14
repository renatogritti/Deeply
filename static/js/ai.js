let isProcessing = false;

// Adiciona mensagem de boas-vindas quando carregar a página
document.addEventListener('DOMContentLoaded', function() {
    const welcomeMessage = `Olá! Sou Deeply, seu assistente especializado em trabalho colaborativo e produtividade. 
    Posso ajudar com:
    • Métodos de trabalho profundo (Deep Work)
    • Práticas ágeis e colaborativas
    • Reconhecimento social (Kudos)
    • Produtividade em equipe
    
    Como posso ajudar você hoje?`;
    
    addMessage(welcomeMessage, 'ai');
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
    
    isProcessing = true;
    
    fetch('/ai/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }) // Corrigido: 'prompt' para 'message'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        addMessage(data.response, 'ai');
    })
    .catch(error => {
        addMessage('Erro ao processar mensagem: ' + error.message, 'error');
        console.error('Erro detalhado:', error); // Adicionado log detalhado
    })
    .finally(() => {
        isProcessing = false;
    });
}

function addMessage(content, type) {
    const messages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    // Use innerHTML em vez de textContent para interpretar HTML
    messageDiv.innerHTML = content.replace(/\n/g, '<br>');
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}
