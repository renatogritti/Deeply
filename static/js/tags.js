document.addEventListener('DOMContentLoaded', function() {
    loadTagsList();
    setupFormSubmission();
});

function setupFormSubmission() {
    document.getElementById('tagForm').onsubmit = async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('tagName').value.trim();
        const color = document.getElementById('tagColor').value;

        if (!name) {
            alert('Tag name is required!');
            return;
        }

        try {
            const response = await fetch('/api/tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    color: color
                })
            });

            const result = await response.json();
            if (result.success) {
                document.getElementById('tagName').value = '';
                document.getElementById('tagColor').value = '#1a73e8';
                loadTagsList();
            } else {
                alert('Error creating tag: ' + result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error creating tag');
        }
    };
}

async function loadTagsList() {
    try {
        const response = await fetch('/api/tags');
        const tags = await response.json();
        
        const tagsList = document.getElementById('tagsList');
        tagsList.innerHTML = tags.map(tag => `
            <div class="tag-item">
                <div class="tag-info">
                    <div class="tag-preview" style="background-color: ${tag.color}">
                        ${tag.name}
                    </div>
                </div>
                <div class="tag-actions">
                    <button onclick="editTag(${tag.id})" class="edit-btn">Edit</button>
                    <button onclick="deleteTag(${tag.id})" class="delete-btn">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading tags list');
    }
}

async function deleteTag(id) {
    if (!confirm('Are you sure you want to delete this tag?')) {
        return;
    }

    try {
        const response = await fetch(`/api/tags/${id}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.success) {
            loadTagsList();
        } else {
            alert('Error deleting tag: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting tag');
    }
}

async function editTag(id) {
    try {
        const response = await fetch(`/api/tags/${id}`);
        const tag = await response.json();
        
        const name = prompt('Enter new tag name:', tag.name);
        const color = prompt('Enter new color (hex format):', tag.color);
        
        if (!name || !color) return;

        const updateResponse = await fetch(`/api/tags/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                color: color
            })
        });

        const result = await updateResponse.json();
        if (result.success) {
            loadTagsList();
        } else {
            alert('Error updating tag: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error updating tag');
    }
}
