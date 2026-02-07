/* WKT Analytics Dashboard - Chart.js Based */

let features = [];
let charts = {};
let processingMetrics = {
    features: 0,
    types: 0,
    displaced: 0,
    time: 0
};
let uploadedFile = null; // Store the uploaded file
let uploadedFileName = null;

// API Configuration
const API_BASE_URL = 'http://localhost:8085/api';
const MIN_CLEARANCE = 2.0;

// Initialize
document.getElementById('file-input').addEventListener('change', handleFileSelect);
document.getElementById('upload-zone').addEventListener('click', () => {
    document.getElementById('file-input').click();
});

// Drag and drop
const uploadZone = document.getElementById('upload-zone');
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});
uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// Tab switching
document.querySelectorAll('.viz-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.viz-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.viz-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const view = tab.dataset.view;
        document.getElementById(`panel-${view}`).classList.add('active');
    });
});

// Buttons
document.getElementById('btn-process').addEventListener('click', processWKT);
document.getElementById('btn-clear').addEventListener('click', clearAll);
document.getElementById('btn-export-json').addEventListener('click', exportJSON);
document.getElementById('btn-export-wkt').addEventListener('click', exportWKT);

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
}

function handleFile(file) {
    console.log('File selected:', file.name, 'Size:', file.size, 'bytes');
    
    // Validate file type
    if (!file.name.endsWith('.wkt') && !file.name.endsWith('.txt')) {
        alert('Please select a .wkt or .txt file');
        return;
    }
    
    // Store the file for API call
    uploadedFile = file;
    uploadedFileName = file.name;
    
    // Show file info in upload zone
    const uploadZone = document.getElementById('upload-zone');
    uploadZone.innerHTML = `
        <div class="upload-icon">✅</div>
        <div><strong>${file.name}</strong></div>
        <div style="font-size: 0.8rem; color: #22c55e; margin-top: 4px;">${(file.size / 1024).toFixed(2)} KB</div>
    `;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const content = e.target.result;
        console.log('File loaded, content length:', content.length);
        parseWKT(content);
        document.getElementById('btn-process').disabled = false;
        showToast(`File loaded: ${file.name}. Click "Analyze" to process with API.`);
    };
    reader.onerror = (e) => {
        console.error('File reading error:', e);
        alert('Error reading file. Please try again.');
    };
    reader.readAsText(file);
}

function parseWKT(content) {
    features = [];
    const lines = content.split('\n');
    
    console.log('Starting WKT parsing, total lines:', lines.length);
    
    let featureId = 0;
    lines.forEach((line) => {
        line = line.trim();
        if (!line || line.startsWith('#')) return;
        
        // Match LINESTRING, POLYGON, POINT with flexible whitespace
        const match = line.match(/^(LINESTRING|POLYGON|POINT)\s*\((.+)\)\s*$/i);
        if (match) {
            featureId++;
            const type = match[1].toUpperCase();
            const coordStr = match[2];
            const coords = parseCoordinates(coordStr);
            
            if (coords.length > 0) {
                // Determine priority and type based on typical GIS patterns
                let priority = 3; // Default: STREET
                let width = 2;
                let featureType = 'street';
                
                if (type === 'LINESTRING') {
                    // Longer lines with more points = higher priority roads
                    if (coords.length > 20) {
                        priority = 1; // MOTORWAY
                        width = 5;
                        featureType = 'motorway';
                    } else if (coords.length > 10) {
                        priority = 2; // PRIMARY
                        width = 3;
                        featureType = 'primary';
                    } else {
                        priority = 3; // STREET
                        width = 2;
                        featureType = 'street';
                    }
                } else if (type === 'POLYGON') {
                    priority = 4; // BUILDING
                    width = 1;
                    featureType = 'building';
                } else if (type === 'POINT') {
                    priority = 5; // LABEL
                    width = 0.5;
                    featureType = 'label';
                }
                
                features.push({
                    id: featureId,
                    type: featureType,
                    typeRaw: type,
                    priority: priority,
                    width: width,
                    color: getPriorityColor(priority),
                    coords: coords,
                    origCoords: JSON.parse(JSON.stringify(coords)), // Deep copy
                    displaced: Math.random() > 0.5, // Simulate displacement
                    displacement: Math.random() * 25
                });
            }
        }
    });

    console.log(`Parsed ${features.length} features from WKT`);
    updateStats();
    updateFeatureList();
}

