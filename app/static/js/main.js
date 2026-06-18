function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    const current = html.getAttribute('data-theme');

    if (current === 'light') {
        html.setAttribute('data-theme', 'dark');
        icon.className = 'fas fa-sun';
        localStorage.setItem('theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
        icon.className = 'fas fa-moon';
        localStorage.setItem('theme', 'light');
    }
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = document.getElementById('theme-icon');
    if (icon) icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
});

// Auto-dismiss alerts after 5 seconds with smooth fade
function autoDismissAlerts() {
    document.querySelectorAll('.alert').forEach(alertEl => {
        setTimeout(() => {
            alertEl.classList.add('fade-out');
            setTimeout(() => {
                try {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
                    bsAlert.close();
                } catch(e) {
                    alertEl.remove();
                }
            }, 1000);
        }, 5000);
    });
}

document.addEventListener('DOMContentLoaded', autoDismissAlerts);
setTimeout(autoDismissAlerts, 500);
