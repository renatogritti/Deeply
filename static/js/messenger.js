let currentChannel = null;

document.addEventListener('DOMContentLoaded', () => {
    loadChannels();
    setupMessageInput();
});

function loadChannels() {
    fetch('/api/channels')
        .then(response => response.json())
        .then(channels => {
            const channelsList = document.getElementById('channelsList');
            channelsList.innerHTML = channels.map(channel => `
                <div class="channel-item" 
                     data-channel-id="${channel.id}" 
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
    } else {
        document.querySelector(`[data-channel-id="${channelId}"]`)?.classList.add('active');
    }
    
    loadMessages(channelId);
}

function loadMessages(channelId) {
    fetch(`/api/channels/${channelId}/messages`)
        .then(response => response.json())
        .then(messages => {
            const messagesContainer = document.getElementById('messagesContainer');
            messagesContainer.innerHTML = messages.map(message => createMessageHTML(message)).join('');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
}

function createMessageHTML(message) {
    const isOwnMessage = message.user_id === currentUserId;
    return `
        <div class="message ${isOwnMessage ? 'own-message' : ''}">
            <div class="message-header">
                <span>${message.user_name}</span>
                <span>${new Date(message.created_at).toLocaleString()}</span>
            </div>
            <div class="message-content">${message.content}</div>
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
        alert('Please select a channel first');
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
        } else {
            throw new Error(data.error || 'Error sending message');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error sending message: ' + error.message);
    });
}

function openNewChannelModal() {
    document.getElementById('newChannelModal').style.display = 'block';
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
    const selectedMembers = Array.from(document.querySelectorAll('#membersList input:checked'))
        .map(input => parseInt(input.value));
    
    if (!name) {
        alert('Channel name is required');
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
            loadChannels();
            selectChannel(data.channel.id);
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
    // Removida a linha que tentava acessar isPrivate que não existe mais
}

function openEditChannelModal(channelId) {
    fetch(`/api/channels/${channelId}`)
        .then(response => response.json())
        .then(channel => {
            document.getElementById('editChannelName').value = channel.name;
            document.getElementById('editChannelDescription').value = channel.description || '';
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
            loadChannels();
        } else {
            alert(data.error || 'Error updating channel');
        }
    });
}

function deleteChannel(channelId) {
    if (!confirm('Are you sure you want to delete this channel?')) return;
    
    fetch(`/api/channels/${channelId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadChannels();
            if (currentChannel === channelId) {
                currentChannel = null;
                document.getElementById('messagesContainer').innerHTML = '';
            }
        } else {
            alert(data.error || 'Error deleting channel');
        }
    });
}

function closeEditModal() {
    document.getElementById('editChannelModal').style.display = 'none';
}
