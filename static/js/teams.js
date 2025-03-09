document.addEventListener('DOMContentLoaded', function() {
    loadTeamsList();
    
    document.getElementById('teamForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('teamName').value;
        const email = document.getElementById('teamEmail').value;

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
                name: name,
                email: email,
                description: '' // opcional
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
                <div class="team-item">
                    <div class="team-info">
                        <div class="team-name">${team.name}</div>
                        <div class="team-email">${team.email}</div>
                    </div>
                    <div class="team-actions">
                        <button onclick="editTeam(${team.id})" class="edit-btn">Edit</button>
                        <button onclick="deleteTeam(${team.id})" class="delete-btn">Delete</button>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading users list');
        });
}

function editTeam(teamId) {
    // ... existing code ...
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
