// Tucson Pedestrian Safety Mapper - Main Application
// MapBox Access Token (use your own token for production)
mapboxgl.accessToken = 'pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJjbGV4YW1wbGUifQ.example'; // Replace with actual token

// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000/api' : '/api';
const TUCSON_CENTER = [-110.9747, 32.2226];
const TUCSON_BOUNDS = [
    [-111.3, 32.0], // Southwest
    [-110.6, 32.5]  // Northeast
];

// Global State
let map;
let allIncidents = [];
let filteredIncidents = [];
let charts = {};
let hotSpots = {};

// Road type colors for markers
const ROAD_COLORS = {
    'Principal Arterial - Other': '#dc2626',
    'Minor Arterial': '#f59e0b',
    'Major Collector': '#10b981',
    'Minor Collector': '#3b82f6',
    'Local': '#8b5cf6',
    'Interstate': '#ef4444'
};

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing Tucson Pedestrian Safety Mapper...');

    // Initialize map
    initMap();

    // Load initial data
    await loadData();

    // Setup event listeners
    setupEventListeners();

    // Hide loading overlay
    hideLoading();

    console.log('Application initialized successfully');
});

// Initialize MapBox map
function initMap() {
    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: TUCSON_CENTER,
        zoom: 11,
        maxBounds: TUCSON_BOUNDS
    });

    // Add navigation controls
    map.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add scale
    map.addControl(new mapboxgl.ScaleControl());

    // Wait for map to load
    map.on('load', () => {
        console.log('Map loaded successfully');
        // Map layers will be added after data is loaded
    });
}

// Load data from API
async function loadData() {
    try {
        showLoading();

        // Load incidents
        const incidentsResponse = await fetch(`${API_BASE_URL}/incidents`);
        const incidentsData = await incidentsResponse.json();
        allIncidents = incidentsData.features;
        filteredIncidents = [...allIncidents];

        console.log(`Loaded ${allIncidents.length} incidents`);

        // Load hot spots
        const hotSpotsResponse = await fetch(`${API_BASE_URL}/hot_spots`);
        hotSpots = await hotSpotsResponse.json();

        // Update UI
        updateStats();
        updateHotSpotsList();
        addIncidentsToMap();
        createCharts();

    } catch (error) {
        console.error('Error loading data:', error);
        alert('Error loading data. Please check if the backend server is running.');
    }
}

// Add incidents to map
function addIncidentsToMap() {
    if (!map.loaded()) {
        map.on('load', () => addIncidentsToMap());
        return;
    }

    // Remove existing sources and layers
    if (map.getSource('incidents')) {
        if (map.getLayer('incidents-heatmap')) map.removeLayer('incidents-heatmap');
        if (map.getLayer('incidents-clusters')) map.removeLayer('incidents-clusters');
        if (map.getLayer('incidents-cluster-count')) map.removeLayer('incidents-cluster-count');
        if (map.getLayer('incidents-unclustered')) map.removeLayer('incidents-unclustered');
        map.removeSource('incidents');
    }

    // Create GeoJSON from filtered incidents
    const geojson = {
        type: 'FeatureCollection',
        features: filteredIncidents
    };

    // Add source
    map.addSource('incidents', {
        type: 'geojson',
        data: geojson,
        cluster: true,
        clusterMaxZoom: 16,
        clusterRadius: 50
    });

    // Add heatmap layer (hidden by default)
    map.addLayer({
        id: 'incidents-heatmap',
        type: 'heatmap',
        source: 'incidents',
        layout: {
            visibility: 'none'
        },
        paint: {
            'heatmap-weight': 1,
            'heatmap-intensity': 1,
            'heatmap-color': [
                'interpolate',
                ['linear'],
                ['heatmap-density'],
                0, 'rgba(33,102,172,0)',
                0.2, 'rgb(103,169,207)',
                0.4, 'rgb(209,229,240)',
                0.6, 'rgb(253,219,199)',
                0.8, 'rgb(239,138,98)',
                1, 'rgb(178,24,43)'
            ],
            'heatmap-radius': 20,
            'heatmap-opacity': 0.8
        }
    });

    // Add cluster circles
    map.addLayer({
        id: 'incidents-clusters',
        type: 'circle',
        source: 'incidents',
        filter: ['has', 'point_count'],
        paint: {
            'circle-color': [
                'step',
                ['get', 'point_count'],
                '#f59e0b', 10,
                '#f97316', 20,
                '#dc2626'
            ],
            'circle-radius': [
                'step',
                ['get', 'point_count'],
                15, 10,
                20, 20,
                25
            ],
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
        }
    });

    // Add cluster count labels
    map.addLayer({
        id: 'incidents-cluster-count',
        type: 'symbol',
        source: 'incidents',
        filter: ['has', 'point_count'],
        layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 12
        },
        paint: {
            'text-color': '#ffffff'
        }
    });

    // Add unclustered points
    map.addLayer({
        id: 'incidents-unclustered',
        type: 'circle',
        source: 'incidents',
        filter: ['!', ['has', 'point_count']],
        paint: {
            'circle-color': [
                'match',
                ['get', 'FUNC_SYSNAME'],
                'Principal Arterial - Other', '#dc2626',
                'Minor Arterial', '#f59e0b',
                'Major Collector', '#10b981',
                'Minor Collector', '#3b82f6',
                'Local', '#8b5cf6',
                'Interstate', '#ef4444',
                '#6b7280' // default
            ],
            'circle-radius': 6,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
        }
    });

    // Add click handlers
    map.on('click', 'incidents-clusters', (e) => {
        const features = map.queryRenderedFeatures(e.point, {
            layers: ['incidents-clusters']
        });
        const clusterId = features[0].properties.cluster_id;
        map.getSource('incidents').getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            map.easeTo({
                center: features[0].geometry.coordinates,
                zoom: zoom
            });
        });
    });

    map.on('click', 'incidents-unclustered', (e) => {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const props = e.features[0].properties;

        const popup = createPopup(props);

        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(popup)
            .addTo(map);
    });

    // Change cursor on hover
    map.on('mouseenter', 'incidents-clusters', () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'incidents-clusters', () => {
        map.getCanvas().style.cursor = '';
    });
    map.on('mouseenter', 'incidents-unclustered', () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'incidents-unclustered', () => {
        map.getCanvas().style.cursor = '';
    });

    console.log(`Added ${filteredIncidents.length} incidents to map`);
}

