
tailwind.config = {
    theme: {
        extend: {
            colors: {
                background: '#0F0F1A',  // Very dark navy
                primary: {
                    DEFAULT: '#6D5DF6',  // Soft purple
                    hover: '#5A4BE0',    // Slightly darker purple
                },
                text: {
                    primary: '#FFFFFF',   // Pure white
                    secondary: '#C7C9E2', // Soft light gray
                    muted: '#8E90B5',     // Gray-purple
                },
                card: {
                    DEFAULT: '#1A1B2E',   // Dark muted blue
                    border: '#2A2C45',    // Subtle dark lines
                },
                cta: {
                    DEFAULT: '#6D5DF6',   // Soft purple
                    hover: '#5A4BE0',     // Darker purple
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