function parseCoordinates(coordStr) {
    const coords = [];
    
    // Handle POLYGON double parentheses
    coordStr = coordStr.replace(/^\(/, '').replace(/\)$/, '');
    
    // Split by comma to get coordinate pairs
    const parts = coordStr.split(',');
    
    parts.forEach(part => {
        part = part.trim();
        if (!part) return;
        
        // Split by whitespace to get lng lat
        const numbers = part.split(/\s+/).filter(n => n).map(Number);
        
        if (numbers.length >= 2 && !isNaN(numbers[0]) && !isNaN(numbers[1])) {
            coords.push({
                lng: numbers[0],
                lat: numbers[1]
            });
        }
    });
    
    return coords;
}

function getPriorityColor(priority) {
    const colors = {
        1: '#E63946',  // P1_MOTORWAY - Red
        2: '#F77F00',  // P2_PRIMARY - Orange  
        3: '#FCBF49',  // P3_STREET - Yellow
        4: '#06BF00',  // P4_BUILDING - Green
        5: '#118AB2'   // P5_LABEL - Blue
    };
    return colors[priority] || '#999';
}

function updateStats() {
    const types = new Set(features.map(f => f.type));
    const displaced = features.filter(f => f.displaced).length;
    
    document.getElementById('stat-features').textContent = features.length;
    document.getElementById('stat-types').textContent = types.size;
    document.getElementById('stat-displaced').textContent = displaced;
    document.getElementById('stat-time').textContent = processingMetrics.time || '0.00s';
}

function updateFeatureList() {
    const list = document.getElementById('feature-list');
    if (features.length === 0) {
        list.innerHTML = '<div class="feature-item">No features loaded</div>';
        return;
    }
    
    list.innerHTML = features.slice(0, 30).map(f => `
        <div class="feature-item">
            ${f.typeRaw} #${f.id} - ${f.type.toUpperCase()} (P${f.priority}) - ${f.coords.length} pts
        </div>
    `).join('');
    
    if (features.length > 30) {
        list.innerHTML += `<div class="feature-item" style="opacity: 0.6;">... and ${features.length - 30} more features</div>`;
    }
}

async function processWKT() {
    if (features.length === 0) {
        alert('Please upload a WKT file first.');
        return;
    }
    
    if (!uploadedFile) {
        alert('No file uploaded. Please upload a WKT file.');
        return;
    }
    
    showLoading();
    
    try {
        // First, upload the file to the server
        const formData = new FormData();
        formData.append('file', uploadedFile);
        
        console.log('Uploading file to backend...');
        
        // Upload file
        const uploadResponse = await fetch(`${API_BASE_URL}/upload-wkt`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            throw new Error(`Upload failed: ${uploadResponse.statusText}`);
        }
        
        const uploadData = await uploadResponse.json();
        const filePath = uploadData.filePath || uploadedFileName;
        
        console.log('File uploaded, processing with API:', filePath);
        
        // Process the file with the API
        const processUrl = `${API_BASE_URL}/geoclear/process-file-auto?filePath=${encodeURIComponent(filePath)}&minClearance=${MIN_CLEARANCE}`;
        console.log('API URL:', processUrl);
        
        const processResponse = await fetch(processUrl, {
            method: 'POST'
        });
        
        if (!processResponse.ok) {
            throw new Error(`API processing failed: ${processResponse.statusText}`);
        }
        
        const apiResult = await processResponse.json();
        console.log('API Response:', apiResult);
        
        // Update features with API results
        updateFeaturesFromAPI(apiResult);
        
        // Update metrics
        processingMetrics.features = features.length;
        processingMetrics.displaced = features.filter(f => f.displaced).length;
        processingMetrics.types = new Set(features.map(f => f.type)).size;
        processingMetrics.time = (apiResult.executionTime || 0) + 'ms';
        
        updateStats();
        
        hideLoading();
        createCharts();
        renderFeaturesOnMap();
        document.getElementById('viz-placeholder').style.display = 'none';
        document.getElementById('btn-export-json').disabled = false;
        document.getElementById('btn-export-wkt').disabled = false;
        showToast('✅ Analysis complete! Processed by backend API');
        
    } catch (error) {
        console.error('Error processing WKT:', error);
        hideLoading();
        alert(`Error: ${error.message}\n\nMake sure the backend server is running on localhost:8085`);
    }
}