// Create popup HTML
function createPopup(props) {
    const date = `${props.MONTH}/${props.DAY}/${props.YEAR}`;
    const time = props.HOUR !== 'Unknown' ? `${props.HOUR}:${props.MINUTE || '00'}` : 'Unknown';
    const street = props.TWAY_ID || 'Unknown Street';
    const crossStreet = props.TWAY_ID2 ? ` & ${props.TWAY_ID2}` : '';

    return `
        <div class="popup-content">
            <h4 class="popup-title">🚶 Pedestrian Fatality</h4>
            <div class="popup-details">
                <div><strong>Date:</strong> <span>${date}</span></div>
                <div><strong>Time:</strong> <span>${time}</span></div>
                <div><strong>Location:</strong> <span>${street}${crossStreet}</span></div>
                <div><strong>Road Type:</strong> <span>${props.FUNC_SYSNAME || 'Unknown'}</span></div>
                <div><strong>Lighting:</strong> <span>${props.LGT_CONDNAME || 'Unknown'}</span></div>
                <div><strong>Intersection:</strong> <span>${props.TYP_INTNAME || 'Unknown'}</span></div>
            </div>
        </div>
    `;
}

// Create charts
function createCharts() {
    createYearChart();
    createHourChart();
    createRoadTypeChart();
    createLightingChart();
}

// Year trend chart
function createYearChart() {
    const yearCounts = {};
    filteredIncidents.forEach(incident => {
        const year = incident.properties.YEAR;
        yearCounts[year] = (yearCounts[year] || 0) + 1;
    });

    const years = Object.keys(yearCounts).sort();
    const counts = years.map(year => yearCounts[year]);

    const ctx = document.getElementById('year-chart').getContext('2d');

    if (charts.yearChart) {
        charts.yearChart.destroy();
    }

    charts.yearChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Fatalities per Year',
                data: counts,
                borderColor: '#dc2626',
                backgroundColor: 'rgba(220, 38, 38, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Hour of day chart
function createHourChart() {
    const hourCounts = {};
    for (let i = 0; i < 24; i++) {
        hourCounts[i] = 0;
    }

    filteredIncidents.forEach(incident => {
        const hour = parseInt(incident.properties.HOUR);
        if (!isNaN(hour) && hour >= 0 && hour < 24) {
            hourCounts[hour]++;
        }
    });

    const hours = Object.keys(hourCounts).map(h => `${h}:00`);
    const counts = Object.values(hourCounts);

    const ctx = document.getElementById('hour-chart').getContext('2d');

    if (charts.hourChart) {
        charts.hourChart.destroy();
    }

    charts.hourChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours,
            datasets: [{
                label: 'Fatalities by Hour',
                data: counts,
                backgroundColor: '#f59e0b'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Road type chart
function createRoadTypeChart() {
    const roadTypeCounts = {};
    filteredIncidents.forEach(incident => {
        const roadType = incident.properties.FUNC_SYSNAME || 'Unknown';
        roadTypeCounts[roadType] = (roadTypeCounts[roadType] || 0) + 1;
    });

    const labels = Object.keys(roadTypeCounts);
    const counts = Object.values(roadTypeCounts);
    const colors = labels.map(label => ROAD_COLORS[label] || '#6b7280');

    const ctx = document.getElementById('road-type-chart').getContext('2d');

    if (charts.roadTypeChart) {
        charts.roadTypeChart.destroy();
    }

    charts.roadTypeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            size: 10
                        }
                    }
                }
            }
        }
    });
}

