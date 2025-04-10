/**
 * Sistema de Gerenciamento de Documentos com Controle de Versão
 */
let currentProject = null;
let currentFolder = null;
let breadcrumbHistory = [];

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Carregar projeto da URL se disponível
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('projeto');
    
    if (projectId) {
        document.getElementById('projectFilter').value = projectId;
        loadProjectDocs(projectId);
    }
    
    // Event listeners para uploads de arquivo
    document.getElementById('documentFile').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            document.getElementById('selectedFileName').textContent = e.target.files[0].name;
        }
    });
    
    document.getElementById('versionFile').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            document.getElementById('selectedVersionFileName').textContent = e.target.files[0].name;
        }
    });
});

function loadProjectDocs(projectId) {
    if (!projectId) {
        document.getElementById('folderTree').innerHTML = '';
        document.getElementById('documentsList').innerHTML = '';
        document.getElementById('folderBreadcrumb').innerHTML = '';
        
        currentProject = null;
        currentFolder = null;
        breadcrumbHistory = [];
        
        // Remove o parâmetro projeto da URL
        const url = new URL(window.location.href);
        url.searchParams.delete('projeto');
        history.pushState({}, '', url);
        return;
    }

    // Atualiza a URL com o projeto selecionado
    const url = new URL(window.location.href);
    url.searchParams.set('projeto', projectId);
    history.pushState({}, '', url);

    currentProject = projectId;
    
    // Carrega a estrutura de pastas e documentos raiz do projeto
    fetch(`/api/docs/structure?project_id=${projectId}`)
        .then(response => {
            if (!response.ok) throw new Error(response.statusText);
            return response.json();
        })
        .then(data => {
            // Guarda a pasta atual
            currentFolder = data.folder ? data.folder.id : null;
            
            // Inicializa o breadcrumb
            breadcrumbHistory = [{
                id: data.folder ? data.folder.id : null,
                name: "Home"
            }];
            
            renderBreadcrumb();
            renderFolderTree(data.subfolders);
            renderDocuments(data.documents);
        })
        .catch(error => {
            console.error('Erro ao carregar estrutura do projeto:', error);
            showNotification('Erro ao carregar documentos do projeto', 'error');
        });
}

function showCreateFolderModal() {
    if (!currentProject) {
        showNotification('Selecione um projeto primeiro', 'warning');
        return;
    }
    
    if (!currentFolder) {
        showNotification('Selecione uma pasta primeiro', 'warning');
        return;
    }
    
    document.getElementById('folderName').value = '';
    document.getElementById('folderDescription').value = '';
    showModal('createFolderModal');
}

function showUploadDocumentModal() {
    if (!currentProject) {
        showNotification('Selecione um projeto primeiro', 'warning');
        return;
    }
    
    if (!currentFolder) {
        showNotification('Selecione uma pasta primeiro', 'warning');
        return;
    }
    
    document.getElementById('documentName').value = '';
    document.getElementById('documentDescription').value = '';
    document.getElementById('documentFile').value = '';
    document.getElementById('selectedFileName').textContent = 'Selecionar arquivo...';
    
    showModal('uploadDocumentModal');
}

function loadFolder(folderId) {
    if (!currentProject || !folderId) return;
    
    fetch(`/api/docs/structure?project_id=${currentProject}&folder_id=${folderId}`)
        .then(response => {
            if (!response.ok) throw new Error(response.statusText);
            return response.json();
        })
        .then(data => {
            // Atualiza a pasta atual
            currentFolder = folderId;
            
            // Atualiza o breadcrumb
            if (data.folder) {
                // Verifica se a pasta já está no breadcrumb
                const existingIndex = breadcrumbHistory.findIndex(item => item.id === folderId);
                
                if (existingIndex >= 0) {
                    // Se já existe, remove tudo depois dela
                    breadcrumbHistory = breadcrumbHistory.slice(0, existingIndex + 1);
                } else {
                    // Caso contrário, adiciona ao histórico
                    breadcrumbHistory.push({
                        id: data.folder.id,
                        name: data.folder.name
                    });
                }
                
                renderBreadcrumb();
            }
            
            // Renderiza pastas e documentos
            renderFolderTree(data.subfolders);
            renderDocuments(data.documents);
            
            // Destaca a pasta na árvore
            highlightActiveFolder(folderId);
        })
        .catch(error => {
            console.error('Erro ao carregar pasta:', error);
            showNotification('Erro ao carregar pasta', 'error');
        });
}

