let currentChannel = null;
let activeHashtags = new Set();
let activeMentions = new Set();
let allMessages = [];
let userProjects = [];

document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    setupMessageInput();
    initEmojiPicker();

    // Event listeners para os inputs de filtro
    const hashtagFilter = document.getElementById('hashtagFilter');
    hashtagFilter.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const tag = this.value.replace('#', '').trim();
            if (tag) {
                addHashtagFilter(tag);
                this.value = '';
            }
        }
    });

    const mentionFilter = document.getElementById('mentionFilter');
    mentionFilter.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const mention = this.value.replace('@', '').trim();
            if (mention) {
                addMentionFilter(mention);
                this.value = '';
            }
        }
    });
});

function loadProjects() {
    fetch('/api/projects/user')
        .then(response => response.json())
        .then(projects => {
            userProjects = projects;
            const projectsAccordion = document.getElementById('projectsAccordion');
            projectsAccordion.innerHTML = '';
            
            projects.forEach(project => {
                const projectSection = document.createElement('div');
                projectSection.className = 'project-section';
                projectSection.id = `project-${project.id}`;
                
                projectSection.innerHTML = `
                    <div class="project-header" onclick="toggleProjectSection(${project.id})">
                        <span>${project.name}</span>
                        <svg class="toggle-icon" viewBox="0 0 24 24" width="16" height="16">
                            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
                        </svg>
                    </div>
                    <div class="project-channels" id="project-channels-${project.id}">
                        <!-- Canais serão carregados via fetch -->
                    </div>
                `;
                
                projectsAccordion.appendChild(projectSection);
                loadProjectChannels(project.id);
            });
            
            // Preenche a seleção de projetos nos modais
            populateProjectSelects();
        })
        .catch(error => {
            console.error('Error loading projects:', error);
        });
}

function populateProjectSelects() {
    const projectSelect = document.getElementById('projectSelect');
    const editProjectSelect = document.getElementById('editProjectSelect');
    
    // Limpa as seleções atuais
    projectSelect.innerHTML = '<option value="">Selecione um projeto</option>';
    editProjectSelect.innerHTML = '<option value="">Selecione um projeto</option>';
    
    // Adiciona as opções de projetos
    userProjects.forEach(project => {
        projectSelect.innerHTML += `<option value="${project.id}">${project.name}</option>`;
        editProjectSelect.innerHTML += `<option value="${project.id}">${project.name}</option>`;
    });
}

function toggleProjectSection(projectId) {
    const projectSection = document.getElementById(`project-${projectId}`);
    projectSection.classList.toggle('expanded');
}

function loadProjectChannels(projectId) {
    fetch(`/api/projects/${projectId}/channels`)
        .then(response => response.json())
        .then(channels => {
            const channelsContainer = document.getElementById(`project-channels-${projectId}`);
            channelsContainer.innerHTML = channels.map(channel => `
                <div class="channel-item" 
                     data-channel-id="${channel.id}" 
                     data-project-id="${projectId}"
                     onclick="selectChannel(${channel.id}, this)">
                    <span>${channel.is_private ? '🔒' : '#'} ${channel.name}</span>
                    <div class="channel-actions" onclick="event.stopPropagation()">
                        <button class="channel-action-btn" onclick="openEditChannelModal(${channel.id})">
                            <svg viewBox="0 0 24 24">
                                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
                            </svg>
                        </button>
                        <button class="channel-action-btn" onclick="deleteChannel(${channel.id})">
                            <svg viewBox="0 0 24 24">
                                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `).join('');
        });
}

function selectChannel(channelId, element = null) {
    currentChannel = channelId;
    
    // Remove classe active de todos os canais
    document.querySelectorAll('.channel-item').forEach(item => {
        item.classList.remove('active');
    });

    // Adiciona classe active ao canal selecionado
    if (element) {
        element.classList.add('active');
        
        // Expande a seção do projeto se necessário
        const projectId = element.getAttribute('data-project-id');
        const projectSection = document.getElementById(`project-${projectId}`);
        if (!projectSection.classList.contains('expanded')) {
            projectSection.classList.add('expanded');
        }
    } else {
        document.querySelector(`[data-channel-id="${channelId}"]`)?.classList.add('active');
    }
    
    loadMessages(channelId);
}

function loadMessages(channelId) {
    fetch(`/api/channels/${channelId}/messages`)
        .then(response => response.json())
        .then(messages => {
            allMessages = messages; // Armazena todas as mensagens
            displayFilteredMessages();
        });
}

