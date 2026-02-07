/* Axes Systems - Enhanced with Backend Integration
    * Focused on RIGHT not PERFECT - excludes full topology, complex snapping
    */

const CONFIG = {
    MIN_CLEARANCE: 10,
    REPULSION_ITERATIONS: 5
};

const FEATURES = {
    motorway: { priority: 1, width: 25, color: '#E63946' },
    trunk: { priority: 1, width: 22, color: '#E63946' },
    primary: { priority: 2, width: 20, color: '#F4A261' },
    secondary: { priority: 3, width: 15, color: '#E9C46A' },
    tertiary: { priority: 4, width: 12, color: '#E9C46A' },
    river: { priority: 4, width: 20, color: '#4A90D9' },
    default: { priority: 5, width: 8, color: '#888888' }
};

let pointA = null, pointB = null;
let mapSelect, mapBefore, mapAfter;
let boundingBox = null;
let lastResultRoads = null;

let trafficAnimationId = null;
let trafficParticles = [];
const TRAFFIC_SPEED = 0.08;
const PARTICLES_PER_ROAD = 2;

function initMaps() {
    mapSelect = L.map('map-select').setView([50.9, 6.9], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OSM & CartoDB'
    }).addTo(mapSelect);

    mapBefore = L.map('map-before').setView([0, 0], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(mapBefore);

    mapAfter = L.map('map-after').setView([0, 0], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(mapAfter);

    // Add coordinate tracking for all maps
    mapSelect.on('mousemove', (e) => {
        document.getElementById('coord-select-lat').textContent = `Lat: ${e.latlng.lat.toFixed(6)}`;
        document.getElementById('coord-select-lng').textContent = `Lng: ${e.latlng.lng.toFixed(6)}`;
    });

    mapBefore.on('mousemove', (e) => {
        document.getElementById('coord-before-lat').textContent = `Lat: ${e.latlng.lat.toFixed(6)}`;
        document.getElementById('coord-before-lng').textContent = `Lng: ${e.latlng.lng.toFixed(6)}`;
    });

    mapAfter.on('mousemove', (e) => {
        document.getElementById('coord-after-lat').textContent = `Lat: ${e.latlng.lat.toFixed(6)}`;
        document.getElementById('coord-after-lng').textContent = `Lng: ${e.latlng.lng.toFixed(6)}`;
    });

    mapSelect.on('click', (e) => {
        const { lat, lng } = e.latlng;
        if (!pointA) {
            pointA = { lat, lng };
            addMarker(lat, lng, 'A', '#22c55e');
            updateUI('point-a', `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`, true);
        } else if (!pointB) {
            pointB = { lat, lng };
            addMarker(lat, lng, 'B', '#ef4444');
            updateUI('point-b', `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`, true);

            const bounds = [[pointA.lat, pointA.lng], [pointB.lat, pointB.lng]];
            boundingBox = L.rectangle(bounds, { color: '#3b82f6', weight: 1 }).addTo(mapSelect);
            mapSelect.fitBounds(bounds, { padding: [50, 50] });

            document.getElementById('btn-fetch').disabled = false;
        }
    });

    document.querySelectorAll('.map-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.map-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.map-view').forEach(v => v.classList.remove('active'));
            tab.classList.add('active');
            const viewId = tab.dataset.view;
            const viewEl = viewId ? document.getElementById('view-' + viewId) : null;
            if (viewEl) viewEl.classList.add('active');
            setTimeout(() => {
                if (mapSelect) mapSelect.invalidateSize();
                if (mapBefore) mapBefore.invalidateSize();
                if (mapAfter) mapAfter.invalidateSize();
            }, 100);
        });
    });

    mapBefore.on('move', () => { if (mapAfter) mapAfter.setView(mapBefore.getCenter(), mapBefore.getZoom(), { animate: false }); });
    mapAfter.on('move', () => { if (mapBefore) mapBefore.setView(mapAfter.getCenter(), mapAfter.getZoom(), { animate: false }); });
}

