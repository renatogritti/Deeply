const columnTemplates = {
    tecnologia: ["Backlog", "Em Desenvolvimento", "Code Review", "Testes", "Deploy", "Concluído"],
    manufatura: ["Matéria-prima", "Produção", "Controle Qualidade", "Embalagem", "Expedição", "Concluído"],
    marketing: ["Ideias", "Planejamento", "Criação", "Revisão", "Aprovação", "Publicado"],
    saude: ["Triagem", "Em Atendimento", "Exames", "Diagnóstico", "Tratamento", "Alta"],
    juridico: ["Novo Caso", "Análise", "Documentação", "Audiências", "Sentença", "Arquivado"],
    recursos_humanos: ["Candidatos", "Triagem", "Entrevistas", "Oferta", "Contratação", "Onboarding"],
    construcao_civil: ["Projeto", "Licenças", "Execução", "Inspeção", "Acabamento", "Entrega"]
};

function fillColumnsFromTemplate() {
    const template = document.getElementById('columnTemplate').value;
    const phasesList = document.getElementById('phasesList');
    
    if (!template) return;

    // Limpa as fases existentes
    phasesList.innerHTML = '';
    
    // Adiciona as novas fases do template
    if (columnTemplates[template]) {
        columnTemplates[template].forEach(phase => {
            const phaseDiv = document.createElement('div');
            phaseDiv.className = 'phase-item';
            phaseDiv.draggable = true;
            phaseDiv.innerHTML = `
                <span class="drag-handle">⋮</span>
                <input type="text" class="phase-name" value="${phase}" required>
                <button type="button" class="remove-phase" onclick="this.parentElement.remove()">&times;</button>
            `;
            phasesList.appendChild(phaseDiv);
        });
    }
}

// Drag and drop para as fases
let draggedItem = null;

document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setupFormSubmission();
    
    // Adiciona listener para o template de colunas
    document.getElementById('columnTemplate').addEventListener('change', function() {
        fillColumnsFromTemplate();
    });
});

function setupDragAndDrop() {
    const phasesList = document.getElementById('phasesList');
    
    phasesList.addEventListener('dragstart', e => {
        if (e.target.classList.contains('phase-item')) {
            draggedItem = e.target;
            e.target.classList.add('dragging');
        }
    });

    phasesList.addEventListener('dragend', e => {
        if (e.target.classList.contains('phase-item')) {
            e.target.classList.remove('dragging');
        }
    });

    phasesList.addEventListener('dragover', e => {
        e.preventDefault();
        if (draggedItem) {
            const closestPhase = getClosestPhase(phasesList, e.clientY);
            if (closestPhase) {
                phasesList.insertBefore(draggedItem, closestPhase);
            } else {
                phasesList.appendChild(draggedItem);
            }
        }
    });
}

// ...resto do código JavaScript específico para projetos...
