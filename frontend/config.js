// Configuration - Auto-detect environment
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? `http://${window.location.hostname}:${window.location.port || 8000}`
    : 'https://onetimeview-1.onrender.com';

// Helper function to build API URLs
function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
}

// Export for use in HTML files
if (typeof window !== 'undefined') {
    window.API_BASE_URL = API_BASE_URL;
    window.apiUrl = apiUrl;
}
