(function () {
    const COOKIE_NAME = 'cookie_consent';

    function hasConsented() {
        return localStorage.getItem(COOKIE_NAME) === 'accepted';
    }

    function showBanner() {
        if (hasConsented()) return;

        const banner = document.createElement('div');
        banner.id = 'cookie-banner';
        banner.className = 'fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-md border-t border-white/10 p-4 z-50 animate-slide-up transform transition-all duration-300';
        banner.innerHTML = `
            <div class="container mx-auto max-w-6xl flex flex-col md:flex-row items-center justify-between gap-4">
                <div class="text-sm text-text-secondary">
                    <p>We use cookies to improve your experience and analyze traffic. By using our site, you agree to our <a href="/privacy" class="text-primary hover:text-white underline">Privacy Policy</a>.</p>
                </div>
                <div class="flex gap-4">
                    <button id="accept-cookies" class="px-6 py-2 bg-primary hover:bg-primary-hover text-background font-bold rounded-lg shadow-glow transition-all text-sm">
                        Accept
                    </button>
                    <button id="decline-cookies" class="px-6 py-2 bg-white/5 hover:bg-white/10 text-white font-medium rounded-lg border border-white/10 transition-all text-sm">
                        Decline
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        document.getElementById('accept-cookies').onclick = () => {
            localStorage.setItem(COOKIE_NAME, 'accepted');
            banner.remove();
        };

        document.getElementById('decline-cookies').onclick = () => {
            localStorage.setItem(COOKIE_NAME, 'declined');
            banner.remove();
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', showBanner);
    } else {
        showBanner();
    }
})();
