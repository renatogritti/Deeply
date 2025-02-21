
// Drag and drop para as fases
let draggedItem = null;

document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setupFormSubmission();
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
