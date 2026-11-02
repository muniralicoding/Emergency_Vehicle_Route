/**
 * Leaflet.js Map Controller & Route Visualizer
 */

let map;
let networkData = null;
let nodeMarkers = {};
let edgePolylines = [];
let routeLayers = {
    fastest: null,
    shortest: null,
    alternative: null
};
let ambulanceMarker = null;
let currentFastestCoords = [];

// Initialize Map
function initMap() {
    // Center around South-Central Delhi / Metro network
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([28.5850, 77.2250], 12);

    // Premium Dark Theme CartoDB tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(map);

    L.control.attribution({ position: 'bottomright' })
        .addAttribution('&copy; OpenStreetMap &copy; CARTO')
        .addTo(map);

    fetchNetworkData();
}

// Fetch network graph from Flask API
async function fetchNetworkData(recomputeCurrent = false) {
    try {
        const res = await fetch('/api/network');
        const data = await res.json();
        if (data.status === 'success') {
            networkData = data.graph;
            renderGraph();
            populateDropdowns();

            if (recomputeCurrent || !window.initialOptimized) {
                window.initialOptimized = true;
                runOptimization();
            }
        }
    } catch (err) {
        console.error("Failed to load network:", err);
    }
}

// Render nodes and edges on the map
function renderGraph() {
    if (!networkData) return;

    // Clear existing road lines
    edgePolylines.forEach(p => map.removeLayer(p));
    edgePolylines = [];

    // Clear existing node markers
    Object.values(nodeMarkers).forEach(m => map.removeLayer(m));
    nodeMarkers = {};

    const nodesMap = {};
    networkData.nodes.forEach(n => { nodesMap[n.id] = n; });

    // Render Edges
    networkData.edges.forEach(edge => {
        const uNode = nodesMap[edge.u];
        const vNode = nodesMap[edge.v];
        if (!uNode || !vNode) return;

        const latLngs = [
            [uNode.lat, uNode.lon],
            [vNode.lat, vNode.lon]
        ];

        let color = '#10b981'; // Green (Clear)
        let weight = 3.5;
        let dashArray = null;

        if (edge.status === 'BLOCKED') {
            color = '#374151'; // Dark grey / blocked
            dashArray = '6, 6';
            weight = 3;
        } else if (edge.status === 'EMERGENCY_LANE') {
            color = '#06b6d4'; // Cyan
            weight = 4.5;
        } else if (edge.traffic_factor >= 3.0) {
            color = '#ef4444'; // Red
            weight = 4;
        } else if (edge.traffic_factor >= 2.0) {
            color = '#f59e0b'; // Amber
            weight = 3.5;
        }

        const polyline = L.polyline(latLngs, {
            color: color,
            weight: weight,
            opacity: 0.65,
            dashArray: dashArray
        }).addTo(map);

        // Edge Popup with quick road control
        const popupContent = `
            <div class="text-xs space-y-2 p-1 font-sans">
                <div class="font-bold text-sm text-gray-100 flex items-center justify-between">
                    <span>${edge.road_name}</span>
                    <span class="px-1.5 py-0.5 rounded text-[10px] ${
                        edge.status === 'BLOCKED' ? 'bg-red-900 text-red-200' : 
                        edge.status === 'EMERGENCY_LANE' ? 'bg-cyan-900 text-cyan-200' : 'bg-gray-700 text-gray-200'
                    }">${edge.status}</span>
                </div>
                <div class="grid grid-cols-2 gap-1 text-gray-300">
                    <div>📏 <b>Dist:</b> ${edge.distance_km} km</div>
                    <div>⚡ <b>Speed:</b> ${edge.effective_speed_kmh} km/h</div>
                    <div>⏱️ <b>Travel:</b> ${edge.travel_time_minutes ? edge.travel_time_minutes + ' min' : 'BLOCKED'}</div>
                    <div>🚦 <b>Traffic:</b> ${edge.traffic_factor}x</div>
                </div>
                <div class="pt-2 border-t border-gray-700 flex gap-2">
                    <button onclick="toggleRoadblock('${edge.u}', '${edge.v}', ${edge.status !== 'BLOCKED'})" 
                            class="px-2 py-1 rounded text-xs font-semibold ${edge.status === 'BLOCKED' ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-red-600 hover:bg-red-500 text-white'} w-full transition">
                        ${edge.status === 'BLOCKED' ? '✅ Unblock Road' : '⛔ Block Road'}
                    </button>
                </div>
            </div>
        `;
        polyline.bindPopup(popupContent);
        edgePolylines.push(polyline);
    });

    // Render Nodes
    const bounds = [];
    networkData.nodes.forEach(node => {
        let iconHtml = '';
        let className = '';

        if (node.node_type === 'hospital') {
            className = 'marker-pin-hospital';
            iconHtml = '<i class="fa-solid fa-hospital"></i>';
        } else if (node.node_type === 'accident_spot') {
            className = 'marker-pin-accident';
            iconHtml = '<i class="fa-solid fa-car-burst"></i>';
        } else {
            className = 'marker-pin-junction';
            iconHtml = '';
        }

        const customIcon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div class="${className}">${iconHtml}</div>`,
            iconSize: node.node_type === 'intersection' ? [14, 14] : [32, 32],
            iconAnchor: node.node_type === 'intersection' ? [7, 7] : [16, 16]
        });

        const marker = L.marker([node.lat, node.lon], { icon: customIcon }).addTo(map);

        let tooltipContent = `<b>${node.name}</b>`;
        if (node.node_type === 'hospital') {
            tooltipContent += `<br/><span class="text-emerald-400">ICU Beds: ${node.beds_available}</span>`;
            if (node.trauma_center) tooltipContent += ` • <span class="text-cyan-400">Level 1 Trauma</span>`;
        }

        marker.bindTooltip(tooltipContent, {
            direction: 'top',
            offset: [0, -10],
            className: 'bg-gray-900 text-white text-xs px-2 py-1 rounded border border-gray-700'
        });

        // Quick click selection
        marker.on('click', () => {
            handleNodeClick(node);
        });

        nodeMarkers[node.id] = marker;
        bounds.push([node.lat, node.lon]);
    });

    if (bounds.length > 0 && !window.initialFitted) {
        map.fitBounds(bounds, { padding: [40, 40] });
        window.initialFitted = true;
    }
}

// Populate dropdown selectors
function populateDropdowns() {
    const startSelect = document.getElementById("startNodeSelect");
    const targetSelect = document.getElementById("targetNodeSelect");

    if (!startSelect || !targetSelect || !networkData) return;

    const currentStart = startSelect.value;
    const currentTarget = targetSelect.value;

    startSelect.innerHTML = "";
    targetSelect.innerHTML = "";

    // Grouping
    const incidents = networkData.nodes.filter(n => n.node_type === 'accident_spot');
    const hospitals = networkData.nodes.filter(n => n.node_type === 'hospital');
    const others = networkData.nodes.filter(n => n.node_type !== 'accident_spot' && n.node_type !== 'hospital');

    function createOption(node) {
        const opt = document.createElement("option");
        opt.value = node.id;
        opt.textContent = node.name;
        if (node.node_type === 'hospital') {
            opt.textContent += ` (${node.beds_available} beds)`;
        }
        return opt;
    }

    const addGroup = (select, label, nodes) => {
        const group = document.createElement("optgroup");
        group.label = label;
        nodes.forEach(n => group.appendChild(createOption(n)));
        select.appendChild(group);
    };

    addGroup(startSelect, "⚠️ Accident / Incident Sites", incidents);
    addGroup(startSelect, "🏥 Hospitals & Hubs", hospitals);
    addGroup(startSelect, "📍 Intersections & Junctions", others);

    addGroup(targetSelect, "🏥 Hospitals & Trauma Centers", hospitals);
    addGroup(targetSelect, "📍 Intersections & Hubs", others);

    // Default selections
    startSelect.value = currentStart || (incidents[0] ? incidents[0].id : networkData.nodes[0].id);
    targetSelect.value = currentTarget || (hospitals[0] ? hospitals[0].id : networkData.nodes[1].id);
}

function handleNodeClick(node) {
    const startSelect = document.getElementById("startNodeSelect");
    const targetSelect = document.getElementById("targetNodeSelect");

    if (node.node_type === 'accident_spot') {
        startSelect.value = node.id;
        showToast(`Selected origin: ${node.name}`, 'info');
    } else if (node.node_type === 'hospital') {
        targetSelect.value = node.id;
        showToast(`Selected destination: ${node.name}`, 'info');
    } else {
        // Toggle based on current selection
        if (!startSelect.value) startSelect.value = node.id;
        else targetSelect.value = node.id;
    }
}

// Run Route Optimization API call
async function runOptimization() {
    const startSelect = document.getElementById("startNodeSelect");
    const targetSelect = document.getElementById("targetNodeSelect");

    if (!startSelect || !targetSelect) return;
    const startId = startSelect.value;
    const targetId = targetSelect.value;

    if (startId === targetId) {
        showToast("Start and Destination cannot be the same node!", "warning");
        return;
    }

    const btn = document.getElementById("optimizeBtn");
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Computing Optimal Corridors...';
        btn.disabled = true;
    }

    try {
        const res = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_id: startId, target_id: targetId })
        });
        const result = await res.json();

        if (result.status === 'success') {
            displayResults(result.data);
        } else {
            showToast(result.message || "Optimization failed", "error");
        }
    } catch (err) {
        console.error("Optimization API error:", err);
        showToast("Error connecting to server", "error");
    } finally {
        if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-bolt mr-2"></i> Optimize Emergency Route';
            btn.disabled = false;
        }
    }
}

// Display route polylines and panel data
function displayResults(data) {
    const nodesMap = {};
    networkData.nodes.forEach(n => { nodesMap[n.id] = n; });

    // Clear previous routes
    if (routeLayers.fastest) map.removeLayer(routeLayers.fastest);
    if (routeLayers.shortest) map.removeLayer(routeLayers.shortest);
    if (routeLayers.alternative) map.removeLayer(routeLayers.alternative);

    // 1. Draw Naive Shortest Distance Route (Coral Red Dashed)
    if (data.shortest_route && data.shortest_route.path && data.shortest_route.path.length > 1) {
        const coords = data.shortest_route.path.map(id => [nodesMap[id].lat, nodesMap[id].lon]);
        routeLayers.shortest = L.polyline(coords, {
            color: '#ef4444',
            weight: 5,
            opacity: 0.75,
            dashArray: '8, 8'
        }).addTo(map);
    }

    // 2. Draw Alternative Backup Route (Purple)
    if (data.alternative_route && data.alternative_route.path && data.alternative_route.path.length > 1) {
        const coords = data.alternative_route.path.map(id => [nodesMap[id].lat, nodesMap[id].lon]);
        routeLayers.alternative = L.polyline(coords, {
            color: '#a855f7',
            weight: 4,
            opacity: 0.7,
            dashArray: '4, 6'
        }).addTo(map);
    }

    // 3. Draw Fastest Emergency Route (Emerald Glowing Green)
    if (data.fastest_route && data.fastest_route.path && data.fastest_route.path.length > 1) {
        currentFastestCoords = data.fastest_route.path.map(id => [nodesMap[id].lat, nodesMap[id].lon]);
        
        // Glow effect: backline + frontline
        routeLayers.fastest = L.layerGroup([
            L.polyline(currentFastestCoords, { color: '#10b981', weight: 12, opacity: 0.3 }),
            L.polyline(currentFastestCoords, { color: '#34d399', weight: 6, opacity: 0.95 })
        ]).addTo(map);

        map.fitBounds(L.polyline(currentFastestCoords).getBounds(), { padding: [50, 50] });

        // Position ambulance at origin
        setupAmbulanceMarker(currentFastestCoords[0]);
    }

    // Update UI Cards
    updateSummaryCards(data);
    updateBenchmarkTable(data.algorithms_benchmark);
    updateLegsList(data.primary_legs);
    renderBenchmarkCharts(data.algorithms_benchmark);
}

function setupAmbulanceMarker(coord) {
    if (ambulanceMarker) {
        map.removeLayer(ambulanceMarker);
    }

    const ambIcon = L.divIcon({
        className: 'custom-amb-icon',
        html: `<div class="marker-ambulance"><i class="fa-solid fa-truck-medical text-red-600"></i></div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });

    ambulanceMarker = L.marker(coord, { icon: ambIcon, zIndexOffset: 1000 }).addTo(map);
}

