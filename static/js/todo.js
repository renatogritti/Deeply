document.addEventListener('DOMContentLoaded', loadTodoLists);

function loadTodoLists() {
    fetch('/api/todo/lists')
        .then(response => response.json())
        .then(lists => {
            const container = document.getElementById('todoLists');
            container.innerHTML = '';
            
            lists.forEach(list => {
                const listElement = createListElement(list);
                container.appendChild(listElement);
            });
            
            setupDragAndDrop();
        });
}

function createListElement(list) {
    const listDiv = document.createElement('div');
    listDiv.className = 'todo-list';
    listDiv.setAttribute('data-list-id', list.id);
    
    listDiv.innerHTML = `
        <div class="list-header">
            <h3>${list.name}</h3>
            <div class="list-actions">
                <button onclick="openNewTaskModal(${list.id})">
                    <svg viewBox="0 0 24 24">
                        <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
                    </svg>
                    Add
                </button>
                <button onclick="editList(${list.id})">
                    <svg viewBox="0 0 24 24">
                        <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
                    </svg>
                    Edit
                </button>
                <button onclick="deleteList(${list.id})">
                    <svg viewBox="0 0 24 24">
                        <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                    </svg>
                    Delete
                </button>
            </div>
        </div>
        <div class="tasks-container" ondrop="drop(event)" ondragover="allowDrop(event)">
            ${list.tasks.sort((a, b) => a.order - b.order).map(task => createTaskHTML(task)).join('')}
        </div>
    `;
    
    return listDiv;
}

function createTaskHTML(task) {
    return `
        <div class="task ${task.completed ? 'completed' : ''}" draggable="true" 
             ondragstart="drag(event)" id="task_${task.id}">
            <input type="checkbox" class="task-checkbox" 
                   id="check_${task.id}" 
                   ${task.completed ? 'checked' : ''} 
                   onchange="toggleTaskComplete(${task.id}, this.checked)">
            <label for="check_${task.id}"></label>
            <div class="task-content">
                <div class="task-header">
                    <span class="task-title">${task.title}</span>
                    <span class="priority-badge priority-${task.priority}">${task.priority}</span>
                </div>
                <p>${task.description || ''}</p>
                <div class="task-actions">
                    <button onclick="editTask(${task.id})">
                        <svg viewBox="0 0 24 24">
                            <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
                        </svg>
                        Edit
                    </button>
                    <button onclick="deleteTask(${task.id})">
                        <svg viewBox="0 0 24 24">
                            <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                        </svg>
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `;
}

function toggleTaskComplete(taskId, completed) {
    fetch(`/api/todo/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: completed })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const taskElement = document.getElementById(`task_${taskId}`);
            if (completed) {
                taskElement.classList.add('completed');
            } else {
                taskElement.classList.remove('completed');
            }
        }
    });
}

function updateTaskOrder(taskId, listId, newOrder) {
    fetch(`/api/todo/tasks/${taskId}/order`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            list_id: listId,
            order: newOrder 
        })
    });
}

function setupDragAndDrop() {
    const tasks = document.querySelectorAll('.task');
    const containers = document.querySelectorAll('.tasks-container');

    tasks.forEach(task => {
        task.addEventListener('dragstart', () => {
            task.classList.add('dragging');
        });

        task.addEventListener('dragend', () => {
            task.classList.remove('dragging');
            
            // Atualizar ordem de todas as tarefas na lista
            const container = task.closest('.tasks-container');
            const tasks = [...container.querySelectorAll('.task')];
            tasks.forEach((task, index) => {
                const taskId = task.id.replace('task_', '');
                const listId = task.closest('.todo-list').getAttribute('data-list-id');
                updateTaskOrder(taskId, listId, index);
            });
        });
    });

    containers.forEach(container => {
        container.addEventListener('dragover', e => {
            e.preventDefault();
            const afterElement = getDragAfterElement(container, e.clientY);
            const draggable = document.querySelector('.dragging');
            if (afterElement) {
                container.insertBefore(draggable, afterElement);
            } else {
                container.appendChild(draggable);
            }
        });
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.task:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// Funções para drag and drop
function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.id);
    ev.target.classList.add('dragging');
}

function drop(ev) {
    ev.preventDefault();
    const taskId = ev.dataTransfer.getData("text").replace('task_', '');
    const targetList = ev.target.closest('.todo-list');
    const listId = targetList.getAttribute('data-list-id');
    
    document.querySelector('.dragging')?.classList.remove('dragging');
    
    updateTaskList(taskId, listId);
}

// Funções CRUD
function createList() {
    const name = document.getElementById('listName').value;
    const description = document.getElementById('listDescription').value;
    
    fetch('/api/todo/lists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTodoLists();
            closeModal('newListModal');
        }
    });
}

function createTask() {
    const listId = document.getElementById('currentListId').value;
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDescription').value;
    const priority = document.getElementById('taskPriority').value;
    
    fetch('/api/todo/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ list_id: listId, title, description, priority })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTodoLists();
            closeModal('newTaskModal');
        }
    });
}

// Funções helper
function openNewListModal() {
    document.getElementById('newListModal').style.display = 'block';
}

function openNewTaskModal(listId) {
    document.getElementById('currentListId').value = listId;
    document.getElementById('newTaskModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function editList(listId) {
    fetch(`/api/todo/lists/${listId}`)
        .then(response => response.json())
        .then(list => {
            document.getElementById('listName').value = list.name;
            document.getElementById('listDescription').value = list.description || '';
            const modal = document.getElementById('newListModal');
            modal.setAttribute('data-list-id', listId);
            document.querySelector('#newListModal .modal-buttons').innerHTML = `
                <button onclick="updateList(${listId})">Update</button>
                <button onclick="closeModal('newListModal')">Cancel</button>
            `;
            modal.style.display = 'block';
        });
}

function updateList(listId) {
    const name = document.getElementById('listName').value;
    const description = document.getElementById('listDescription').value;
    
    fetch(`/api/todo/lists/${listId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTodoLists();
            closeModal('newListModal');
        }
    });
}

function deleteList(listId) {
    if (!confirm('Are you sure you want to delete this list?')) return;
    
    fetch(`/api/todo/lists/${listId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTodoLists();
        }
    });
}

function editTask(taskId) {
    fetch(`/api/todo/tasks/${taskId}`)
        .then(response => response.json())
        .then(task => {
            document.getElementById('taskTitle').value = task.title;
            document.getElementById('taskDescription').value = task.description || '';
            document.getElementById('taskPriority').value = task.priority;
            document.getElementById('currentListId').value = task.list_id;
            const modal = document.getElementById('newTaskModal');
            modal.setAttribute('data-task-id', taskId);
            document.querySelector('#newTaskModal .modal-buttons').innerHTML = `
                <button onclick="updateTask(${taskId})">Update</button>
                <button onclick="closeModal('newTaskModal')">Cancel</button>
            `;
            modal.style.display = 'block';
        });
}

function updateTask(taskId) {
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDescription').value;
    const priority = document.getElementById('taskPriority').value;
    
    fetch(`/api/todo/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, priority })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTodoLists();
            closeModal('newTaskModal');
        }
    });
}

function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    fetch(`/api/todo/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTodoLists();
        }
    });
}