function displayFilteredMessages() {
    let filteredMessages = allMessages;

    if (activeHashtags.size > 0) {
        filteredMessages = filteredMessages.filter(message => 
            Array.from(activeHashtags).some(tag => 
                message.content.includes(`#${tag}`)));
    }

    if (activeMentions.size > 0) {
        filteredMessages = filteredMessages.filter(message =>
            Array.from(activeMentions).some(mention =>
                message.content.includes(`@${mention}`)));
    }

    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML = filteredMessages.map(message => createMessageHTML(message)).join('');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Atualiza os filtros ativos na UI
    updateActiveFilters();
}

function processMessageContent(content) {
    // Substituições para formatação de texto
    content = content
        // Negrito: *texto* ou **texto**
        .replace(/\*\*(.*?)\*\*|\*(.*?)\*/g, '<strong>$1$2</strong>')
        // Itálico: _texto_ ou __texto__
        .replace(/\_\_(.*?)\_\_|\_(.*?)\_/g, '<em>$1$2</em>')
        // Código: `texto`
        .replace(/\`(.*?)\`/g, '<code>$1</code>')
        // Tachado: ~texto~ ou ~~texto~~
        .replace(/\~\~(.*?)\~\~|\~(.*?)\~/g, '<del>$1$2</del>')
        // Links: [texto](url)
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Processa hashtags
    content = content.replace(/#(\w+)/g, '<span class="hashtag" onclick="addHashtagFilter(\'$1\')">#$1</span>');
    
    // Processa menções
    content = content.replace(/@(\w+)/g, '<span class="mention" onclick="addMentionFilter(\'$1\')">@$1</span>');
    
    return content;
}

function createMessageHTML(message) {
    const isOwnMessage = message.user_id === currentUserId;
    return `
        <div class="message ${isOwnMessage ? 'own-message' : ''}">
            <div class="message-header">
                <span>${message.user_name}</span>
                <span>${new Date(message.created_at).toLocaleString()}</span>
            </div>
            <div class="message-content">${processMessageContent(message.content)}</div>
        </div>
    `;
}

function setupMessageInput() {
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function sendMessage() {
    if (!currentChannel) {
        alert('Por favor, selecione um canal primeiro');
        return;
    }
    
    const messageInput = document.getElementById('messageInput');
    const content = messageInput.value.trim();
    
    if (!content) return;
    
    fetch('/api/messages', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            channel_id: currentChannel,
            content: content
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            messageInput.value = '';
            // Adiciona a nova mensagem diretamente ao container
            const messagesContainer = document.getElementById('messagesContainer');
            messagesContainer.insertAdjacentHTML('beforeend', createMessageHTML(data.message));
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Se usamos hashtags ou menções, atualizamos os filtros
            if (activeHashtags.size > 0 || activeMentions.size > 0) {
                loadMessages(currentChannel);
            }
        } else {
            throw new Error(data.error || 'Error sending message');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error sending message: ' + error.message);
    });
}

function formatText(type) {
    const messageInput = document.getElementById('messageInput');
    const start = messageInput.selectionStart;
    const end = messageInput.selectionEnd;
    const text = messageInput.value;
    let formattedText = '';
    
    const selectedText = text.substring(start, end);
    
    switch(type) {
        case 'bold':
            formattedText = `**${selectedText}**`;
            break;
        case 'italic':
            formattedText = `_${selectedText}_`;
            break;
        case 'code':
            formattedText = `\`${selectedText}\``;
            break;
        case 'strikethrough':
            formattedText = `~~${selectedText}~~`;
            break;
        case 'link':
            const url = prompt('Digite a URL:');
            if (url) {
                formattedText = `[${selectedText || 'link'}](${url})`;
            } else {
                return;
            }
            break;
    }
    
    messageInput.value = text.slice(0, start) + formattedText + text.slice(end);
    messageInput.focus();
    
    // Posiciona o cursor após o texto formatado
    const newPosition = start + formattedText.length;
    messageInput.setSelectionRange(newPosition, newPosition);
}

function openNewChannelModal() {
    document.getElementById('newChannelModal').style.display = 'block';
    populateProjectSelects();  // Garante que as opções de projeto estão atualizadas
    loadUsers();
}

