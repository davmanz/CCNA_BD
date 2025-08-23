// Animar la barra de progreso al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const progressBar = document.getElementById('progressBar');
    const scoreData = JSON.parse(document.getElementById('score-data').textContent);
    
    if (progressBar) {
        // Animar la barra de progreso
        setTimeout(function() {
            progressBar.style.width = scoreData + '%';
        }, 500);
    }
});