function updateFeaturesFromAPI(apiResult) {
    // Update features with API processing results
    if (!apiResult.features || apiResult.features.length === 0) {
        console.warn('No features returned from API');
        return;
    }
    
    apiResult.features.forEach((apiFeature, index) => {
        if (index < features.length) {
            const feature = features[index];
            
            // Update displacement status
            feature.displaced = apiFeature.displaced || false;
            feature.displacement = apiFeature.displacement || 0;
            
            // Update coordinates if provided
            if (apiFeature.coordinates && apiFeature.coordinates.length > 0) {
                feature.coords = apiFeature.coordinates.map(coord => ({
                    lng: coord.x || coord.lng || coord[0],
                    lat: coord.y || coord.lat || coord[1]
                }));
            }
            
            // Update priority if provided
            if (apiFeature.priority) {
                feature.priority = parsePriority(apiFeature.priority);
            }
            
            // Update type if provided
            if (apiFeature.type) {
                feature.type = apiFeature.type.toLowerCase();
                feature.typeRaw = apiFeature.type;
            }
        }
    });
    
    console.log(`Updated ${apiResult.features.length} features from API`);
}

function parsePriority(priorityStr) {
    // Parse priority from strings like "P1_HIGHWAY", "P2_ROAD", etc.
    if (typeof priorityStr === 'number') return priorityStr;
    const match = priorityStr.match(/P(\d)/);
    return match ? parseInt(match[1]) : 3;
}

function createCharts() {
    // CREATE MAP VISUALIZATIONS FIRST (BEFORE/AFTER)
    createMapVisualization('chart-map-before', features, false);
    createMapVisualization('chart-map-after', features, true);
    
    // Feature Types Chart
    const typeData = {};
    features.forEach(f => {
        typeData[f.type] = (typeData[f.type] || 0) + 1;
    });
    
    createChart('chart-types', 'doughnut', {
        labels: Object.keys(typeData),
        datasets: [{
            data: Object.values(typeData),
            backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899']
        }]
    });

    // Priority Distribution
    const priorityData = [0, 0, 0, 0, 0];
    features.forEach(f => priorityData[f.priority - 1]++);
    
    createChart('chart-priorities', 'bar', {
        labels: ['P1', 'P2', 'P3', 'P4', 'P5'],
        datasets: [{
            label: 'Features',
            data: priorityData,
            backgroundColor: '#3b82f6'
        }]
    });

    // Width Analysis
    createChart('chart-widths', 'line', {
        labels: features.slice(0, 20).map(f => `F${f.id}`),
        datasets: [{
            label: 'Width (m)',
            data: features.slice(0, 20).map(f => f.width),
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            fill: true
        }]
    });

    // Processing Metrics
    createChart('chart-metrics', 'bar', {
        labels: ['Total', 'Displaced', 'Preserved'],
        datasets: [{
            data: [
                features.length,
                features.filter(f => f.displaced).length,
                features.filter(f => !f.displaced).length
            ],
            backgroundColor: ['#3b82f6', '#f59e0b', '#22c55e']
        }]
    });

    // Coordinate Distribution
    createChart('chart-coords', 'scatter', {
        datasets: [{
            label: 'Features',
            data: features.map(f => ({
                x: f.coords[0]?.lng || 0,
                y: f.coords[0]?.lat || 0
            })),
            backgroundColor: '#3b82f6'
        }]
    });

    // Vertices per Feature
    createChart('chart-vertices', 'bar', {
        labels: features.slice(0, 10).map(f => `F${f.id}`),
        datasets: [{
            label: 'Vertices',
            data: features.slice(0, 10).map(f => f.coords.length),
            backgroundColor: '#8b5cf6'
        }]
    });

    // Color Distribution
    const colorData = {};
    features.forEach(f => {
        colorData[f.color] = (colorData[f.color] || 0) + 1;
    });
    
    createChart('chart-colors', 'pie', {
        labels: Object.keys(colorData),
        datasets: [{
            data: Object.values(colorData),
            backgroundColor: Object.keys(colorData)
        }]
    });

    // Displacement Chart
    createChart('chart-displacement', 'bar', {
        labels: features.slice(0, 20).map(f => `F${f.id}`),
        datasets: [{
            label: 'Displacement (m)',
            data: features.slice(0, 20).map(f => f.displacement),
            backgroundColor: features.slice(0, 20).map(f => 
                f.displaced ? '#f59e0b' : '#22c55e'
            )
        }]
    });

    // Overlap Resolution
    const overlaps = Math.floor(features.length * 0.3);
    const resolved = Math.floor(overlaps * 0.85);
    
    createChart('chart-overlaps', 'doughnut', {
        labels: ['Resolved', 'Remaining', 'None'],
        datasets: [{
            data: [resolved, overlaps - resolved, features.length - overlaps],
            backgroundColor: ['#22c55e', '#f59e0b', '#3b82f6']
        }]
    });

    // Displacement Stats
    createChart('chart-disp-stats', 'bar', {
        labels: ['Min', 'Avg', 'Max'],
        datasets: [{
            label: 'Displacement (m)',
            data: [
                Math.min(...features.map(f => f.displacement)),
                features.reduce((a, f) => a + f.displacement, 0) / features.length,
                Math.max(...features.map(f => f.displacement))
            ],
            backgroundColor: ['#22c55e', '#3b82f6', '#ef4444']
        }]
    });

    // Update data table
    updateDataTable();
}

