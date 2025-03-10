let currentProject = null;
let currentPath = '';
let selectedFolder = ''; // Nova variável para controlar a pasta selecionada

document.addEventListener('DOMContentLoaded', function() {
    const projectFilter = document.getElementById('projectFilter');
    if (projectFilter && projectFilter.value) {
        loadProjectDocs(projectFilter.value);
    }
});

function loadProjectDocs(projectId) {
    if (!projectId) {
        currentProject = null;
        currentPath = '';
        document.getElementById('folderTree').innerHTML = '';
        document.getElementById('filesList').innerHTML = '';
        return;
    }

    currentProject = projectId;
    currentPath = `Docs/Projects/${projectId}`;
    selectedFolder = '';
    
    fetch(`/api/docs/${projectId}/structure`)
        .then(response => response.json())
        .then(data => {
            renderFolderTree(data.folders);
            renderFiles(data.files);
        })
        .catch(error => {
            console.error('Error loading project docs:', error);
            alert('Error loading project documents');
        });
}

function openFolder(folderPath) {
    selectedFolder = folderPath;
    const allFolders = document.querySelectorAll('.folder-item');
    allFolders.forEach(f => f.classList.remove('active'));
    
    // Destacar pasta selecionada
    const folder = document.querySelector(`.folder-item[data-path="${folderPath}"]`);
    if (folder) folder.classList.add('active');

    // Atualizar arquivos da pasta
    fetch(`/api/docs/${currentProject}/structure?folder=${encodeURIComponent(folderPath)}`)
        .then(response => response.json())
        .then(data => {
            renderFiles(data.files);
        })
        .catch(error => {
            console.error('Error loading folder:', error);
            alert('Error loading folder contents');
        });
}

function reloadCurrentFolder() {
    const currentFolderPath = selectedFolder || currentPath;
    fetch(`/api/docs/${currentProject}/structure?folder=${encodeURIComponent(currentFolderPath)}`)
        .then(response => response.json())
        .then(data => {
            renderFiles(data.files);
        })
        .catch(error => {
            console.error('Error reloading folder:', error);
            alert('Error reloading folder contents');
        });
}

function renderFolderTree(folders) {
    const tree = document.getElementById('folderTree');
    tree.innerHTML = buildFolderHTML(folders);
}

function buildFolderHTML(folders, path = '') {
    let html = '<ul class="folder-list">';
    folders.forEach(folder => {
        const fullPath = folder.path || (path ? `${path}/${folder.name}` : folder.name);
        html += `
            <li class="folder-item" onclick="openFolder('${fullPath}')" data-path="${fullPath}">
                <svg viewBox="0 0 24 24" width="18" height="18">
                    <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z" />
                </svg>
                ${folder.name}
            </li>
        `;
        if (folder.subfolders && folder.subfolders.length > 0) {
            html += buildFolderHTML(folder.subfolders, fullPath);
        }
    });
    html += '</ul>';
    return html;
}

function renderFiles(files) {
    const filesList = document.getElementById('filesList');
    filesList.innerHTML = files.map(file => `
        <div class="file-item">
            <span>${file.name}</span>
            <div class="file-controls">
                <button onclick="downloadFile('${encodeURIComponent(file.path)}')" class="btn-download">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                        <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                    </svg>
                    Download
                </button>
                <button onclick="deleteFile('${encodeURIComponent(file.path)}')" class="btn-delete">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                        <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                    </svg>
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

function createFolder() {
    if (!currentProject) {
        alert('Please select a project first');
        return;
    }
    document.getElementById('createFolderModal').style.display = 'block';
}

function confirmCreateFolder() {
    const folderName = document.getElementById('folderName').value.trim();
    if (!folderName) return;

    fetch('/api/docs/folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            project_id: currentProject,
            path: currentPath,
            name: folderName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadProjectDocs(currentProject);
            closeModal('createFolderModal');
        }
    });
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Modificar o event listener do upload
document.getElementById('fileUpload').addEventListener('change', function(e) {
    if (!currentProject) {
        alert('Please select a project first');
        return;
    }

    const files = e.target.files;
    const formData = new FormData();
    
    for (let file of files) {
        formData.append('files[]', file);
    }

    // Usar o caminho da pasta selecionada ou o caminho raiz do projeto
    const uploadPath = selectedFolder ? 
        `${currentPath}/${selectedFolder}` : 
        currentPath;
    
    formData.append('path', uploadPath);

    fetch('/api/docs/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            reloadCurrentFolder(); // Usar nova função para recarregar
        }
    })
    .catch(error => {
        console.error('Error uploading files:', error);
        alert('Error uploading files');
    });
});

function downloadFile(path) {
    try {
        window.location.href = `/api/docs/download?path=${path}`;
    } catch (error) {
        console.error('Error downloading file:', error);
        alert('Error downloading file');
    }
}

function deleteFile(path) {
    if (!confirm('Are you sure you want to delete this file?')) return;

    fetch('/api/docs/file', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: decodeURIComponent(path) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Recarrega apenas a pasta atual
            if (selectedFolder) {
                openFolder(selectedFolder);
            } else {
                loadProjectDocs(currentProject);
            }
        } else {
            throw new Error(data.error || 'Failed to delete file');
        }
    })
    .catch(error => {
        console.error('Error deleting file:', error);
        alert('Error deleting file');
    });
}

function updateFolderTree(folders) {
    const folderTree = document.getElementById('folderTree');
    folderTree.innerHTML = folders.map(folder => `
        <div class="folder-item" onclick="selectFolder(${folder.id})">
            <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
            </svg>
            <span>${folder.name}</span>
        </div>
    `).join('');
}
