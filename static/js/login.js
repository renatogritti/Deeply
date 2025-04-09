document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Limpar mensagem de erro anterior
    document.getElementById('errorMessage').textContent = '';

    fetch('/validate_login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Resposta do servidor:', data); // Log para diagnóstico
        
        if (data.success) {
            // Redirecionar para o assistente AI com parâmetro de login
            window.location.replace('/ai?acao=login');
        } else {
            document.getElementById('errorMessage').textContent = 'Usuário ou senha inválidos';
        }
    })
    .catch(error => {
        console.error('Erro no login:', error);
        document.getElementById('errorMessage').textContent = 'Erro na conexão. Tente novamente.';
    });
});
