// MapBox Configuration
// Copy this file to src/frontend/js/config.js and add your MapBox token

const CONFIG = {
    // Get your free MapBox token at: https://account.mapbox.com/
    // Sign up at: https://www.mapbox.com/signup/
    MAPBOX_TOKEN: 'pk.YOUR_TOKEN_HERE',

    // API Configuration (usually don't need to change these)
    API_BASE_URL: window.location.hostname === 'localhost' ? 'http://localhost:5000/api' : '/api',

    // Map Configuration
    TUCSON_CENTER: [-110.9747, 32.2226],
    TUCSON_BOUNDS: [
        [-111.3, 32.0],  // Southwest
        [-110.6, 32.5]   // Northeast
    ],
    DEFAULT_ZOOM: 11
};

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
