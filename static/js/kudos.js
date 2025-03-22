document.addEventListener('DOMContentLoaded', function() {
    loadKudos();
    loadUsers();
    setupFilters();
    setupNewKudoButton();

    // Configurar o emoji picker
    const picker = document.querySelector('emoji-picker');
    const textarea = document.querySelector('textarea[name="message"]');
    
    picker.addEventListener('emoji-click', event => {
        const cursor = textarea.selectionStart;
        const text = textarea.value;
        const insert = event.detail.unicode;
        textarea.value = text.slice(0, cursor) + insert + text.slice(cursor);
        textarea.selectionStart = cursor + insert.length;
        textarea.selectionEnd = cursor + insert.length;
        textarea.focus();
    });

    // Fechar o picker ao clicar fora
    document.addEventListener('click', function(e) {
        const picker = document.querySelector('emoji-picker');
        const trigger = document.querySelector('.emoji-trigger');
        if (!picker.contains(e.target) && !trigger.contains(e.target)) {
            picker.style.display = 'none';
        }
    });

    updateRemainingKudos();
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
            updateRemainingKudos(); // Atualiza as estrelas após carregar kudos
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

function getCategoryIcon(category) {
    const icons = {
        'reconhecimento': '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 6H4V4H20V6M20 12H4V10H20V12M20 18H4V16H20V18Z"/></svg>',
        'premio': '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 6.91L17.09 4H12V2H22V12H20V6.91M18 13L21 16V22H3V16L6 13H18M11 18.5C11 19.33 10.33 20 9.5 20S8 19.33 8 18.5 8.67 17 9.5 17 11 17.67 11 18.5M16 18.5C16 19.33 15.33 20 14.5 20S13 19.33 13 18.5 13.67 17 14.5 17 16 17.67 16 18.5Z"/></svg>',
        'mensagem': '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H5.17L4,17.17V4H20V16Z"/></svg>'
    };
    return icons[category] || '';
}

function getTypeIcon(type) {
    const icons = {
        'trabalho_equipe': '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12,5.5A3.5,3.5 0 0,1 15.5,9A3.5,3.5 0 0,1 12,12.5A3.5,3.5 0 0,1 8.5,9A3.5,3.5 0 0,1 12,5.5M5,8C5.56,8 6.08,8.15 6.53,8.42C6.38,9.85 6.8,11.27 7.66,12.38C7.16,13.34 6.16,14 5,14A3,3 0 0,1 2,11A3,3 0 0,1 5,8M19,8A3,3 0 0,1 22,11A3,3 0 0,1 19,14C17.84,14 16.84,13.34 16.34,12.38C17.2,11.27 17.62,9.85 17.47,8.42C17.92,8.15 18.44,8 19,8M5.5,18.25C5.5,16.18 8.41,14.5 12,14.5C15.59,14.5 18.5,16.18 18.5,18.25V20H5.5V18.25M0,20V18.5C0,17.11 1.89,15.94 4.45,15.6C3.86,16.28 3.5,17.22 3.5,18.25V20H0M24,20H20.5V18.25C20.5,17.22 20.14,16.28 19.55,15.6C22.11,15.94 24,17.11 24,18.5V20Z"/></svg>',
        'inovacao': '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12,2A7,7 0 0,1 19,9C19,11.38 17.81,13.47 16,14.74V17A1,1 0 0,1 15,18H9A1,1 0 0,1 8,17V14.74C6.19,13.47 5,11.38 5,9A7,7 0 0,1 12,2M9,21V20H15V21A1,1 0 0,1 14,22H10A1,1 0 0,1 9,21M12,4A5,5 0 0,0 7,9C7,11.05 8.23,12.81 10,13.58V16H14V13.58C15.77,12.81 17,11.05 17,9A5,5 0 0,0 12,4Z"/></svg>',
        'ajuda': '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12,1C7,1 3,5 3,10C3,14.1 5.2,17.7 8.8,19.4C9.8,19.8 10,20.3 10,20.8V22H14V20.8C14,20.3 14.2,19.8 15.2,19.4C18.8,17.7 21,14.1 21,10C21,5 17,1 12,1M12,3C15.9,3 19,6.1 19,10C19,13.1 17.2,15.8 14.5,17.1C13.8,17.4 13.3,17.7 12.9,18H11.1C10.7,17.7 10.2,17.4 9.5,17.1C6.8,15.8 5,13.1 5,10C5,6.1 8.1,3 12,3M14,16L12,14L10,16L9,15L11,13L9,11L10,10L12,12L14,10L15,11L13,13L15,15L14,16Z"/></svg>'
    };
    return icons[type] || '';
}

function createKudoCard(kudo) {
    const card = document.createElement('div');
    card.className = 'kudo-card';
    card.innerHTML = `
        <div class="kudo-header">
            <div class="kudo-info">
                <strong>${kudo.sender.name}</strong> → <strong>${kudo.receiver.name}</strong>
                <div class="kudo-meta">
                    ${formatDate(kudo.created_at)}
                    <div class="kudo-badges">
                        <span class="kudo-badge category-badge">
                            ${getCategoryIcon(kudo.category)}
                            ${kudo.category}
                        </span>
                        <span class="kudo-badge type-badge">
                            ${getTypeIcon(kudo.type)}
                            ${kudo.type}
                        </span>
                    </div>
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

let isSubmitting = false;

function submitKudo(event) {
    event.preventDefault();
    
    if (isSubmitting) {
        return;
    }

    isSubmitting = true;
    const submitButton = event.target.querySelector('button[type="submit"]');
    submitButton.disabled = true;

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
    .then(() => {
        closeKudoModal();
        return loadKudos();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro ao criar kudo: ' + (error.error || 'Erro desconhecido'));
    })
    .finally(() => {
        submitButton.disabled = false;
        isSubmitting = false;
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

function selectType(type) {
    const radio = document.querySelector(`input[name="type"][value="${type}"]`);
    radio.checked = true;
}

function toggleEmojiPicker() {
    const picker = document.querySelector('emoji-picker');
    picker.style.display = picker.style.display === 'none' ? 'block' : 'none';
}

function updateRemainingKudos() {
    return fetch('/kudos/api/kudos/remaining')
        .then(response => response.json())
        .then(data => {
            const stars = document.querySelectorAll('.kudos-stars .star');
            const remainingText = document.querySelector('.remaining-kudos span');
            
            stars.forEach((star, index) => {
                if (index < data.remaining) {
                    star.classList.add('active');
                } else {
                    star.classList.remove('active');
                }
            });

            remainingText.textContent = `Remaining Kudos (${data.remaining}/${data.total})`;
        })
        .catch(error => {
            console.error('Error loading remaining kudos:', error);
        });
}
