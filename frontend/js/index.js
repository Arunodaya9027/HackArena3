
// Check backend health
async function checkHealth() {
    try {
        const javaRes = await fetch('http://localhost:8085/api/health', { method: 'GET' });
        const javaStatus = document.getElementById('java-status');
        if (javaRes.ok) {
            javaStatus.classList.remove('offline');
        } else {
            javaStatus.classList.add('offline');
        }
    } catch (e) {
        document.getElementById('java-status').classList.add('offline');
    }

    try {
        const pythonRes = await fetch('http://localhost:8002/api/health', { method: 'GET' });
        const pythonStatus = document.getElementById('python-status');
        if (pythonRes.ok) {
            pythonStatus.classList.remove('offline');
        } else {
            pythonStatus.classList.add('offline');
        }
    } catch (e) {
        document.getElementById('python-status').classList.add('offline');
    }
}

// Check on load and every 10 seconds
checkHealth();
setInterval(checkHealth, 10000);