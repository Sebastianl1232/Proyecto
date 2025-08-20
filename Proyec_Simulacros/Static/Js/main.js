// Funciones JavaScript globales

// Formatear tiempo en minutos:segundos
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Mostrar notificación
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
    } text-white`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Confirmar antes de salir de la página durante una prueba
function setupBeforeUnload() {
    window.addEventListener('beforeunload', function(e) {
        if (document.querySelector('#timer')) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    setupBeforeUnload();
    
    // Animar números en resultados
    const animateNumbers = () => {
        const numbers = document.querySelectorAll('.animate-number');
        numbers.forEach(num => {
            const target = parseFloat(num.textContent);
            const duration = 1000;
            const start = 0;
            const increment = target / (duration / 16);
            let current = start;
            
            const updateNumber = () => {
                current += increment;
                if (current < target) {
                    num.textContent = current.toFixed(1);
                    requestAnimationFrame(updateNumber);
                } else {
                    num.textContent = target.toFixed(1);
                }
            };
            
            updateNumber();
        });
    };
    
    // Ejecutar animación si estamos en página de resultados
    if (document.querySelector('.result-card')) {
        setTimeout(animateNumbers, 100);
    }
});

// Utilidades para gráficos (si se agregan en el futuro)
const ChartUtils = {
    createPieChart: function(canvasId, data, colors) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const total = data.reduce((sum, value) => sum + value, 0);
        let currentAngle = -Math.PI / 2;
        
        data.forEach((value, index) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            
            ctx.beginPath();
            ctx.moveTo(canvas.width / 2, canvas.height / 2);
            ctx.arc(canvas.width / 2, canvas.height / 2, Math.min(canvas.width, canvas.height) / 2 - 10, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            
            ctx.fillStyle = colors[index];
            ctx.fill();
            
            currentAngle += sliceAngle;
        });
    }
};