function loadUsers() {
    fetch('/api/teams')
        .then(response => response.json())
        .then(users => {
            const membersList = document.getElementById('membersList');
            membersList.innerHTML = users
                .sort((a, b) => a.name.localeCompare(b.name)) // Ordena por nome
                .map(user => `
                    <div class="member-item">
                        <input type="checkbox" 
                               id="user_${user.id}" 
                               value="${user.id}">
                        <label for="user_${user.id}">${user.name}</label>
                    </div>
                `).join('');
        })
        .catch(error => {
            console.error('Error loading users:', error);
            alert('Error loading users list');
        });
}

function createChannel() {
    const name = document.getElementById('channelName').value.trim();
    const description = document.getElementById('channelDescription').value.trim();
    const projectId = document.getElementById('projectSelect').value;
    const selectedMembers = Array.from(document.querySelectorAll('#membersList input:checked'))
        .map(input => parseInt(input.value));
    
    if (!name) {
        alert('O nome do canal é obrigatório');
        return;
    }
    
    if (!projectId) {
        alert('Selecione um projeto para o canal');
        return;
    }

    // Inclui o usuário atual na lista de membros se não estiver
    if (!selectedMembers.includes(currentUserId)) {
        selectedMembers.push(currentUserId);
    }

    const data = {
        name: name,
        description: description,
        is_private: false,
        project_id: parseInt(projectId),
        member_ids: selectedMembers
    };

    fetch('/api/channels', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Error creating channel') });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            closeModal();
            // Recarrega os canais do projeto
            loadProjectChannels(parseInt(projectId));
            // Expande o projeto para mostrar o novo canal
            const projectSection = document.getElementById(`project-${projectId}`);
            if (projectSection && !projectSection.classList.contains('expanded')) {
                projectSection.classList.add('expanded');
            }
            // Seleciona o novo canal
            setTimeout(() => {
                selectChannel(data.channel.id);
            }, 300);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message);
    });
}

function closeModal() {
    document.getElementById('newChannelModal').style.display = 'none';
    document.getElementById('channelName').value = '';
    document.getElementById('channelDescription').value = '';
    document.getElementById('projectSelect').value = '';
}

function openEditChannelModal(channelId) {
    fetch(`/api/channels/${channelId}`)
        .then(response => response.json())
        .then(channel => {
            document.getElementById('editChannelName').value = channel.name;
            document.getElementById('editChannelDescription').value = channel.description || '';
            document.getElementById('editProjectSelect').value = channel.project_id;
            document.getElementById('editChannelModal').setAttribute('data-channel-id', channelId);
            
            // Carrega a lista de usuários para edição
            fetch('/api/teams')
                .then(response => response.json())
                .then(users => {
                    const membersList = document.getElementById('editMembersList');
                    membersList.innerHTML = users
                        .sort((a, b) => a.name.localeCompare(b.name))
                        .map(user => `
                            <div class="member-item">
                                <input type="checkbox" 
                                       id="edit_user_${user.id}" 
                                       value="${user.id}"
                                       ${channel.members.some(m => m.id === user.id) ? 'checked' : ''}>
                                <label for="edit_user_${user.id}">${user.name}</label>
                            </div>
                        `).join('');
                });
            
            document.getElementById('editChannelModal').style.display = 'block';
        });
}

function updateChannel() {
    const modal = document.getElementById('editChannelModal');
    const channelId = modal.getAttribute('data-channel-id');
    const data = {
        name: document.getElementById('editChannelName').value.trim(),
        description: document.getElementById('editChannelDescription').value.trim(),
        project_id: parseInt(document.getElementById('editProjectSelect').value),
        member_ids: Array.from(document.querySelectorAll('#editMembersList input:checked'))
            .map(input => parseInt(input.value))
    };

    fetch(`/api/channels/${channelId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeEditModal();
            // Recarregar todos os projetos e canais para refletir possíveis mudanças
            loadProjects();
        } else {
            alert(data.error || 'Error updating channel');
        }
    });
}

function deleteChannel(channelId) {
    if (!confirm('Tem certeza que deseja excluir este canal?')) return;
    
    // Primeiro obtemos os detalhes do canal para saber a qual projeto ele pertence
    fetch(`/api/channels/${channelId}`)
        .then(response => response.json())
        .then(channel => {
            const projectId = channel.project_id;
            
            // Agora deletamos o canal
            fetch(`/api/channels/${channelId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Recarrega os canais do projeto
                    loadProjectChannels(projectId);
                    if (currentChannel === channelId) {
                        currentChannel = null;
                        document.getElementById('messagesContainer').innerHTML = '';
                    }
                } else {
                    alert(data.error || 'Error deleting channel');
                }
            });
        });
}

