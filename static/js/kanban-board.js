// Funções principais do Kanban
function allowDrop(event) {
    event.preventDefault();
}

function drag(event) {
    event.dataTransfer.setData("text", event.target.id);
}

function createCard(id, title, description, tempo, team_name, tags = [], project_id, deadline = null, users = []) {
    var card = document.createElement("div");
    card.className = "kanban-card";
    card.id = id;
    card.draggable = true;
    card.ondragstart = drag;
    card.ondblclick = editCard;
    card.setAttribute('data-project-id', project_id);
    card.setAttribute('data-description', description);

    var cardTitle = document.createElement("h3");
    cardTitle.textContent = title;
    card.appendChild(cardTitle);

    var cardTempo = document.createElement("p");
    cardTempo.textContent = "Tempo: " + tempo;
    card.appendChild(cardTempo);

    if (deadline) {
        var cardDeadline = document.createElement("p");
        cardDeadline.textContent = "Deadline: " + new Date(deadline).toLocaleDateString();
        cardDeadline.className = "card-deadline";
        card.appendChild(cardDeadline);
    }

    if (team_name) {
        var teamTag = document.createElement("div");
        teamTag.className = "team-tag";
        teamTag.textContent = team_name;
        card.appendChild(teamTag);
    }

    if (tags && tags.length > 0) {
        var tagsContainer = document.createElement("div");
        tagsContainer.className = "card-tags";
        tags.forEach(tag => {
            var tagElement = document.createElement("span");
            tagElement.className = "card-tag";
            tagElement.textContent = tag.name;
            tagElement.style.backgroundColor = tag.color;
            tagsContainer.appendChild(tagElement);
        });
        card.appendChild(tagsContainer);
    }

    if (users && users.length > 0) {
        var usersContainer = document.createElement("div");
        usersContainer.className = "card-users";
        users.forEach(user => {
            var userTag = document.createElement("div");
            userTag.className = "user-tag";
            userTag.textContent = user.name;
            usersContainer.appendChild(userTag);
        });
        card.appendChild(usersContainer);
    }

    return card;
}

// Função unificada para carregar o board
async function loadBoard(projectId) {
    if (!projectId) {
        document.querySelector('.kanban-board').innerHTML = '<p>Selecione um projeto para visualizar o quadro Kanban</p>';
        return;
    }

    try {
        // Carrega as fases do projeto
        const phasesResponse = await fetch(`/api/projects/${projectId}/phases`);
        const phases = await phasesResponse.json();
        
        // Atualiza o board com as colunas
        const board = document.querySelector('.kanban-board');
        board.innerHTML = '';
        
        phases.forEach(phase => {
            const column = document.createElement('div');
            column.className = 'kanban-column';
            column.id = `phase_${phase.id}`;
            column.setAttribute('ondrop', 'drop(event)');
            column.setAttribute('ondragover', 'allowDrop(event)');
            
            column.innerHTML = `
                <div class="column-header">
                    <h2>${phase.name}</h2>
                    <button class="add-card-button" onclick="openNewCardModal('phase_${phase.id}')">+</button>
                </div>
            `;
            
            board.appendChild(column);
        });

        // Carrega os cards do projeto
        const cardsResponse = await fetch(`/api/cards?project_id=${projectId}`);
        const cards = await cardsResponse.json();
        
        // Adiciona cada card na coluna correta
        cards.forEach(card => {
            const column = document.getElementById(`phase_${card.phase_id}`);
            if (column) {
                const cardElement = createCard(
                    card.id,
                    card.title,
                    card.description,
                    card.tempo,
                    card.team?.name || '',
                    card.tags,
                    card.project_id,
                    card.deadline,
                    card.users
                );
                column.appendChild(cardElement);
            }
        });
    } catch (error) {
        console.error('Error loading board:', error);
        alert('Error loading board: ' + error.message);
    }
}

// Função unificada para filtrar por projeto
function applyProjectFilter(projectId) {
    const url = new URL(window.location.href);
    
    if (projectId) {
        url.searchParams.set('projeto', projectId);
        loadBoard(projectId);
    } else {
        url.searchParams.delete('projeto');
        document.querySelector('.kanban-board').innerHTML = '<p>Selecione um projeto para visualizar o quadro Kanban</p>';
    }
    
    history.pushState({}, '', url);
    updateAllLinks(projectId);
}

// Função para atualizar links com o projeto selecionado
function updateAllLinks(projectId) {
    ['sidebar-button', 'ai-button', 'badges-button'].forEach(className => {
        document.querySelectorAll(`.${className}`).forEach(button => {
            const onclick = button.getAttribute('onclick');
            if (onclick?.includes('window.location.href')) {
                const baseUrl = onclick.match(/href='([^']+)'/)[1];
                const newUrl = updateUrlWithProject(baseUrl, projectId);
                button.setAttribute('onclick', `window.location.href='${newUrl}'`);
            }
        });
    });
}

// Função auxiliar para atualizar URL com projeto
function updateUrlWithProject(url, projectId) {
    const urlObj = new URL(url, window.location.origin);
    if (projectId) {
        urlObj.searchParams.set('projeto', projectId);
    } else {
        urlObj.searchParams.delete('projeto');
    }
    return urlObj.toString();
}

// Inicialização quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('projeto');
    
    const projectFilter = document.getElementById('projectFilter');
    if (projectFilter) {
        // Atualiza o valor do filtro com o projeto da URL
        projectFilter.value = projectId || '';
        
        // Adiciona event listener para mudanças no filtro
        projectFilter.addEventListener('change', (e) => {
            applyProjectFilter(e.target.value);
        });
        
        // Carrega o board inicial se houver projeto selecionado
        if (projectId) {
            loadBoard(projectId);
        }
    }
});
