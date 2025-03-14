let currentChart = null;

document.addEventListener('DOMContentLoaded', function() {
    loadStats('week'); // Carrega estatísticas semanais por padrão
});

function switchPeriod(period) {
    // Atualiza botões
    document.querySelectorAll('.period-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    loadStats(period);
}

function loadStats(period) {
    console.log('Carregando stats para período:', period);
    fetch(`/gamification/api/stats/${period}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Dados recebidos:', data);
            if (data.error) {
                throw new Error(data.error);
            }
            updateChart(data, period);
        })
        .catch(error => {
            console.error('Erro ao carregar dados:', error);
            const ctx = document.getElementById('deepWorkChart').getContext('2d');
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.font = '14px Arial';
            ctx.fillStyle = '#666';
            ctx.fillText('Erro ao carregar dados: ' + error.message, 10, 50);
        });
}

function updateChart(data, period) {
    const ctx = document.getElementById('deepWorkChart').getContext('2d');
    
    if (currentChart) {
        currentChart.destroy();
    }

    // Verificação mais simples dos dados
    if (!data.labels || !data.values) {
        console.error('Dados inválidos:', data);
        return;
    }

    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Minutos em Deep Work',
                data: data.values,
                backgroundColor: '#8A05BE',
                borderColor: '#6A03A0',
                borderWidth: 1,
                borderRadius: 16, // Aumentado de 8 para 16
                borderSkipped: false // Garante que a borda arredondada apareça em todos os lados
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Minutos'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: period === 'week' ? 'Deep Work Semanal' : 'Deep Work Mensal',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} minutos`;
                        }
                    }
                }
            }
        }
    });
    
    // Atualiza o ranking
    updateRanking(data.ranking);
}

function getMedalIcon(position) {
    const medalSVG = `<svg class="medal-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M20,2H4V4L9.81,8.36C6.14,9.57 4.14,13.53 5.35,17.2C6.56,20.87 10.5,22.87 14.19,21.66C17.86,20.45 19.86,16.5 18.65,12.82C17.95,10.71 16.3,9.05 14.19,8.36L20,4V2M14.94,19.5L12,17.78L9.06,19.5L9.84,16.17L7.25,13.93L10.66,13.64L12,10.5L13.34,13.64L16.75,13.93L14.16,16.17L14.94,19.5Z"/></svg>`;
    
    switch(position) {
        case 0: return `<div class="medal-gold">${medalSVG}</div>`;
        case 1: return `<div class="medal-silver">${medalSVG}</div>`;
        case 2: return `<div class="medal-bronze">${medalSVG}</div>`;
        default: return `<div class="medal-none">${medalSVG}</div>`;
    }
}

function updateRanking(ranking) {
    const rankingList = document.getElementById('rankingList');
    const medalCard = document.getElementById('medalCard');
    
    // Encontra posição do usuário atual
    const userPosition = ranking.findIndex(user => user.id === parseInt(document.body.dataset.userId));
    
    // Atualiza card de medalha
    if (userPosition >= 0 && userPosition <= 2) {
        const medals = ['ouro', 'prata', 'bronze'];
        const medalColors = {
            'ouro': '#FFD700',
            'prata': '#C0C0C0', 
            'bronze': '#CD7F32'
        };
        const medal = medals[userPosition];
        
        medalCard.querySelector('.big-medal').innerHTML = `
            <svg viewBox="0 0 24 24" style="color: ${medalColors[medal]}">
                <path fill="currentColor" d="M20,2H4V4L9.81,8.36C6.14,9.57 4.14,13.53 5.35,17.2C6.56,20.87 10.5,22.87 14.19,21.66C17.86,20.45 19.86,16.5 18.65,12.82C17.95,10.71 16.3,9.05 14.19,8.36L20,4V2M14.94,19.5L12,17.78L9.06,19.5L9.84,16.17L7.25,13.93L10.66,13.64L12,10.5L13.34,13.64L16.75,13.93L14.16,16.17L14.94,19.5Z"/>
            </svg>`;
        
        medalCard.querySelector('.medal-text').textContent = 
            `Parabéns! Você conquistou a medalha de ${medal} estando em ${userPosition + 1}º lugar no ranking de Deep Work! Continue mantendo o foco e alta produtividade.`;
        
        medalCard.style.display = 'block';
    } else {
        medalCard.style.display = 'none';
    }

    // Atualiza lista de ranking
    rankingList.innerHTML = ranking.map((user, index) => `
        <div class="ranking-item">
            <div style="display: flex; align-items: center;">
                <div class="ranking-position">${index + 1}</div>
                <div class="ranking-info">
                    <div class="ranking-name">${user.name}</div>
                    <div class="ranking-minutes">${user.minutes} minutos</div>
                </div>
            </div>
            ${getMedalIcon(index)}
        </div>
    `).join('');
}