function closeEditModal() {
    document.getElementById('editChannelModal').style.display = 'none';
}

// Lista de emojis comuns para mensagens
const commonEmojis = [
    '😊', '😄', '😅', '🤣', '😂', '😉', '😍', '🥰',
    '😘', '😋', '😎', '🤩', '🥳', '😤', '🤔', '🤗',
    '👍', '👎', '👌', '🙌', '👏', '🤝', '💪', '🙏',
    '❤️', '💔', '💯', '✨', '🎉', '🎊', '🎈', '🎵'
];

// Inicializa o emoji picker
function initEmojiPicker() {
    const emojiList = document.querySelector('.emoji-list');
    if (emojiList) {
        emojiList.innerHTML = commonEmojis.map(emoji => 
            `<span class="emoji-item" onclick="insertEmoji('${emoji}')">${emoji}</span>`
        ).join('');
    }
}

// Toggle do emoji picker
function toggleEmojiPicker(event) {
    const picker = document.getElementById('emojiPicker');
    const button = event.currentTarget;
    
    if (!picker.initialized) {
        initEmojiPicker();
        picker.initialized = true;
    }
    
    if (picker.style.display === 'block') {
        picker.style.display = 'none';
        return;
    }

    // Calcula a posição ideal
    const buttonRect = button.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;
    
    // Exibe temporariamente para obter dimensões
    picker.style.display = 'block';
    picker.style.visibility = 'hidden';
    const pickerHeight = picker.offsetHeight;
    const pickerWidth = picker.offsetWidth;
    
    // Calcula posição inicial (acima do botão)
    let top = buttonRect.top - pickerHeight - 5;
    let left = buttonRect.left;
    
    // Se não couber acima, posiciona abaixo
    if (top < 0) {
        top = buttonRect.bottom + 5;
        
        // Se também não couber abaixo, posiciona onde houver mais espaço
        if (top + pickerHeight > windowHeight) {
            top = Math.max(5, windowHeight - pickerHeight - 5);
        }
    }
    
    // Ajusta posição horizontal se necessário
    if (left + pickerWidth > windowWidth) {
        left = Math.max(5, windowWidth - pickerWidth - 5);
    }
    
    // Aplica a posição final
    picker.style.top = `${top}px`;
    picker.style.left = `${left}px`;
    picker.style.visibility = 'visible';
    
    event.stopPropagation();
}

function insertEmoji(emoji) {
    const messageInput = document.getElementById('messageInput');
    const start = messageInput.selectionStart;
    const end = messageInput.selectionEnd;
    const text = messageInput.value;
    
    messageInput.value = text.slice(0, start) + emoji + text.slice(end);
    messageInput.focus();
    messageInput.selectionStart = messageInput.selectionEnd = start + emoji.length;
}

// Fecha o picker ao clicar fora
document.addEventListener('click', (event) => {
    const picker = document.getElementById('emojiPicker');
    if (picker && !event.target.closest('.emoji-trigger') && !event.target.closest('.emoji-picker')) {
        picker.style.display = 'none';
    }
});

// Funções para gerenciar filtros
function addHashtagFilter(tag) {
    activeHashtags.add(tag);
    displayFilteredMessages();
}

function addMentionFilter(mention) {
    activeMentions.add(mention);
    displayFilteredMessages();
}

function removeHashtagFilter(tag) {
    activeHashtags.delete(tag);
    displayFilteredMessages();
}

function removeMentionFilter(mention) {
    activeMentions.delete(mention);
    displayFilteredMessages();
}

function updateActiveFilters() {
    const hashtagsContainer = document.getElementById('activeHashtags');
    const mentionsContainer = document.getElementById('activeMentions');

    hashtagsContainer.innerHTML = Array.from(activeHashtags)
        .map(tag => `
            <span class="filter-tag">
                #${tag}
                <button onclick="removeHashtagFilter('${tag}')">&times;</button>
            </span>
        `).join('');

    mentionsContainer.innerHTML = Array.from(activeMentions)
        .map(mention => `
            <span class="filter-tag">
                @${mention}
                <button onclick="removeMentionFilter('${mention}')">&times;</button>
            </span>
        `).join('');
}

function clearFilters() {
    activeHashtags.clear();
    activeMentions.clear();
    displayFilteredMessages();
    document.getElementById('hashtagFilter').value = '';
    document.getElementById('mentionFilter').value = '';
}
