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

// --- Shared History Logic ---

function saveSecretToHistory(url, hasPassword, passwordText = null) {
    let history = JSON.parse(localStorage.getItem('secretHistory') || '[]');
    
    // Check if already exists to prevent duplicates
    if (history.find(s => s.url === url)) {
        if (typeof window.loadSecretHistory === 'function') {
            window.loadSecretHistory();
        }
        return;
    }

    const newSecret = {
        id: Date.now().toString(),
        url: url,
        date: new Date().toISOString(),
        hasPassword: hasPassword,
        password: passwordText,
        status: 'Active' // We just use Active now
    };

    history.unshift(newSecret); // Add to beginning
    
    // Limit history to 20 items
    if (history.length > 20) {
        history = history.slice(0, 20);
    }
    
    localStorage.setItem('secretHistory', JSON.stringify(history));
    
    if (typeof window.loadSecretHistory === 'function') {
        window.loadSecretHistory();
    }
}

function removeHistoryItem(id) {
    let history = JSON.parse(localStorage.getItem('secretHistory') || '[]');
    history = history.filter(s => s.id !== id);
    localStorage.setItem('secretHistory', JSON.stringify(history));
    if (typeof window.loadSecretHistory === 'function') {
        window.loadSecretHistory();
    }
}

function clearAllHistory() {
    if (confirm('Are you sure you want to clear your recent links history?')) {
        localStorage.removeItem('secretHistory');
        if (typeof window.loadSecretHistory === 'function') {
            window.loadSecretHistory();
        }
    }
}

function copyHistoryLink(url) {
    const tempInput = document.createElement('input');
    tempInput.value = url;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand('copy');
    document.body.removeChild(tempInput);
    
    if (typeof showToast === 'function') {
        showToast('Link copied to clipboard!');
    } else {
        alert('Link copied to clipboard!');
    }
}
function showPassword(id) {
    const history = JSON.parse(localStorage.getItem('secretHistory') || '[]');
    const secret = history.find(s => s.id === id);
    if (secret && secret.password) {
        alert('Password for this link:\n\n' + secret.password);
    } else {
        alert('Password was set, but not saved locally.');
    }
}