document.getElementById('btn-fetch').addEventListener('click', async () => {
    if (!pointA || !pointB) return;
    document.getElementById('loading').classList.add('show');
    const startTime = performance.now();
    try {
        const roads = await fetchRoads(pointA, pointB);
        const result = runDisplacementAlgorithm(roads);

        lastResultRoads = result.roads;
        renderResultMaps(result.roads);

        const processingTime = ((performance.now() - startTime) / 1000).toFixed(2);

        document.getElementById('stat-overlaps').textContent = result.overlapsDetected;
        document.getElementById('stat-resolved').textContent = result.overlapsResolved;
        document.getElementById('stat-max-shift').textContent = result.maxDisplacementMeters.toFixed(1) + 'm';
        document.getElementById('stat-features').textContent = roads.length;
        document.getElementById('stat-time').textContent = processingTime + 's';

        document.getElementById('loading').classList.remove('show');
        document.getElementById('toast').classList.add('show');
        setTimeout(() => document.getElementById('toast').classList.remove('show'), 3000);
        const beforeTab = document.querySelector('[data-view="before"]');
        if (beforeTab) beforeTab.click();

    } catch (err) {
        alert("Error: " + (err && err.message ? err.message : String(err)));
        document.getElementById('loading').classList.remove('show');
    }
});

async function fetchRoads(p1, p2) {
    if (!p1 || !p2 || typeof p1.lat !== 'number' || typeof p2.lat !== 'number') {
        throw new Error('Points A and B must be set.');
    }
    const minLat = Math.min(p1.lat, p2.lat);
    const maxLat = Math.max(p1.lat, p2.lat);
    const minLng = Math.min(p1.lng, p2.lng);
    const maxLng = Math.max(p1.lng, p2.lng);

    const query = `
        [out:json][timeout:25];
        (
            way["highway"~"motorway|trunk|primary|secondary|tertiary"](${minLat},${minLng},${maxLat},${maxLng});
            way["waterway"="river"](${minLat},${minLng},${maxLat},${maxLng});
        );
        out geom;
    `;

    const res = await fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        body: 'data=' + encodeURIComponent(query)
    });
    const text = await res.text();
    if (!text.trim().startsWith('{')) {
        const msg = text.includes('<?xml') || text.includes('<')
            ? 'Overpass API rate limit. Try again in a moment.'
            : (res.status ? `Server error (${res.status})` : 'Invalid response');
        throw new Error(msg);
    }
    const data = JSON.parse(text);
    if (data.elements === undefined) {
        if (data.error) throw new Error('Overpass: ' + data.error);
        throw new Error('No data. Try different area.');
    }

    const elements = Array.isArray(data.elements) ? data.elements : [];
    return elements
        .filter(el => el.type === 'way' && el.geometry && el.geometry.length >= 2 && el.tags)
        .map(el => {
            const type = el.tags.highway || el.tags.waterway || 'default';
            const conf = FEATURES[type] || FEATURES.default;
            const coords = el.geometry.map(p => [p.lat, p.lon]);
            return {
                id: el.id,
                type: type,
                priority: conf.priority,
                width: conf.width,
                color: conf.color,
                coords: coords,
                origCoords: coords.slice(),
                displaced: false
            };
        });
}

