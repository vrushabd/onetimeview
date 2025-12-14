// Configuration
const API_BASE_URL = 'https://onetimeview-1.onrender.com';

// Helper function to build API URLs
function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
}

// Export for use in HTML files
if (typeof window !== 'undefined') {
    window.API_BASE_URL = API_BASE_URL;
    window.apiUrl = apiUrl;
}
