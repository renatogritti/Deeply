document.addEventListener('DOMContentLoaded', function() {
    loadSharesList();
    setupFormSubmission();
});

function setupFormSubmission() {
    document.getElementById('shareForm').onsubmit = async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('shareEmail').value.trim();
        const message = document.getElementById('shareMessage').value.trim();

        if (!email) {
            alert('Email address is required!');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address!');
            return;
        }

        try {
            const response = await fetch('/api/share', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    message: message
                })
            });

            const result = await response.json();
            if (result.success) {
                document.getElementById('shareEmail').value = '';
                document.getElementById('shareMessage').value = '';
                loadSharesList();
                alert('Board shared successfully!');
            } else {
                alert('Error sharing board: ' + result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error sharing board');
        }
    };
}

async function loadSharesList() {
    try {
        const response = await fetch('/api/shares');
        const shares = await response.json();
        
        const sharesList = document.getElementById('sharesList');
        sharesList.innerHTML = shares.map(share => `
            <div class="share-item">
                <div class="share-info">
                    <span class="share-email">${share.email}</span>
                    <span class="share-date">${new Date(share.created_at).toLocaleDateString()}</span>
                </div>
                <div class="share-actions">
                    <button onclick="resendShare(${share.id})" class="resend-btn">Resend</button>
                    <button onclick="revokeShare(${share.id})" class="delete-btn">Revoke</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading shares list');
    }
}

async function resendShare(id) {
    try {
        const response = await fetch(`/api/share/${id}/resend`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            alert('Share invitation resent successfully!');
            loadSharesList();
        } else {
            alert('Error resending share: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error resending share');
    }
}

async function revokeShare(id) {
    if (!confirm('Are you sure you want to revoke this share?')) {
        return;
    }

    try {
        const response = await fetch(`/api/share/${id}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.success) {
            loadSharesList();
        } else {
            alert('Error revoking share: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error revoking share');
    }
}
