
tailwind.config = {
    theme: {
        extend: {
            colors: {
                background: '#0F0F1A',  // Very dark navy
                primary: {
                    DEFAULT: '#22d3ee',  // Cyan-400 (Cyberpunk Cyan)
                    hover: '#06b6d4',    // Cyan-500
                    light: '#67e8f9',    // Cyan-300
                },
                text: {
                    primary: '#FFFFFF',   // Pure white
                    secondary: '#94a3b8', // Slate-400
                    muted: '#64748b',     // Slate-500
                },
                card: {
                    DEFAULT: '#1e293b',   // Slate-800
                    border: '#334155',    // Slate-700
                },
                cta: {
                    DEFAULT: '#22d3ee',   // Cyan-400
                    hover: '#06b6d4',     // Cyan-500
                },
                accent: {
                    DEFAULT: '#3b82f6',   // Blue-500
                    hover: '#2563eb',     // Blue-600
                }
            },
            borderRadius: {
                'DEFAULT': '8px',
                'lg': '12px',
            },
            boxShadow: {
                'soft': '0 2px 8px rgba(0, 0, 0, 0.2)',
                'soft-lg': '0 4px 12px rgba(0, 0, 0, 0.3)',
            }
        }
    }
}