// Lighting conditions chart
function createLightingChart() {
    const lightingCounts = {};
    filteredIncidents.forEach(incident => {
        const lighting = incident.properties.LGT_CONDNAME || 'Unknown';
        lightingCounts[lighting] = (lightingCounts[lighting] || 0) + 1;
    });

    const labels = Object.keys(lightingCounts);
    const counts = Object.values(lightingCounts);

    const ctx = document.getElementById('lighting-chart').getContext('2d');

    if (charts.lightingChart) {
        charts.lightingChart.destroy();
    }

    charts.lightingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fatalities',
                data: counts,
                backgroundColor: '#10b981'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Update statistics
function updateStats() {
    document.getElementById('total-incidents').textContent = allIncidents.length;
    document.getElementById('filtered-incidents').textContent = filteredIncidents.length;

    const years = new Set(allIncidents.map(i => i.properties.YEAR));
    document.getElementById('years-covered').textContent = `${Math.min(...years)}-${Math.max(...years)}`;
}

// Update hot spots list
function updateHotSpotsList() {
    const container = document.getElementById('hot-spots-list');
    const sortedSpots = Object.entries(hotSpots.hot_spots || {})
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 10);

    if (sortedSpots.length === 0) {
        container.innerHTML = '<p>No high-risk streets found</p>';
        return;
    }

    container.innerHTML = sortedSpots.map(([street, data]) => `
        <div class="hot-spot-item" data-street="${street}">
            <div class="hot-spot-street">${street}</div>
            <div class="hot-spot-count">${data.count} incidents</div>
        </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.hot-spot-item').forEach(item => {
        item.addEventListener('click', () => {
            const street = item.dataset.street;
            highlightStreet(street);
        });
    });
}

// Highlight incidents on a specific street
function highlightStreet(street) {
    const streetIncidents = allIncidents.filter(i => i.properties.TWAY_ID === street);

    if (streetIncidents.length > 0) {
        // Fit map to street incidents
        const bounds = new mapboxgl.LngLatBounds();
        streetIncidents.forEach(incident => {
            bounds.extend(incident.geometry.coordinates);
        });
        map.fitBounds(bounds, { padding: 50 });
    }
}

// Apply filters
function applyFilters() {
    const yearStart = parseInt(document.getElementById('year-start').value) || 1991;
    const yearEnd = parseInt(document.getElementById('year-end').value) || 2022;
    const roadType = document.getElementById('road-type-filter').value;
    const hourStart = document.getElementById('hour-start').value;
    const hourEnd = document.getElementById('hour-end').value;
    const lighting = document.getElementById('lighting-filter').value;
    const intersectionType = document.getElementById('intersection-filter').value;

    filteredIncidents = allIncidents.filter(incident => {
        const props = incident.properties;
        const year = parseInt(props.YEAR);
        const hour = parseInt(props.HOUR);

        // Year filter
        if (year < yearStart || year > yearEnd) return false;

        // Road type filter
        if (roadType && props.FUNC_SYSNAME !== roadType) return false;

        // Hour filter
        if (hourStart && !isNaN(hour) && hour < parseInt(hourStart)) return false;
        if (hourEnd && !isNaN(hour) && hour > parseInt(hourEnd)) return false;

        // Lighting filter
        if (lighting && props.LGT_CONDNAME !== lighting) return false;

        // Intersection filter
        if (intersectionType && props.TYP_INTNAME !== intersectionType) return false;

        return true;
    });

    // Update map and charts
    addIncidentsToMap();
    createCharts();
    updateStats();

    console.log(`Filtered to ${filteredIncidents.length} incidents`);
}

// Reset filters
function resetFilters() {
    document.getElementById('year-start').value = '2018';
    document.getElementById('year-end').value = '2022';
    document.getElementById('road-type-filter').value = '';
    document.getElementById('hour-start').value = '';
    document.getElementById('hour-end').value = '';
    document.getElementById('lighting-filter').value = '';
    document.getElementById('intersection-filter').value = '';

    filteredIncidents = [...allIncidents];
    addIncidentsToMap();
    createCharts();
    updateStats();
}

// Setup event listeners
function setupEventListeners() {
    // Filter buttons
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);

    // Layer toggles
    document.getElementById('show-markers').addEventListener('change', (e) => {
        const visibility = e.target.checked ? 'visible' : 'none';
        map.setLayoutProperty('incidents-clusters', 'visibility', visibility);
        map.setLayoutProperty('incidents-cluster-count', 'visibility', visibility);
        map.setLayoutProperty('incidents-unclustered', 'visibility', visibility);
    });

    document.getElementById('show-heatmap').addEventListener('change', (e) => {
        const visibility = e.target.checked ? 'visible' : 'none';
        map.setLayoutProperty('incidents-heatmap', 'visibility', visibility);
    });

    document.getElementById('cluster-markers').addEventListener('change', (e) => {
        // Reload map with/without clustering
        const source = map.getSource('incidents');
        if (source) {
            const data = source._data;
            map.removeLayer('incidents-heatmap');
            map.removeLayer('incidents-clusters');
            map.removeLayer('incidents-cluster-count');
            map.removeLayer('incidents-unclustered');
            map.removeSource('incidents');

            map.addSource('incidents', {
                type: 'geojson',
                data: data,
                cluster: e.target.checked,
                clusterMaxZoom: 16,
                clusterRadius: 50
            });

            addIncidentsToMap();
        }
    });
}

// Loading helpers
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}
