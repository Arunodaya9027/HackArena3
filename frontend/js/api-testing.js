const JAVA_URL = 'http://localhost:8085';
const PYTHON_URL = 'http://localhost:8002';

// Check server status
async function checkAllServers() {
    addLog('info', 'Checking server status...');
    await checkServer(JAVA_URL, 'status-java');
    await checkServer(PYTHON_URL, 'status-python');
}

async function checkServer(url, dotId) {
    try {
        const response = await fetch(`${url}/api/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        const dot = document.getElementById(dotId);
        if (response.ok) {
            dot.classList.remove('offline');
            dot.classList.add('online');
            addLog('success', `${url} is ONLINE`);
        } else {
            throw new Error('Server returned error');
        }
    } catch (error) {
        const dot = document.getElementById(dotId);
        dot.classList.remove('online');
        dot.classList.add('offline');
        addLog('error', `${url} is OFFLINE`);
    }
}

// Test endpoints
async function testHealth() {
    const server = document.getElementById('health-server').value;
    await makeRequest('GET', `${server}/api/health`, null, 'response-health');
}

async function testWktProcess() {
    const wktContent = document.getElementById('wkt-content').value;
    if (!wktContent.trim()) {
        alert('Please enter WKT content');
        return;
    }
    await makeRequest('POST', `${JAVA_URL}/api/wkt/process`, { wktContent }, 'response-wkt');
}

async function testFeatureDetails() {
    const id = document.getElementById('feature-id').value;
    if (!id.trim()) {
        alert('Please enter feature ID');
        return;
    }
    await makeRequest('GET', `${JAVA_URL}/api/features/${id}`, null, 'response-feature');
}

async function testDisplacement() {
    const json = document.getElementById('displacement-json').value;
    if (!json.trim()) {
        alert('Please enter features JSON');
        return;
    }
    try {
        const data = JSON.parse(json);
        await makeRequest('POST', `${JAVA_URL}/api/displacement`, data, 'response-displacement');
    } catch (e) {
        alert('Invalid JSON: ' + e.message);
    }
}

async function testOsmFetch() {
    const minLat = parseFloat(document.getElementById('bbox-minlat').value);
    const minLng = parseFloat(document.getElementById('bbox-minlng').value);
    const maxLat = parseFloat(document.getElementById('bbox-maxlat').value);
    const maxLng = parseFloat(document.getElementById('bbox-maxlng').value);
    
    if (isNaN(minLat) || isNaN(minLng) || isNaN(maxLat) || isNaN(maxLng)) {
        alert('Please enter all bounding box coordinates');
        return;
    }
    
    await makeRequest('POST', `${JAVA_URL}/api/osm/fetch`, 
        { minLat, minLng, maxLat, maxLng }, 'response-osm');
}

async function testRoute() {
    const aLat = parseFloat(document.getElementById('route-a-lat').value);
    const aLng = parseFloat(document.getElementById('route-a-lng').value);
    const bLat = parseFloat(document.getElementById('route-b-lat').value);
    const bLng = parseFloat(document.getElementById('route-b-lng').value);
    
    if (isNaN(aLat) || isNaN(aLng) || isNaN(bLat) || isNaN(bLng)) {
        alert('Please enter all coordinates');
        return;
    }
    
    await makeRequest('POST', `${JAVA_URL}/api/route/calculate`,
        { pointA: { lat: aLat, lng: aLng }, pointB: { lat: bLat, lng: bLng } },
        'response-route');
}

// Generic request handler
async function makeRequest(method, url, body, responseId) {
    const startTime = Date.now();
    const responseDiv = document.getElementById(responseId);
    
    try {
        addLog('info', `${method} ${url}`);
        
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(url, options);
        const duration = Date.now() - startTime;
        const data = await response.json();
        
        // Display response
        responseDiv.style.display = 'block';
        responseDiv.innerHTML = `
            <div class="response-header">
                <span class="status-code status-${response.status}">${response.status} ${response.statusText}</span>
                <span class="response-time">${duration}ms</span>
            </div>
            <div class="response-body">${JSON.stringify(data, null, 2)}</div>
        `;
        
        if (response.ok) {
            addLog('success', `${method} ${url} → ${response.status} (${duration}ms)`);
        } else {
            addLog('error', `${method} ${url} → ${response.status} ${data.error || ''}`);
        }
        
    } catch (error) {
        const duration = Date.now() - startTime;
        addLog('error', `${method} ${url} → FAILED: ${error.message}`);
        
        responseDiv.style.display = 'block';
        responseDiv.innerHTML = `
            <div class="response-header">
                <span class="status-code status-500">ERROR</span>
                <span class="response-time">${duration}ms</span>
            </div>
            <div class="response-body" style="color: var(--danger);">${error.message}</div>
        `;
    }
}

// Logging
function addLog(type, message) {
    const logsContainer = document.getElementById('logs-container');
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span>${message}`;
    logsContainer.appendChild(entry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function clearLogs() {
    const logsContainer = document.getElementById('logs-container');
    logsContainer.innerHTML = '<div class="log-entry log-info"><span class="log-timestamp">[CLEARED]</span>Logs cleared.</div>';
}

// Auto-check servers on load
setTimeout(checkAllServers, 500);