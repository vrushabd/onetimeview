tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
            },
            colors: {
                background: '#0a0a0a',
                surface: '#111111',
                primary: {
                    DEFAULT: '#ededed',
                    hover: '#ffffff',
                    dim: 'rgba(255, 255, 255, 0.1)',
                },
                accent: {
                    DEFAULT: '#3b82f6', // Clean blue instead of neon purple
                    hover: '#60a5fa',
                },
                destructive: '#ef4444',
                text: {
                    primary: '#ededed',
                    secondary: '#a1a1aa',
                    muted: '#52525b'
                },
                card: {
                    DEFAULT: '#111111',
                    border: '#3f3f46',
                },
                success: '#10b981'
            },
            boxShadow: {
                // Removing glow shadows, replacing with subtle structural shadows if needed
                'subtle': '0 1px 2px rgba(0, 0, 0, 0.5)',
            }
        }
    }
}