// Start animated simulation
function triggerAmbulanceRun() {
    if (!currentFastestCoords || currentFastestCoords.length < 2) {
        showToast("Please calculate a route first!", "warning");
        return;
    }

    const simBtn = document.getElementById("simulateBtn");
    const progressBanner = document.getElementById("simulationBanner");

    if (window.ambulanceSim.isSimulating) {
        window.ambulanceSim.stopSimulation();
        if (simBtn) simBtn.innerHTML = '<i class="fa-solid fa-play mr-2"></i> Simulate Ambulance Trip';
        if (progressBanner) progressBanner.classList.add("hidden");
        return;
    }

    if (simBtn) simBtn.innerHTML = '<i class="fa-solid fa-stop mr-2"></i> Stop Simulation';
    if (progressBanner) progressBanner.classList.remove("hidden");

    window.ambulanceSim.startSimulation(
        currentFastestCoords,
        (currentCoord, percent) => {
            if (ambulanceMarker) {
                ambulanceMarker.setLatLng(currentCoord);
            }
            const progBar = document.getElementById("simProgressBar");
            const progText = document.getElementById("simProgressText");
            if (progBar) progBar.style.width = `${percent}%`;
            if (progText) progText.textContent = `${percent}% In Transit`;
        },
        () => {
            // Arrival callback
            if (simBtn) simBtn.innerHTML = '<i class="fa-solid fa-play mr-2"></i> Replay Ambulance Trip';
            const progText = document.getElementById("simProgressText");
            if (progText) progText.textContent = `✅ Arrived at Emergency Bay!`;
            showToast("🚑 Ambulance arrived safely at Hospital Trauma Center!", "success");
        }
    );
}

