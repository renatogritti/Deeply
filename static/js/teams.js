document.addEventListener('DOMContentLoaded', function() {
    loadTeamsList();
    loadProjectsList();
    
    document.getElementById('teamForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('teamName').value;
        const email = document.getElementById('teamEmail').value;
        const isAdmin = document.getElementById('teamIsAdmin').checked;
        const projectAccess = Array.from(document.querySelectorAll('#projectAccessList input:checked'))
            .map(cb => parseInt(cb.value));

        if (!name || !email) {
            alert('Please fill in all required fields');
            return;
        }

        fetch('/api/teams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name,
                email,
                is_admin: isAdmin,
                project_access: projectAccess
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Limpar formulário
                document.getElementById('teamForm').reset();
                // Recarregar lista
                loadTeamsList();
                alert('User created successfully! Default password is: admin');
            } else {
                throw new Error(data.error || 'Error creating user');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
    });
});

function loadTeamsList() {
    fetch('/api/teams')
        .then(response => response.json())
        .then(teams => {
            const teamsList = document.getElementById('teamsList');
            teamsList.innerHTML = teams.map(team => `
                <div class="team-item fence">
                    <div class="team-card">
                        <div class="team-info">
                            <div class="team-name">${team.name}</div>
                            <div class="team-meta">
                                <span class="team-email">${team.email}</span>
                                ${team.is_admin ? '<span class="badge badge-admin">Admin</span>' : ''}
                            </div>
                            <div class="team-projects">
                                ${team.project_access.map(projectId => 
                                    `<span class="badge badge-project">Project ${projectId}</span>`
                                ).join('')}
                            </div>
                        </div>
                        <div class="team-actions">
                            <button onclick="editTeam(${team.id})" class="edit-btn">Edit</button>
                            <button onclick="deleteTeam(${team.id})" class="delete-btn">Delete</button>
                        </div>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading users list');
        });
}

function loadProjectsList() {
    fetch('/api/projects')
        .then(response => response.json())
        .then(projects => {
            const projectsList = createProjectCheckboxes(projects, 'projectAccessList');
            const editProjectsList = createProjectCheckboxes(projects, 'editProjectAccessList');
        });
}

function createProjectCheckboxes(projects, containerId) {
    const container = document.getElementById(containerId).querySelector('.project-list');
    container.innerHTML = projects.map(project => `
        <li>
            <div class="checkbox-row">
                <input type="checkbox" id="${containerId}_${project.id}" value="${project.id}">
                <label for="${containerId}_${project.id}">${project.name}</label>
            </div>
        </li>
    `).join('');
}

function editTeam(teamId) {
    fetch(`/api/teams/${teamId}`)
        .then(response => response.json())
        .then(team => {
            document.getElementById('editTeamId').value = team.id;
            document.getElementById('editName').value = team.name;
            document.getElementById('editEmail').value = team.email;
            document.getElementById('editIsAdmin').checked = team.is_admin;
            
            // Marcar projetos com acesso
            team.project_access.forEach(projectId => {
                const checkbox = document.getElementById(`editProjectAccessList_${projectId}`);
                if (checkbox) checkbox.checked = true;
            });
            
            document.getElementById('editModal').style.display = 'block';
        });
}

document.getElementById('editForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const teamId = document.getElementById('editTeamId').value;
    const projectAccess = Array.from(document.querySelectorAll('#editProjectAccessList input:checked'))
        .map(cb => parseInt(cb.value));

    fetch(`/api/teams/${teamId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: document.getElementById('editName').value,
            email: document.getElementById('editEmail').value,
            is_admin: document.getElementById('editIsAdmin').checked,
            project_access: projectAccess
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeModal();
            loadTeamsList();
        } else {
            throw new Error(data.error || 'Error updating user');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message);
    });
});

function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

function deleteTeam(teamId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }

    fetch(`/api/teams/${teamId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTeamsList();
        } else {
            throw new Error(data.error || 'Error deleting user');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message);
    });
}
