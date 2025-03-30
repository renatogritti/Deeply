async function requestAIEstimate(description, toastElement, inputElement) {
    if (!description.trim()) {
        toastElement.textContent = "Adicione uma descrição antes de solicitar uma estimativa.";
        toastElement.classList.add("show");
        setTimeout(() => toastElement.classList.remove("show"), 5000);
        return;
    }

    toastElement.textContent = "Analisando estimativa...";
    toastElement.classList.add("show", "loading");

    try {
        const prompt = `Baseado na descrição da tarefa, me passe uma estimativa sumarizada baseado nas melhores práticas. Segue a descrição: ${description}`;
        
        const response = await fetch('/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: prompt })
        });

        if (!response.ok) throw new Error(`HTTP error ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        const formattedResponse = formatAIResponse(data.response);
        toastElement.innerHTML = formattedResponse;
        toastElement.classList.remove("loading");
        
        const timePattern = /(\d+)\s*(?:h|hora|horas)(?:\s*e\s*(\d+)\s*(?:m|min|minutos)?)?/i;
        const match = data.response.match(timePattern);
        
        if (match) {
            let estimatedTime = `${match[1]}h`;
            if (match[2]) estimatedTime += `${match[2]}m`;
            inputElement.value = estimatedTime;
        }
        
        setTimeout(() => toastElement.classList.remove("show"), 15000);
    } catch (error) {
        console.error('Error:', error);
        toastElement.textContent = `Erro ao obter estimativa: ${error.message}`;
        toastElement.classList.remove("loading");
        setTimeout(() => toastElement.classList.remove("show"), 5000);
    }
}

function formatAIResponse(response) {
    response = response.replace(/(\d+\s*(?:h|hora|horas)(?:\s*e\s*\d+\s*(?:m|min|minutos))?)/gi, 
        '<span class="time-estimate">$1</span>');
    response = response.replace(/\n/g, '<br>');
    response = response.replace(/([.,:;!?])([^\s])/g, '$1 $2');
    return response;
}

// Inicialização dos botões AI
document.addEventListener('DOMContentLoaded', function() {
    ['aiEstimateBtn', 'aiEstimateEditBtn'].forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', function() {
                const isEdit = btnId.includes('Edit');
                const prefix = isEdit ? 'edit' : 'new';
                requestAIEstimate(
                    document.getElementById(`${prefix}CardDescription`).value,
                    document.getElementById(`estimate${isEdit ? 'Edit' : ''}Toast`),
                    document.getElementById(`${prefix}CardTempo`)
                );
            });
        }
    });
});