function runDisplacementAlgorithm(roads) {
    let overlapsDetected = 0;
    let overlapsResolved = 0;
    let maxDisplacementMeters = 0;
    const roadList = Array.isArray(roads) ? roads : [];

    const sorted = [...roadList].sort((a, b) => (a.priority || 5) - (b.priority || 5));
    const fixed = sorted.filter(r => r.priority <= 2);
    const moveable = sorted.filter(r => r.priority > 2);

    for (let iter = 0; iter < CONFIG.REPULSION_ITERATIONS; iter++) {
        moveable.forEach(mRoad => {
            if (!mRoad.coords || !Array.isArray(mRoad.coords) || mRoad.coords.length < 2) return;
            let roadMoved = false;

            mRoad.coords = mRoad.coords.map(vertex => {
                let totalDx = 0, totalDy = 0;
                let count = 0;

                fixed.forEach(fRoad => {
                    const nearest = getNearestPoint(vertex, fRoad.coords);
                    const requiredDistMeters = (fRoad.width / 2) + (mRoad.width / 2) + CONFIG.MIN_CLEARANCE;
                    const distMeters = getDistMeters(vertex, nearest.point);

                    if (distMeters < requiredDistMeters) {
                        if (iter === 0) overlapsDetected++;
                        const pushDistMeters = (requiredDistMeters - distMeters) * 1.2;
                        let angle = Math.atan2(vertex[0] - nearest.point[0], vertex[1] - nearest.point[1]);
                        const pushDeg = pushDistMeters / 111111;

                        totalDx += Math.sin(angle) * pushDeg;
                        totalDy += Math.cos(angle) * pushDeg;
                        count++;
                    }
                });

                if (count > 0) {
                    roadMoved = true;
                    const newVertex = [vertex[0] + (totalDx / count), vertex[1] + (totalDy / count)];
                    const shiftM = getDistMeters(vertex, newVertex);
                    if (shiftM > maxDisplacementMeters) maxDisplacementMeters = shiftM;
                    return newVertex;
                }
                return vertex;
            });

            if (roadMoved) {
                mRoad.displaced = true;
                overlapsResolved++;
            }
        });
    }

    moveable.forEach(r => {
        if (r.displaced && r.coords && r.coords.length >= 2) r.coords = smoothLine(r.coords);
    });

    return { roads: roadList, overlapsDetected, overlapsResolved, maxDisplacementMeters };
}

function getNearestPoint(p, line) {
    if (!line || line.length === 0) return { point: [p[0], p[1]] };
    if (line.length === 1) return { point: line[0] };
    let minD = Infinity, nearest = line[0];
    for (let i = 0; i < line.length - 1; i++) {
        const res = project(p, line[i], line[i + 1]);
        const d = getDistSq(p, res);
        if (d < minD) { minD = d; nearest = res; }
    }
    return { point: nearest };
}

function project(p, a, b) {
    if (!p || !a || !b || p.length < 2 || a.length < 2 || b.length < 2) return a && a.length >= 2 ? [a[0], a[1]] : (p && p.length >= 2 ? [p[0], p[1]] : [0, 0]);
    const x = p[0], y = p[1], x1 = a[0], y1 = a[1], x2 = b[0], y2 = b[1];
    const A = x - x1, B = y - y1, C = x2 - x1, D = y2 - y1;
    const dot = A * C + B * D;
    const lenSq = C * C + D * D;
    let param = -1;
    if (lenSq !== 0) param = dot / lenSq;
    if (param < 0) return a;
    if (param > 1) return b;
    return [x1 + param * C, y1 + param * D];
}

function getDistSq(a, b) { return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2; }

function getDistMeters(p1, p2) {
    if (!p1 || !p2 || !Array.isArray(p1) || !Array.isArray(p2) || p1.length < 2 || p2.length < 2) return 0;
    const R = 6371e3;
    const φ1 = p1[0] * Math.PI / 180;
    const φ2 = p2[0] * Math.PI / 180;
    const Δφ = (p2[0] - p1[0]) * Math.PI / 180;
    const Δλ = (p2[1] - p1[1]) * Math.PI / 180;
    const a = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function getPointAlongPath(coords, t) {
    if (!coords || coords.length === 0) return null;
    if (coords.length === 1) return coords[0];
    let u = Number(t);
    if (Number.isNaN(u) || u < 0) u = 0;
    if (u > 1) u = 1;
    const n = coords.length - 1;
    const lengths = [];
    let total = 0;
    for (let i = 0; i < n; i++) {
        const d = getDistMeters(coords[i], coords[i + 1]);
        lengths.push(d);
        total += d;
    }
    if (total <= 0) return coords[0];
    let s = u * total;
    for (let i = 0; i < n; i++) {
        if (s <= lengths[i]) {
            const f = lengths[i] > 0 ? s / lengths[i] : 0;
            return [
                coords[i][0] + f * (coords[i + 1][0] - coords[i][0]),
                coords[i][1] + f * (coords[i + 1][1] - coords[i][1])
            ];
        }
        s -= lengths[i];
    }
    return coords[coords.length - 1];
}

function smoothLine(points, iterations = 3) {
    if (!points || !Array.isArray(points)) return [];
    if (points.length < 2) return points.slice();
    let current = points.map(p => [...p]);

    for (let iter = 0; iter < iterations; iter++) {
        const next = [current[0]];
        for (let i = 0; i < current.length - 1; i++) {
            const a = current[i], b = current[i + 1];
            next.push(
                [0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]],
                [0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]]
            );
        }
        next.push(current[current.length - 1]);
        current = next;
    }
    return current;
}

