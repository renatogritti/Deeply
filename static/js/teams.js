document.addEventListener('DOMContentLoaded', function() {
    loadTeamsList();
    setupFormSubmission();
});

function setupFormSubmission() {
    document.getElementById('teamForm').onsubmit = async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('teamName').value.trim();
        const email = document.getElementById('teamEmail').value.trim();

        if (!name || !email) {
            alert('All fields are required!');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address!');
            return;
        }

        try {
            const response = await fetch('/api/teams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: email
                })
            });

            const result = await response.json();
            if (result.success) {
                document.getElementById('teamName').value = '';
                document.getElementById('teamEmail').value = '';
                loadTeamsList();
            } else {
                alert('Error creating user: ' + result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error creating user');
        }
    };
}

async function loadTeamsList() {
    try {
        const response = await fetch('/api/teams');
        const teams = await response.json();
        
        const teamsList = document.getElementById('teamsList');
        teamsList.innerHTML = teams.map(team => `
            <div class="team-item">
                <div class="team-info">
                    <span class="team-name">${team.name}</span>
                    <span class="team-email">${team.description}</span>
                </div>
                <div class="team-actions">
                    <button onclick="editTeam(${team.id})" class="edit-btn">Edit</button>
                    <button onclick="deleteTeam(${team.id})" class="delete-btn">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading users list');
    }
}

async function deleteTeam(id) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }

    try {
        const response = await fetch(`/api/teams/${id}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.success) {
            loadTeamsList();
        } else {
            alert('Error deleting user: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting user');
    }
}

async function editTeam(id) {
    try {
        const response = await fetch(`/api/teams/${id}`);
        const team = await response.json();
        
        const name = prompt('Enter new name:', team.name);
        const email = prompt('Enter new email:', team.description);
        
        if (!name || !email) return;

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address!');
            return;
        }

        const updateResponse = await fetch(`/api/teams/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                description: email
            })
        });

        const result = await updateResponse.json();
        if (result.success) {
            loadTeamsList();
        } else {
            alert('Error updating user: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error updating user');
    }
}