function highlightActiveFolder(folderId) {
    const folderItems = document.querySelectorAll('.folder-item');
    
    folderItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-id') == folderId) {
            item.classList.add('active');
        }
    });
}

function renderBreadcrumb() {
    const breadcrumb = document.getElementById('folderBreadcrumb');
    
    if (!breadcrumb) return;
    
    let breadcrumbHTML = '';
    
    breadcrumbHistory.forEach((item, index) => {
        const isLast = index === breadcrumbHistory.length - 1;
        
        if (isLast) {
            breadcrumbHTML += `<div class="breadcrumb-item active">${item.name}</div>`;
        } else {
            breadcrumbHTML += `
                <div class="breadcrumb-item">
                    <span class="breadcrumb-link" onclick="loadFolder(${item.id || 'null'})">${item.name}</span>
                </div>
            `;
        }
    });
    
    breadcrumb.innerHTML = breadcrumbHTML;
}

function renderFolderTree(folders) {
    const tree = document.getElementById('folderTree');
    
    if (!folders || folders.length === 0) {
        tree.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z" />
                </svg>
                <p>Nenhuma pasta encontrada</p>
            </div>
        `;
        return;
    }
    
    let foldersHTML = '';
    
    folders.forEach(folder => {
        const isActive = folder.id === currentFolder;
        
        foldersHTML += `
            <div class="folder-item ${isActive ? 'active' : ''}" data-id="${folder.id}" onclick="loadFolder(${folder.id})">
                <div class="folder-icon">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z" />
                    </svg>
                </div>
                <div class="folder-name">${folder.name}</div>
                <div class="folder-actions">
                    <button class="btn-icon" title="Excluir pasta" onclick="confirmDeleteFolder(event, ${folder.id})">
                        <svg viewBox="0 0 24 24">
                            <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                        </svg>
                    </button>
                </div>
            </div>
        `;
    });
    
    tree.innerHTML = foldersHTML;
}

function renderDocuments(documents) {
    const documentsList = document.getElementById('documentsList');
    
    if (!documents || documents.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M14,17H7V15H14M17,13H7V11H17M17,9H7V7H17M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3Z" />
                </svg>
                <p>Nenhum documento encontrado nesta pasta</p>
            </div>
        `;
        return;
    }
    
    let documentsHTML = '';
    
    documents.forEach(doc => {
        documentsHTML += `
            <div class="document-item">
                <div class="document-header">
                    <div class="document-title">${doc.name}</div>
                </div>
                <div class="document-body">
                    <div class="document-description">${doc.description || 'Sem descrição'}</div>
                    <div class="document-meta">
                        <span>
                            <svg viewBox="0 0 24 24">
                                <path fill="currentColor" d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z" />
                            </svg>
                            ${doc.creator_name}
                        </span>
                        <span>
                            <svg viewBox="0 0 24 24">
                                <path fill="currentColor" d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z" />
                            </svg>
                            ${formatDate(doc.updated_at)}
                        </span>
                        ${doc.latest_version ? `
                        <span>
                            <svg viewBox="0 0 24 24">
                                <path fill="currentColor" d="M17,3L22.25,7.5L17,12L22.25,16.5L17,21V16.5H8.5V21L3.25,16.5L8.5,12L3.25,7.5L8.5,3V7.5H17M17,8.5V6.5H8.5V8.5H17M8.5,15.5H17V13.5H8.5V15.5Z" />
                            </svg>
                            Versão ${doc.latest_version} (${doc.latest_version_by})
                        </span>
                        ` : ''}
                    </div>
                    <div class="document-actions">
                        <button class="btn-sm btn-success" onclick="downloadLatestVersion(${doc.id})">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z" />
                            </svg>
                            Download
                        </button>
                        <button class="btn-sm btn-primary-outline" onclick="showNewVersionModal(${doc.id}, '${doc.name}')">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path fill="currentColor" d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M11,15V12H9V15H6V17H9V20H11V17H14V15H11Z" />
                            </svg>
                            Nova versão
                        </button>
                        <button class="btn-sm btn-primary-outline" onclick="showVersionHistory(${doc.id})">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path fill="currentColor" d="M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3" />
                            </svg>
                            Histórico
                        </button>
                        <button class="btn-sm btn-danger" onclick="confirmDeleteDocument(${doc.id})">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                            </svg>
                            Excluir
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    documentsList.innerHTML = documentsHTML;
}

function createFolder() {
    if (!currentProject) {
        showNotification('Selecione um projeto primeiro', 'warning');
        return;
    }
    
    if (!currentFolder) {
        showNotification('Selecione uma pasta primeiro', 'warning');
        return;
    }
    
    const folderName = document.getElementById('folderName').value.trim();
    const folderDescription = document.getElementById('folderDescription').value.trim();
    
    if (!folderName) {
        showNotification('Nome da pasta é obrigatório', 'warning');
        return;
    }
    
    const folderData = {
        name: folderName,
        description: folderDescription,
        project_id: currentProject,
        parent_id: currentFolder
    };
    
    fetch('/api/docs/folders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(folderData)
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
    })
    .then(data => {
        closeModal('createFolderModal');
        showNotification('Pasta criada com sucesso', 'success');
        loadFolder(currentFolder);
    })
    .catch(error => {
        console.error('Erro ao criar pasta:', error);
        showNotification('Erro ao criar pasta', 'error');
    });
}

function confirmDeleteFolder(event, folderId) {
    event.stopPropagation(); // Evita que clique na pasta
    
    if (confirm('Tem certeza que deseja excluir esta pasta e todo seu conteúdo?')) {
        deleteFolder(folderId);
    }
}

function deleteFolder(folderId) {
    fetch(`/api/docs/folders/${folderId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
    })
    .then(data => {
        showNotification('Pasta excluída com sucesso', 'success');
        
        // Se a pasta excluída for a atual, voltamos para a pasta pai
        if (currentFolder === folderId && breadcrumbHistory.length > 1) {
            breadcrumbHistory.pop(); // Remove a pasta atual
            const parentFolder = breadcrumbHistory[breadcrumbHistory.length - 1];
            loadFolder(parentFolder.id);
        } else {
            // Caso contrário, apenas recarregamos a pasta atual
            loadFolder(currentFolder);
        }
    })
    .catch(error => {
        console.error('Erro ao excluir pasta:', error);
        showNotification('Erro ao excluir pasta', 'error');
    });
}

function uploadDocument() {
    if (!currentProject) {
        showNotification('Selecione um projeto primeiro', 'warning');
        return;
    }
    
    if (!currentFolder) {
        showNotification('Selecione uma pasta primeiro', 'warning');
        return;
    }
    
    const documentName = document.getElementById('documentName').value.trim();
    const documentDescription = document.getElementById('documentDescription').value.trim();
    const documentFile = document.getElementById('documentFile').files[0];
    
    if (!documentName) {
        showNotification('Nome do documento é obrigatório', 'warning');
        return;
    }
    
    if (!documentFile) {
        showNotification('Selecione um arquivo para upload', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('name', documentName);
    formData.append('description', documentDescription);
    formData.append('folder_id', currentFolder);
    formData.append('project_id', currentProject);
    formData.append('file', documentFile);
    
    // Mostra indicador de loading
    showNotification('Enviando documento...', 'info');
    
    fetch('/api/docs/documents', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Erro ao criar documento');
            });
        }
        return response.json();
    })
    .then(data => {
        closeModal('uploadDocumentModal');
        showNotification('Documento criado com sucesso', 'success');
        loadFolder(currentFolder);
    })
    .catch(error => {
        console.error('Erro ao criar documento:', error);
        showNotification(error.message || 'Erro ao criar documento', 'error');
    });
}

