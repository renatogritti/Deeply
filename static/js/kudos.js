document.addEventListener('DOMContentLoaded', function() {
    loadKudos();
    loadUsers();
    setupFilters();
    setupNewKudoButton();
});

function loadKudos() {
    fetch('/kudos/api/kudos')
        .then(response => response.json())
        .then(kudos => {
            const feed = document.getElementById('kudosFeed');
            feed.innerHTML = '';
            kudos.forEach(kudo => {
                feed.appendChild(createKudoCard(kudo));
            });
        })
        .catch(error => {
            console.error('Error loading kudos:', error);
        });
}

function loadUsers() {
    fetch('/api/teams')
        .then(response => response.json())
        .then(users => {
            const select = document.querySelector('select[name="receiver_id"]');
            select.innerHTML = users.map(user => 
                `<option value="${user.id}">${user.name}</option>`
            ).join('');
        });
}

function createKudoCard(kudo) {
    const card = document.createElement('div');
    card.className = 'kudo-card';
    card.innerHTML = `
        <div class="kudo-header">
            <div>
                <strong>${kudo.sender.name}</strong> → <strong>${kudo.receiver.name}</strong>
                <div class="kudo-meta">
                    ${formatDate(kudo.created_at)}
                    <span class="kudo-category">${kudo.category}</span>
                    <span class="kudo-type">${kudo.type}</span>
                </div>
            </div>
        </div>
        <div class="kudo-content">
            ${kudo.message}
        </div>
        <div class="kudo-footer">
            <div class="reactions">
                <button onclick="addReaction(${kudo.id}, 'like')" 
                        class="reaction-button ${hasReaction(kudo.reactions, 'like') ? 'active' : ''}">
                    👍 ${countReactions(kudo.reactions, 'like')}
                </button>
                <button onclick="addReaction(${kudo.id}, 'heart')" 
                        class="reaction-button ${hasReaction(kudo.reactions, 'heart') ? 'active' : ''}">
                    ❤️ ${countReactions(kudo.reactions, 'heart')}
                </button>
            </div>
            <button onclick="toggleComments(${kudo.id})" class="comment-button">
                ${kudo.comments.length} comentários
            </button>
        </div>
        <div class="comments-section" id="comments-${kudo.id}" style="display: none;">
            ${createCommentsHTML(kudo.comments)}
            <form onsubmit="addComment(event, ${kudo.id})" class="comment-form">
                <textarea required placeholder="Adicione um comentário..."></textarea>
                <button type="submit">Enviar</button>
            </form>
        </div>
    `;
    return card;
}

function setupFilters() {
    const categoryFilter = document.getElementById('filterCategory');
    const dateFilter = document.getElementById('filterDate');

    categoryFilter.addEventListener('change', filterKudos);
    dateFilter.addEventListener('change', filterKudos);
}

function filterKudos() {
    const category = document.getElementById('filterCategory').value;
    const date = document.getElementById('filterDate').value;

    fetch(`/api/kudos?category=${category}&date=${date}`)
        .then(response => response.json())
        .then(kudos => {
            const feed = document.getElementById('kudosFeed');
            feed.innerHTML = '';
            kudos.forEach(kudo => {
                feed.appendChild(createKudoCard(kudo));
            });
        });
}

function setupNewKudoButton() {
    const button = document.getElementById('newKudoButton');
    const modal = document.getElementById('kudoModal');
    const form = document.getElementById('kudoForm');

    button.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    form.addEventListener('submit', submitKudo);

    // Adiciona fechamento do modal ao clicar fora
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeKudoModal();
        }
    });
}

function submitKudo(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        receiver_id: parseInt(formData.get('receiver_id')),
        category: formData.get('category'),
        type: formData.get('type'),
        message: formData.get('message')
    };

    fetch('/kudos/api/kudos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(result => {
        closeKudoModal();
        loadKudos(); // Recarrega todos os kudos após criar um novo
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro ao criar kudo: ' + (error.error || 'Erro desconhecido'));
    });
}

function closeKudoModal() {
    document.getElementById('kudoModal').style.display = 'none';
    document.getElementById('kudoForm').reset();
}

// Funções auxiliares
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('pt-BR');
}

function createReactionsHTML(reactions) {
    const types = {
        'like': '👍',
        'heart': '❤️'
    };
    
    return Object.entries(types).map(([type, emoji]) => `
        <button onclick="addReaction(${kudo.id}, '${type}')" 
                class="reaction-button ${hasReaction(reactions, type) ? 'active' : ''}">
            ${emoji} ${countReactions(reactions, type)}
        </button>
    `).join('');
}

function createCommentsHTML(comments) {
    return comments.map(comment => `
        <div class="comment">
            <strong>${comment.user.name}</strong>
            <div>${comment.content}</div>
            <small>${formatDate(comment.created_at)}</small>
        </div>
    `).join('');
}

function addReaction(kudoId, type) {
    fetch(`/kudos/api/kudos/${kudoId}/react`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reaction_type: type })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            loadKudos();  // Recarrega para atualizar reações
        }
    });
}

function toggleComments(kudoId) {
    const section = document.getElementById(`comments-${kudoId}`);
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
}

function addComment(event, kudoId) {
    event.preventDefault();
    const textarea = event.target.querySelector('textarea');
    const content = textarea.value.trim();

    if (!content) return;

    fetch(`/kudos/api/kudos/${kudoId}/comment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
    })
    .then(response => response.json())
    .then(result => {
        textarea.value = '';
        loadKudos();  // Recarrega para mostrar novo comentário
    });
}

function hasReaction(reactions, type) {
    return reactions.some(r => r.reaction_type === type);
}

function countReactions(reactions, type) {
    return reactions.filter(r => r.reaction_type === type).length;
}