// Toggle roadblock API
async function toggleRoadblock(u, v, blocked) {
    try {
        const res = await fetch('/api/toggle-roadblock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ u, v, blocked })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`${data.road_name} is now ${data.new_status}`, 'info');
            fetchNetworkData(true); // reload and recompute
        }
    } catch (e) {
        console.error("Roadblock toggle failed:", e);
    }
}

// Auto-triage nearest hospital
async function dispatchNearestHospital() {
    const startSelect = document.getElementById("startNodeSelect");
    const accidentId = startSelect.value;
    const requireTrauma = document.getElementById("requireTraumaCheckbox")?.checked || false;

    try {
        const res = await fetch('/api/nearest-hospital', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ accident_id: accidentId, require_trauma: requireTrauma })
        });
        const data = await res.json();
        if (data.status === 'success' && data.data.recommended) {
            const rec = data.data.recommended;
            const targetSelect = document.getElementById("targetNodeSelect");
            targetSelect.value = rec.hospital.id;
            showToast(`Triaged to ${rec.hospital.name} (ETA: ${rec.travel_time_min}m, Beds: ${rec.beds_available})`, 'success');
            runOptimization();
        } else {
            showToast("No reachable hospital with available beds!", "error");
        }
    } catch (e) {
        console.error("Triage error:", e);
    }
}