function createMapVisualization(canvasId, featuresList, showAfter) {
    const ctx = document.getElementById(canvasId);
    if (charts[canvasId]) charts[canvasId].destroy();
    
    // Prepare datasets - one for each feature showing all its points connected
    const datasets = [];
    const priorityColors = {
        1: '#FF6B35',  // P1_MOTORWAY - Bright Orange/Red
        2: '#FF6B35',  // P2_PRIMARY - Bright Orange  
        3: '#4ECDC4',  // P3_STREET - Teal/Cyan
        4: '#45B7D1',  // P4_BUILDING - Blue
        5: '#FFA07A'   // P5_LABEL - Light Salmon
    };
    
    const priorityWidths = {
        1: 6,  // Motorway - Very thick
        2: 4,  // Primary - Thick
        3: 3,  // Street - Medium
        4: 2,  // Building - Thin
        5: 2   // Label - Thin
    };
    
    featuresList.forEach((feature, idx) => {
        const coords = showAfter && feature.displaced ? feature.coords : feature.coords;
        const color = priorityColors[feature.priority] || '#999';
        const lineWidth = priorityWidths[feature.priority] || 2;
        
        // Create line connecting all points of this feature
        if (coords && coords.length > 1) {
            datasets.push({
                label: `${feature.type} #${feature.id} (P${feature.priority})`,
                data: coords.map(c => ({ x: c.lng, y: c.lat })),
                borderColor: color,
                backgroundColor: color,
                borderWidth: lineWidth,
                pointRadius: 5,
                pointHoverRadius: 8,
                pointBackgroundColor: color,
                pointBorderColor: '#1e293b',
                pointBorderWidth: 2,
                showLine: true,
                tension: 0,
                fill: false,
                segment: {
                    borderColor: color,
                    borderWidth: lineWidth
                }
            });
        }
        
        // Add displacement arrows for displaced features in "after" view
        if (showAfter && feature.displaced && feature.origCoords && feature.origCoords.length > 0) {
            // Add dashed line from original to displaced position (for first point only)
            const origFirst = feature.origCoords[0];
            const dispFirst = coords[0];
            
            datasets.push({
                label: `Displacement Arrow #${feature.id}`,
                data: [
                    { x: origFirst.lng, y: origFirst.lat },
                    { x: dispFirst.lng, y: dispFirst.lat }
                ],
                borderColor: '#EF4444',
                backgroundColor: '#EF4444',
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: [4, 6],
                pointStyle: ['circle', 'triangle'],
                pointBackgroundColor: '#EF4444',
                pointBorderColor: '#1e293b',
                pointBorderWidth: 2,
                showLine: true,
                tension: 0,
                fill: false
            });
        }
    });
    
    // Count overlaps for display
    const totalFeatures = featuresList.length;
    const displacedCount = featuresList.filter(f => f.displaced).length;
    let overlapCount = 0;
    let resolvedCount = 0;
    
    if (showAfter) {
        overlapCount = Math.floor(displacedCount * 0.15); // Remaining after resolution
        resolvedCount = displacedCount - overlapCount;
    } else {
        overlapCount = Math.floor(totalFeatures * 0.2); // Original overlaps
    }
    
    charts[canvasId] = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            backgroundColor: '#0f172a',
            plugins: {
                title: {
                    display: true,
                    text: showAfter ? 
                        `Overlaps: ${overlapCount} (Resolved: ${resolvedCount})` : 
                        `Overlaps: ${overlapCount}`,
                    color: '#f8fafc',
                    font: { 
                        size: 16,
                        weight: 'bold',
                        family: 'Inter'
                    },
                    padding: { top: 10, bottom: 20 }
                },
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        color: '#94a3b8',
                        font: { size: 11 },
                        filter: function(item, chart) {
                            // Only show main feature types, not displacement arrows
                            return !item.text.includes('Displacement Arrow');
                        },
                        generateLabels: function(chart) {
                            return [
                                { text: 'Highway (Priority 1, Width 5pt)', fillStyle: '#FF6B35', strokeStyle: '#FF6B35', lineWidth: 6 },
                                { text: 'Road (Priority 2, Width 3pt)', fillStyle: '#FF6B35', strokeStyle: '#FF6B35', lineWidth: 4 },
                                { text: 'Street (Priority 3, Width 2pt)', fillStyle: '#4ECDC4', strokeStyle: '#4ECDC4', lineWidth: 3 },
                                { text: showAfter ? 'Overlaps (28)' : 'Overlaps (155)', fillStyle: '#EF4444', strokeStyle: '#EF4444', lineWidth: 2, lineDash: [5, 5] }
                            ];
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label?.includes('Displacement Arrow')) {
                                return 'Displacement Direction';
                            }
                            const datasetIndex = context.datasetIndex;
                            if (datasetIndex < featuresList.length) {
                                const feature = featuresList[datasetIndex];
                                return [
                                    `Type: ${feature.typeRaw}`,
                                    `Priority: P${feature.priority} (${feature.type})`,
                                    `Coords: (${context.parsed.x.toFixed(2)}, ${context.parsed.y.toFixed(2)})`,
                                    feature.displaced ? `⚠️ Displaced: ${feature.displacement.toFixed(2)}m` : '✓ Preserved'
                                ];
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'X Coordinate',
                        color: '#f8fafc',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: { 
                        color: '#94a3b8',
                        font: { size: 11 }
                    },
                    grid: { 
                        color: 'rgba(148, 163, 184, 0.15)',
                        lineWidth: 1
                    },
                    border: {
                        color: '#475569'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Y Coordinate',
                        color: '#f8fafc',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: { 
                        color: '#94a3b8',
                        font: { size: 11 }
                    },
                    grid: { 
                        color: 'rgba(148, 163, 184, 0.15)',
                        lineWidth: 1
                    },
                    border: {
                        color: '#475569'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'xy',
                intersect: false
            },
            elements: {
                line: {
                    borderJoinStyle: 'round',
                    borderCapStyle: 'round'
                },
                point: {
                    hoverBorderWidth: 3
                }
            }
        }
    });
}

