document.getElementById('csvFile').addEventListener('change', function(e) {
    const fileName = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');
    
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        fileName.textContent = `📄 ${file.name}`;
        fileName.style.color = '#28a745';
        submitBtn.disabled = false;
        
        if (!file.name.toLowerCase().endsWith('.csv')) {
            fileName.textContent = '⚠️ Por favor selecciona un archivo .csv';
            fileName.style.color = '#dc3545';
            submitBtn.disabled = true;
        }
    } else {
        fileName.textContent = 'Ningún archivo seleccionado';
        fileName.style.color = '#666';
        submitBtn.disabled = true;
    }
});

document.querySelector('.file-input-button').addEventListener('click', function() {
    document.getElementById('csvFile').click();
});

document.getElementById('uploadForm').addEventListener('submit', function() {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.textContent = '📝 Validando CSV...';
    submitBtn.disabled = true;
});