// Change traffic scenario
async function changeTrafficScenario(scenarioKey) {
    try {
        const res = await fetch('/api/traffic-scenario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario: scenarioKey })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`Applied: ${data.scenario.description}`, 'info');
            fetchNetworkData(true);
        }
    } catch (e) {
        console.error("Scenario error:", e);
    }
}

// Reset network
async function resetEntireNetwork() {
    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            showToast("Network restored to default condition.", "info");
            fetchNetworkData(true);
        }
    } catch (e) {
        console.error("Reset error:", e);
    }
}

// Update UI elements
function updateSummaryCards(data) {
    const fTime = document.getElementById("fastestTimeVal");
    const fDist = document.getElementById("fastestDistVal");
    const sTime = document.getElementById("shortestTimeVal");
    const sDist = document.getElementById("shortestDistVal");
    const timeSavedBadge = document.getElementById("timeSavedBadge");

    if (fTime && data.fastest_route) fTime.textContent = `${data.fastest_route.total_time_min ?? 'N/A'} min`;
    if (fDist && data.fastest_route) fDist.textContent = `${data.fastest_route.total_distance_km} km`;

    if (sTime && data.shortest_route) sTime.textContent = `${data.shortest_route.total_time_min ?? 'N/A'} min`;
    if (sDist && data.shortest_route) sDist.textContent = `${data.shortest_route.total_distance_km} km`;

    if (timeSavedBadge) {
        if (data.time_saved_minutes > 0) {
            timeSavedBadge.innerHTML = `<i class="fa-solid fa-clock mr-1"></i> Saved ${data.time_saved_minutes} min vs naive shortest!`;
            timeSavedBadge.classList.remove("hidden");
        } else {
            timeSavedBadge.classList.add("hidden");
        }
    }
}