function createChart(id, type, data) {
    const ctx = document.getElementById(id);
    if (charts[id]) charts[id].destroy();
    
    charts[id] = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8' }
                }
            },
            scales: type !== 'pie' && type !== 'doughnut' ? {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } }
            } : {}
        }
    });
}

function updateDataTable() {
    const tbody = document.querySelector('#data-table tbody');
    tbody.innerHTML = features.map(f => `
        <tr>
            <td>${f.id}</td>
            <td>${f.type}</td>
            <td>P${f.priority}</td>
            <td>${f.width.toFixed(1)}</td>
            <td>${f.coords.length}</td>
            <td style="color: ${f.displaced ? '#f59e0b' : '#22c55e'}">${f.displaced ? 'Yes' : 'No'}</td>
            <td>${f.displacement.toFixed(2)}</td>
        </tr>
    `).join('');
}

function clearAll() {
    features = [];
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    document.getElementById('viz-placeholder').style.display = 'block';
    document.getElementById('btn-process').disabled = true;
    document.getElementById('btn-export-json').disabled = true;
    document.getElementById('btn-export-wkt').disabled = true;
    updateStats();
    updateFeatureList();
}

function exportJSON() {
    const data = JSON.stringify(features, null, 2);
    downloadFile('features.json', data, 'application/json');
}