function renderResultMaps(roads) {
    if (!pointA || !pointB || !mapBefore || !mapAfter) return;
    mapBefore.eachLayer(l => {
        if (l instanceof L.Polyline || l instanceof L.CircleMarker) mapBefore.removeLayer(l);
    });
    mapAfter.eachLayer(l => {
        if (l instanceof L.Polyline || l instanceof L.CircleMarker) mapAfter.removeLayer(l);
    });

    const bounds = L.latLngBounds([pointA.lat, pointA.lng], [pointB.lat, pointB.lng]);
    mapBefore.fitBounds(bounds);
    mapAfter.fitBounds(bounds);

    (roads || []).forEach(r => {
        if (!r.origCoords || r.origCoords.length < 2) return;
        L.polyline(r.origCoords, {
            color: r.color,
            weight: r.width / 3,
            opacity: 0.7
        }).addTo(mapBefore);

        const coords = r.coords && r.coords.length >= 2 ? r.coords : r.origCoords;
        const isWater = r.type === 'river';
        const afterColor = isWater ? r.color : (r.displaced ? '#22c55e' : r.color);
        const origLine = L.polyline(r.origCoords, {
            color: r.color,
            weight: r.width / 3,
            opacity: 0.7
        }).addTo(mapBefore);
        const line = L.polyline(coords, {
            color: afterColor,
            weight: r.width / 3,
            opacity: 0.9
        }).addTo(mapAfter);
        
        // Add detailed popup to both lines
        const popupContent = createFeaturePopup(r, coords);
        origLine.bindPopup(popupContent);
        line.bindPopup(popupContent);
    });

    const pointStyle = { radius: 5, weight: 1.5, fillOpacity: 1 };
    L.circleMarker([pointA.lat, pointA.lng], { ...pointStyle, fillColor: '#22c55e', color: '#fff' })
        .bindTooltip('A', { permanent: true, direction: 'center' }).addTo(mapBefore);
    L.circleMarker([pointB.lat, pointB.lng], { ...pointStyle, fillColor: '#ef4444', color: '#fff' })
        .bindTooltip('B', { permanent: true, direction: 'center' }).addTo(mapBefore);
    L.circleMarker([pointA.lat, pointA.lng], { ...pointStyle, fillColor: '#22c55e', color: '#fff' })
        .bindTooltip('A', { permanent: true, direction: 'center' }).addTo(mapAfter);
    L.circleMarker([pointB.lat, pointB.lng], { ...pointStyle, fillColor: '#ef4444', color: '#fff' })
        .bindTooltip('B', { permanent: true, direction: 'center' }).addTo(mapAfter);

    const trafficToggle = document.getElementById('traffic-toggle');
    if (trafficToggle && trafficToggle.checked) startTraffic();
}

function getTrafficMapsBounds() {
    if (mapBefore) {
        const bBefore = mapBefore.getBounds();
        if (bBefore && bBefore.isValid()) return bBefore;
    }
    if (mapAfter) {
        const bAfter = mapAfter.getBounds();
        if (bAfter && bAfter.isValid()) return bAfter;
    }
    if (pointA && pointB) {
        return L.latLngBounds([pointA.lat, pointA.lng], [pointB.lat, pointB.lng]);
    }
    return null;
}

