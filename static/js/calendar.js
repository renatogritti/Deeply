document.addEventListener('DOMContentLoaded', function() {
    let calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
        locale: 'pt-br',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
        },
        views: {
            dayGridMonth: {
                titleFormat: { year: 'numeric', month: 'long' }
            },
            timeGridWeek: {
                titleFormat: { year: 'numeric', month: 'short', day: 'numeric' },
                slotDuration: '01:00:00',
                slotLabelFormat: {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                }
            }
        },
        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana'
        },
        events: initialEvents // Variável global definida no template
    });
    calendar.render();

    // Adiciona listener do filtro e carrega eventos iniciais
    const projectFilter = document.getElementById('projectFilter');
    projectFilter.addEventListener('change', e => filterCalendarEvents(e.target.value));

    window.filterCalendarEvents = function(projectId) {
        const url = projectId ? `/api/cards?project_id=${projectId}` : '/api/cards';
        
        fetch(url)
            .then(response => response.json())
            .then(cards => {
                calendar.removeAllEvents();
                const events = cards
                    .filter(card => card.deadline)
                    .map(card => ({
                        title: card.title,
                        start: card.deadline,
                        description: card.description,
                        backgroundColor: card.tags?.[0]?.color || '#1a73e8',
                        borderColor: card.tags?.[0]?.color || '#1a73e8',
                        textColor: '#ffffff'
                    }));
                calendar.addEventSource(events);
                updateTasksList(cards);
            })
            .catch(error => {
                console.error('Erro ao filtrar eventos:', error);
                alert('Erro ao carregar eventos');
            });
    };

    // Pré-seleciona o projeto da URL
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    if (projectId) {
        const projectFilter = document.getElementById('projectFilter');
        if (projectFilter) {
            projectFilter.value = projectId;
            filterByProject(projectId);
        }
    }
});

function filterByProject(projectId) {
    // Atualiza a URL com o projeto selecionado
    const url = new URL(window.location.href);
    if (projectId) {
        url.searchParams.set('projeto', projectId);
    } else {
        url.searchParams.delete('projeto');
    }
    history.pushState({}, '', url);

    // Filtra os cartões usando o mesmo parâmetro
    fetch(`/api/calendar/cards${projectId ? `?projeto=${projectId}` : ''}`)
        .then(response => response.json())
        .then(data => {
            calendar.removeAllEvents();
            const events = data.map(card => ({
                title: card.title,
                start: card.deadline,
                description: card.description,
                backgroundColor: card.tags?.[0]?.color || '#1a73e8',
                borderColor: card.tags?.[0]?.color || '#1a73e8',
                textColor: '#ffffff'
            }));
            calendar.addEventSource(events);
            updateTasksList(data);
        })
        .catch(error => console.error('Erro ao filtrar eventos:', error));
}

function updateTasksList(cards) {
    const withDeadline = cards.filter(card => card.deadline);
    const withoutDeadline = cards.filter(card => !card.deadline);
    
    const withDeadlineContainer = document.querySelector('.mb-4');
    const withoutDeadlineContainer = withDeadlineContainer.nextElementSibling;
    
    withDeadlineContainer.innerHTML = `
        <h6 class="border-bottom pb-2">Tarefas com Prazo</h6>
        ${withDeadline.map(card => createTaskCard(card)).join('') || '<p class="text-muted">Nenhuma tarefa com prazo</p>'}
    `;
    
    withoutDeadlineContainer.innerHTML = `
        <h6 class="border-bottom pb-2">Tarefas sem Prazo</h6>
        ${withoutDeadline.map(card => createTaskCard(card)).join('') || '<p class="text-muted">Nenhuma tarefa sem prazo</p>'}
    `;
}

function createTaskCard(card) {
    const deadline = card.deadline ? 
        `<p class="deadline">${new Date(card.deadline).toLocaleDateString('pt-BR')}</p>` : '';

    const tags = card.tags?.length ? `
        <div class="card-tags">
            ${card.tags.map(tag => `
                <span class="card-tag" style="background-color: ${tag.color}">${tag.name}</span>
            `).join('')}
        </div>
    ` : '';

    return `
        <div class="kanban-card">
            <h3>${card.title}</h3>
            ${deadline}
            <p class="description">${card.description.slice(0, 100)}${card.description.length > 100 ? '...' : ''}</p>
            ${tags}
        </div>
    `;
}