function updateBenchmarkTable(benchmarks) {
    const tbody = document.getElementById("benchmarkTableBody");
    if (!tbody || !benchmarks) return;

    tbody.innerHTML = "";
    benchmarks.forEach(item => {
        const row = document.createElement("tr");
        row.className = "border-b border-gray-800 hover:bg-gray-800/40 text-xs";

        row.innerHTML = `
            <td class="py-2.5 px-3 font-semibold text-gray-200 flex items-center gap-1.5">
                ${item.optimal ? '<i class="fa-solid fa-check text-emerald-400"></i>' : '<i class="fa-solid fa-triangle-exclamation text-amber-400"></i>'}
                ${item.name}
            </td>
            <td class="py-2.5 px-3 text-emerald-400 font-bold">${item.time_min !== null ? item.time_min + ' min' : 'Unreachable'}</td>
            <td class="py-2.5 px-3 text-gray-300">${item.distance_km} km</td>
            <td class="py-2.5 px-3 text-purple-400 font-mono">${item.visited_nodes}</td>
            <td class="py-2.5 px-3 text-blue-400 font-mono">${item.relaxations}</td>
            <td class="py-2.5 px-3 text-yellow-400 font-mono">${item.exec_time_ms} ms</td>
            <td class="py-2.5 px-3 text-gray-400 font-mono text-[11px]">${item.complexity}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateLegsList(legs) {
    const container = document.getElementById("legsContainer");
    if (!container) return;

    if (!legs || legs.length === 0) {
        container.innerHTML = `<div class="text-xs text-gray-500 py-3 text-center">No route steps available.</div>`;
        return;
    }

    container.innerHTML = "";
    legs.forEach((leg, idx) => {
        const item = document.createElement("div");
        item.className = "p-2 bg-gray-800/50 rounded border border-gray-750 flex items-center justify-between text-xs";

        item.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="w-5 h-5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center justify-center font-bold text-[10px]">${idx + 1}</span>
                <div>
                    <div class="font-medium text-gray-200">${leg.road_name}</div>
                    <div class="text-[11px] text-gray-400">${leg.from_name} ➔ ${leg.to_name}</div>
                </div>
            </div>
            <div class="text-right">
                <div class="font-bold text-emerald-400">${leg.travel_time_min}m</div>
                <div class="text-[10px] text-gray-400">${leg.distance_km}km • ${leg.effective_speed_kmh}km/h</div>
            </div>
        `;
        container.appendChild(item);
    });
}

function showToast(msg, type = 'info') {
    const toast = document.createElement("div");
    const colors = {
        info: 'bg-blue-900/90 border-blue-600 text-blue-100',
        success: 'bg-emerald-900/90 border-emerald-600 text-emerald-100',
        warning: 'bg-amber-900/90 border-amber-600 text-amber-100',
        error: 'bg-red-900/90 border-red-600 text-red-100'
    };

    toast.className = `fixed bottom-5 right-5 z-50 px-4 py-2.5 rounded-lg border shadow-xl backdrop-blur-md text-xs font-medium flex items-center gap-2 transition-all transform duration-300 ${colors[type] || colors.info}`;
    toast.innerHTML = `<i class="fa-solid fa-bell"></i> <span>${msg}</span>`;

    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 350);
    }, 3200);
}

// Window on-load
window.addEventListener('DOMContentLoaded', () => {
    initMap();
});