function startTraffic() {
    stopTraffic();
    if (!lastResultRoads || lastResultRoads.length === 0) return;
    const majorRoads = lastResultRoads.filter(r => r.type !== 'river');
    if (majorRoads.length === 0) return;
    const bounds = getTrafficMapsBounds();
    if (!bounds) return;

    const particleIcon = L.divIcon({
        className: 'traffic-particle-wrap',
        html: '<div class="traffic-particle"></div>',
        iconSize: [4, 4],
        iconAnchor: [2, 2]
    });

    majorRoads.forEach(road => {
        const paths = [
            { coords: road.origCoords, map: mapBefore },
            { coords: road.coords, map: mapAfter }
        ];
        paths.forEach(({ coords, map }) => {
            if (!coords || !Array.isArray(coords) || coords.length < 2) return;
            for (let p = 0; p < PARTICLES_PER_ROAD; p++) {
                const offset = p / PARTICLES_PER_ROAD;
                const marker = L.marker([coords[0][0], coords[0][1]], { icon: particleIcon }).addTo(map);
                trafficParticles.push({
                    marker,
                    coords,
                    t: offset % 1,
                    map
                });
            }
        });
    });

    let lastTime = performance.now();
    function animate() {
        trafficAnimationId = requestAnimationFrame(animate);
        const now = performance.now();
        const dt = (now - lastTime) / 1000;
        lastTime = now;
        trafficParticles.forEach(p => {
            p.t += TRAFFIC_SPEED * dt;
            if (p.t >= 1) p.t -= 1;
            if (p.t < 0) p.t += 1;
            const pt = getPointAlongPath(p.coords, p.t);
            if (pt) p.marker.setLatLng([pt[0], pt[1]]);
        });
    }
    animate();
}

function stopTraffic() {
    if (trafficAnimationId != null) {
        cancelAnimationFrame(trafficAnimationId);
        trafficAnimationId = null;
    }
    trafficParticles.forEach(p => {
        if (p.map && p.marker) p.map.removeLayer(p.marker);
    });
    trafficParticles = [];
}

function toggleTraffic() {
    const el = document.getElementById('traffic-toggle');
    if (!el) return;
    if (el.checked) startTraffic();
    else stopTraffic();
}

function addMarker(lat, lng, label, color) {
    if (!mapSelect) return;
    L.circleMarker([lat, lng], {
        radius: 8, fillColor: color, color: '#fff', weight: 2, fillOpacity: 1
    }).bindTooltip(label, { permanent: true, direction: 'center' }).addTo(mapSelect);
}

function createFeaturePopup(feature, coords) {
    const statusBadge = feature.displaced 
        ? '<span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">🔴 DISPLACED</span>'
        : '<span style="background: rgba(34, 197, 94, 0.2); color: #22c55e; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">🟢 PRESERVED</span>';

    const priorityName = {
        1: 'P1_MOTORWAY',
        2: 'P2_PRIMARY',
        3: 'P3_STREET',
        4: 'P4_BUILDING',
        5: 'P5_LABEL'
    }[feature.priority] || 'UNKNOWN';

    let displacementInfo = '';
    if (feature.displaced && feature.origCoords && coords) {
        const dist = calculateHaversine(feature.origCoords[0], coords[0]);
        const angle = calculateBearing(feature.origCoords[0], coords[0]);
        displacementInfo = `
            <tr><td style="color: #94a3b8; padding-right: 12px;">Displacement:</td><td><strong>${dist.toFixed(2)}m</strong></td></tr>
            <tr><td style="color: #94a3b8; padding-right: 12px;">Direction:</td><td><strong>${angle.toFixed(1)}°</strong></td></tr>
        `;
    }

    const coordsList = coords || feature.coords || [];
    const firstCoord = coordsList.length > 0 ? coordsList[0] : null;
    const lastCoord = coordsList.length > 1 ? coordsList[coordsList.length - 1] : null;

    return `
        <div style="font-family: 'Inter', sans-serif; min-width: 280px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(148,163,184,0.3);">
                <strong style="font-size: 1rem;">🗺️ ${feature.id || feature.type || 'Feature'}</strong>
                ${statusBadge}
            </div>
            <table style="width: 100%; font-size: 0.85rem; line-height: 1.8;">
                <tr><td style="color: #64748b; padding-right: 12px;">Type:</td><td><strong>${feature.type || 'Unknown'}</strong></td></tr>
                <tr><td style="color: #64748b; padding-right: 12px;">Priority:</td><td><strong>${priorityName}</strong></td></tr>
                <tr><td style="color: #64748b; padding-right: 12px;">Width:</td><td><strong>${feature.width || 0}m</strong></td></tr>
                <tr><td style="color: #64748b; padding-right: 12px;">Z-Index:</td><td><strong>${800 - feature.priority * 100}</strong></td></tr>
                <tr><td style="color: #64748b; padding-right: 12px;">Points:</td><td><strong>${coordsList.length}</strong></td></tr>
                ${displacementInfo}
            </table>
            ${firstCoord ? `
                <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(148,163,184,0.3);">
                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">Start Point:</div>
                    <div style="font-family: 'Courier New', monospace; font-size: 0.8rem;">${firstCoord[0].toFixed(6)}, ${firstCoord[1].toFixed(6)}</div>
                </div>
            ` : ''}
            ${lastCoord && coordsList.length > 1 ? `
                <div style="margin-top: 8px;">
                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">End Point:</div>
                    <div style="font-family: 'Courier New', monospace; font-size: 0.8rem;">${lastCoord[0].toFixed(6)}, ${lastCoord[1].toFixed(6)}</div>
                </div>
            ` : ''}
        </div>
    `;
}