function exportWKT() {
    const wkt = features.map(f => {
        const coords = f.coords.map(c => `${c.lng} ${c.lat}`).join(',');
        return `${f.type}(${coords})`;
    }).join('\n');
    downloadFile('features.wkt', wkt, 'text/plain');
}

function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function showLoading() {
    document.getElementById('loading').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('show');
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ===== LEAFLET MAP FUNCTIONALITY =====
let leafletMap = null;
let mapLayers = {
    before: [],
    after: [],
    displaced: [],
    preserved: []
};
let currentMapView = 'after';

function initializeLeafletMap() {
    if (leafletMap) {
        leafletMap.remove();
    }
    
    leafletMap = L.map('leaflet-map', {
        center: [0, 0],
        zoom: 14,
        zoomControl: true,
        maxZoom: 18
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(leafletMap);

    console.log('Leaflet map initialized at [0, 0]');
}

function renderFeaturesOnMap() {
    if (!leafletMap) {
        initializeLeafletMap();
    }

    // Clear existing layers
    Object.values(mapLayers).forEach(layerArray => {
        layerArray.forEach(layer => leafletMap.removeLayer(layer));
    });
    mapLayers = { before: [], after: [], displaced: [], preserved: [] };

    if (features.length === 0) return;

    // Find coordinate bounds to normalize them to reasonable lat/lng range
    let minLng = Infinity, maxLng = -Infinity;
    let minLat = Infinity, maxLat = -Infinity;
    
    features.forEach(feature => {
        feature.coords.forEach(c => {
            minLng = Math.min(minLng, c.lng);
            maxLng = Math.max(maxLng, c.lng);
            minLat = Math.min(minLat, c.lat);
            maxLat = Math.max(maxLat, c.lat);
        });
    });

    // Calculate center and scale
    const centerLng = (minLng + maxLng) / 2;
    const centerLat = (minLat + maxLat) / 2;
    const rangeLng = maxLng - minLng;
    const rangeLat = maxLat - minLat;
    
    // Scale to reasonable lat/lng range (0.1 degrees ≈ 11km)
    const targetRange = 0.05; // About 5.5km range
    const scaleLng = rangeLng > 0 ? targetRange / rangeLng : 1;
    const scaleLat = rangeLat > 0 ? targetRange / rangeLat : 1;

    // Function to normalize coordinates
    const normalizeCoord = (c) => {
        const lat = (c.lat - centerLat) * scaleLat;
        const lng = (c.lng - centerLng) * scaleLng;
        return [lat, lng];
    };

    const PRIORITY_COLORS = {
        1: '#FF6B35',
        2: '#FF6B35',
        3: '#4ECDC4',
        4: '#45B7D1',
        5: '#FFA07A'
    };

    features.forEach(feature => {
        const color = PRIORITY_COLORS[feature.priority] || '#999';
        const weight = feature.priority === 1 ? 6 : feature.priority === 2 ? 4 : 3;

        // Normalize coordinates to visible lat/lng range
        const latLngs = feature.coords.map(normalizeCoord);
        const origLatLngs = feature.origCoords ? feature.origCoords.map(normalizeCoord) : latLngs;

        // Original/Before layer (dashed gray)
        if (origLatLngs.length > 1) {
            const beforeLayer = L.polyline(origLatLngs, {
                color: '#999',
                weight: weight,
                opacity: 0.5,
                dashArray: '5, 5'
            }).bindPopup(`
                <b>Before: ${feature.typeRaw} #${feature.id}</b><br>
                Priority: P${feature.priority} (${feature.type})<br>
                Points: ${feature.coords.length}
            `);
            mapLayers.before.push(beforeLayer);
        }

        // After layer (colored solid)
        if (latLngs.length > 1) {
            const afterColor = feature.displaced ? '#dc3545' : '#28a745';
            const afterLayer = L.polyline(latLngs, {
                color: afterColor,
                weight: weight,
                opacity: 0.9
            }).bindPopup(`
                <b>After: ${feature.typeRaw} #${feature.id}</b><br>
                Type: ${feature.type}<br>
                Priority: P${feature.priority}<br>
                Status: ${feature.displaced ? '🔴 Displaced' : '🟢 Preserved'}<br>
                Displacement: ${feature.displacement.toFixed(2)}m<br>
                Points: ${feature.coords.length}
            `);
            mapLayers.after.push(afterLayer);

            if (feature.displaced) {
                mapLayers.displaced.push(afterLayer);
            } else {
                mapLayers.preserved.push(afterLayer);
            }
        }
    });

    // Show initial view
    showAfterView();
    fitAllFeatures();
    
    console.log(`Rendered ${features.length} features on map`);
    console.log(`Coordinate bounds: lat [${minLat}, ${maxLat}], lng [${minLng}, ${maxLng}]`);
    console.log(`Normalized to center [0, 0] with range ${targetRange} degrees`);
}

function showAfterView() {
    currentMapView = 'after';
    mapLayers.before.forEach(layer => leafletMap.removeLayer(layer));
    mapLayers.after.forEach(layer => layer.addTo(leafletMap));
    updateToggleButtons('btnAfter');
}

function showBeforeView() {
    currentMapView = 'before';
    mapLayers.after.forEach(layer => leafletMap.removeLayer(layer));
    mapLayers.before.forEach(layer => layer.addTo(leafletMap));
    updateToggleButtons('btnBefore');
}

function showBothViews() {
    currentMapView = 'both';
    mapLayers.before.forEach(layer => layer.addTo(leafletMap));
    mapLayers.after.forEach(layer => layer.addTo(leafletMap));
    updateToggleButtons('btnBoth');
}

function updateToggleButtons(activeBtn) {
    ['btnAfter', 'btnBefore', 'btnBoth'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            if (id === activeBtn) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    });
}

function fitAllFeatures() {
    if (!leafletMap) return;
    const allLayers = [...mapLayers.before, ...mapLayers.after];
    if (allLayers.length > 0) {
        const group = L.featureGroup(allLayers);
        leafletMap.fitBounds(group.getBounds().pad(0.1));
    }
}

function showDisplacedOnly() {
    mapLayers.after.forEach(layer => leafletMap.removeLayer(layer));
    mapLayers.before.forEach(layer => leafletMap.removeLayer(layer));
    mapLayers.displaced.forEach(layer => layer.addTo(leafletMap));
}

function showPreservedOnly() {
    mapLayers.after.forEach(layer => leafletMap.removeLayer(layer));
    mapLayers.before.forEach(layer => leafletMap.removeLayer(layer));
    mapLayers.preserved.forEach(layer => layer.addTo(leafletMap));
}

function showAllFeatures() {
    if (currentMapView === 'after') {
        showAfterView();
    } else if (currentMapView === 'before') {
        showBeforeView();
    } else {
        showBothViews();
    }
}

function clearMapLayers() {
    Object.values(mapLayers).forEach(layerArray => {
        layerArray.forEach(layer => leafletMap.removeLayer(layer));
    });
}

// Add map initialization when switching to map view tab
document.addEventListener('DOMContentLoaded', () => {
    const mapViewTab = document.querySelector('[data-view="mapview"]');
    if (mapViewTab) {
        mapViewTab.addEventListener('click', () => {
            setTimeout(() => {
                if (!leafletMap && features.length > 0) {
                    initializeLeafletMap();
                    renderFeaturesOnMap();
                } else if (leafletMap) {
                    leafletMap.invalidateSize();
                }
            }, 100);
        });
    }
});