function showNewVersionModal(documentId, documentName) {
    document.getElementById('documentNameVersion').textContent = documentName;
    document.getElementById('currentDocumentId').value = documentId;
    document.getElementById('changeDescription').value = '';
    document.getElementById('versionFile').value = '';
    document.getElementById('selectedVersionFileName').textContent = 'Selecionar arquivo...';
    
    showModal('newVersionModal');
}

function uploadVersion() {
    const documentId = document.getElementById('currentDocumentId').value;
    const changeDescription = document.getElementById('changeDescription').value.trim();
    const versionFile = document.getElementById('versionFile').files[0];
    
    if (!changeDescription) {
        showNotification('Descrição das alterações é obrigatória', 'warning');
        return;
    }
    
    if (!versionFile) {
        showNotification('Selecione um arquivo para upload', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('change_description', changeDescription);
    formData.append('file', versionFile);
    
    fetch(`/api/docs/documents/${documentId}/versions`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
    })
    .then(data => {
        closeModal('newVersionModal');
        showNotification('Nova versão enviada com sucesso', 'success');
        loadFolder(currentFolder); // Recarrega documentos para mostrar versão atualizada
    })
    .catch(error => {
        console.error('Erro ao enviar nova versão:', error);
        showNotification('Erro ao enviar nova versão', 'error');
    });
}

function downloadLatestVersion(documentId) {
    window.location.href = `/api/docs/documents/${documentId}/download`;
}

function showVersionHistory(documentId) {
    fetch(`/api/docs/documents/${documentId}?include_versions=true`)
        .then(response => {
            if (!response.ok) throw new Error(response.statusText);
            return response.json();
        })
        .then(data => {
            document.getElementById('historyDocumentName').textContent = data.name;
            document.getElementById('historyDocumentDescription').textContent = data.description || 'Sem descrição';
            
            const versionHistoryElement = document.getElementById('versionHistory');
            
            if (!data.versions || data.versions.length === 0) {
                versionHistoryElement.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24">
                            <path fill="currentColor" d="M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3" />
                        </svg>
                        <p>Nenhuma versão encontrada para este documento</p>
                    </div>
                `;
            } else {
                let versionsHTML = '';
                
                data.versions.forEach(version => {
                    versionsHTML += `
                        <div class="version-item">
                            <div class="version-header">
                                <div class="version-number">Versão ${version.version_number}</div>
                                <div class="version-date">${formatDate(version.created_at)}</div>
                            </div>
                            ${version.change_description ? `
                                <div class="version-description">${version.change_description}</div>
                            ` : ''}
                            <div class="version-meta">
                                <span>Enviado por: ${version.uploader_name}</span>
                                <span>Arquivo: ${version.file_name}</span>
                                <span>Tamanho: ${formatFileSize(version.file_size)}</span>
                            </div>
                            <div class="version-actions">
                                <button class="version-download" onclick="downloadVersionFile(${documentId}, ${version.id})">
                                    <svg viewBox="0 0 24 24" width="16" height="16">
                                        <path fill="currentColor" d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z" />
                                    </svg>
                                    Download
                                </button>
                            </div>
                        </div>
                    `;
                });
                
                versionHistoryElement.innerHTML = versionsHTML;
            }
            
            showModal('versionHistoryModal');
        })
        .catch(error => {
            console.error('Erro ao carregar histórico de versões:', error);
            showNotification('Erro ao carregar histórico de versões', 'error');
        });
}

function downloadVersionFile(documentId, versionId) {
    window.location.href = `/api/docs/documents/${documentId}/versions/${versionId}/download`;
}

function confirmDeleteDocument(documentId) {
    if (confirm('Tem certeza que deseja excluir este documento e todas suas versões?')) {
        deleteDocument(documentId);
    }
}

function deleteDocument(documentId) {
    fetch(`/api/docs/documents/${documentId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
    })
    .then(data => {
        showNotification('Documento excluído com sucesso', 'success');
        loadFolder(currentFolder); // Recarrega para atualizar a lista
    })
    .catch(error => {
        console.error('Erro ao excluir documento:', error);
        showNotification('Erro ao excluir documento', 'error');
    });
}

// Funções Utilitárias
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0 || !bytes) return '0 B';
    
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
}

function showNotification(message, type = 'info') {
    // Implementação simplificada - só alerta
    alert(message);
    
    // Uma implementação mais elegante seria criar elementos visuais como toasts
    // ou notificações que desaparecem sozinhas
}