function calculateHaversine(coord1, coord2) {
    const lat1 = coord1[0], lng1 = coord1[1];
    const lat2 = coord2[0], lng2 = coord2[1];
    const R = 6371000; // Earth radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lng2 - lng1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // Distance in meters
}

function calculateBearing(coord1, coord2) {
    const lat1 = coord1[0] * Math.PI / 180;
    const lat2 = coord2[0] * Math.PI / 180;
    const Δλ = (coord2[1] - coord1[1]) * Math.PI / 180;

    const y = Math.sin(Δλ) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) -
                Math.sin(lat1) * Math.cos(lat2) * Math.cos(Δλ);
    const θ = Math.atan2(y, x);
    const bearing = (θ * 180 / Math.PI + 360) % 360;

    return bearing;
}

function updateUI(id, text, set) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    if (set) el.classList.add('set');
    else el.classList.remove('set');
}

document.getElementById('traffic-toggle').addEventListener('change', toggleTraffic);

document.getElementById('btn-reset').addEventListener('click', () => {
    pointA = null;
    pointB = null;
    boundingBox = null;
    lastResultRoads = null;
    const pointAEl = document.getElementById('point-a');
    const pointBEl = document.getElementById('point-b');
    if (pointAEl) { pointAEl.textContent = 'Point A: Not set'; pointAEl.classList.remove('set'); }
    if (pointBEl) { pointBEl.textContent = 'Point B: Not set'; pointBEl.classList.remove('set'); }
    const btnFetch = document.getElementById('btn-fetch');
    if (btnFetch) btnFetch.disabled = true;
    const trafficToggle = document.getElementById('traffic-toggle');
    if (trafficToggle) trafficToggle.checked = false;
    stopTraffic();
    if (mapSelect) mapSelect.eachLayer(l => { if (!(l instanceof L.TileLayer)) mapSelect.removeLayer(l); });
    if (mapBefore) mapBefore.eachLayer(l => { if (!(l instanceof L.TileLayer)) mapBefore.removeLayer(l); });
    if (mapAfter) mapAfter.eachLayer(l => { if (!(l instanceof L.TileLayer)) mapAfter.removeLayer(l); });
    document.getElementById('stat-overlaps').textContent = '0';
    document.getElementById('stat-resolved').textContent = '0';
    document.getElementById('stat-max-shift').textContent = '0.0m';
    document.getElementById('stat-features').textContent = '0';
    document.getElementById('stat-time').textContent = '-';
});

initMaps();