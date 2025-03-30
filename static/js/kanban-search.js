function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    const newSearchInput = searchInput.cloneNode(true);
    searchInput.parentNode.replaceChild(newSearchInput, searchInput);

    let timeout = null;
    newSearchInput.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const searchTerm = this.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.kanban-card');
            let found = 0;

            cards.forEach(card => {
                card.querySelectorAll('.highlight').forEach(el => {
                    el.outerHTML = el.textContent;
                });

                if (!searchTerm) {
                    card.style.display = 'block';
                    found++;
                    return;
                }

                const content = [
                    card.querySelector('h3')?.textContent,
                    card.getAttribute('data-description'),
                    card.querySelector('p')?.textContent,
                    card.querySelector('.card-deadline')?.textContent,
                    ...Array.from(card.querySelectorAll('.card-tag')).map(tag => tag.textContent),
                    ...Array.from(card.querySelectorAll('.user-tag')).map(user => user.textContent)
                ].filter(Boolean).join(' ').toLowerCase();

                const isMatch = content.includes(searchTerm);
                card.style.display = isMatch ? 'block' : 'none';
                
                if (isMatch) {
                    found++;
                    highlightText(card, searchTerm);
                }
            });

            this.placeholder = searchTerm ? 
                `${found} resultado${found !== 1 ? 's' : ''} encontrado${found !== 1 ? 's' : ''}` : 
                'Buscar por título, descrição, tags, usuários...';
        }, 300);
    });
}

function highlightText(card, term) {
    const elements = [
        card.querySelector('h3'),
        card.querySelector('p'),
        ...card.querySelectorAll('.card-tag'),
        ...card.querySelectorAll('.user-tag')
    ].filter(Boolean);

    elements.forEach(el => {
        if (el.textContent.toLowerCase().includes(term)) {
            el.innerHTML = el.textContent.replace(
                new RegExp(`(${term})`, 'gi'),
                '<span class="highlight">$1</span>'
            );
        }
    });
}

document.addEventListener('DOMContentLoaded', setupSearch);
