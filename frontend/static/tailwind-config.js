
tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            colors: {
                background: 'hsl(220, 20%, 6%)', // Deep navy
                surface: 'hsl(222, 18%, 10%)', // Slightly lighter background
                primary: {
                    DEFAULT: 'hsl(190, 95%, 50%)', // Electric Cyan
                    hover: 'hsl(190, 85%, 60%)',
                    dim: 'rgba(6, 182, 212, 0.1)',
                },
                accent: {
                    DEFAULT: 'hsl(280, 100%, 65%)', // Bright Purple
                    hover: 'hsl(280, 90%, 75%)',
                },
                destructive: 'hsl(0, 84%, 60%)', // Bright Red
                text: {
                    primary: '#FFFFFF',
                    secondary: 'hsl(215, 20%, 65%)', // Muted Gray
                    muted: 'hsl(215, 20%, 45%)'
                },
                card: {
                    DEFAULT: 'rgba(30, 35, 60, 0.6)', // Glass-like base
                    border: 'rgba(6, 182, 212, 0.2)', // Cyan border hint
                },
                success: 'hsl(150, 90%, 45%)' // Neon Green
            },
            boxShadow: {
                'glow': '0 0 20px rgba(6, 182, 212, 0.35)',
                'glow-sm': '0 0 10px rgba(6, 182, 212, 0.25)',
                'glow-accent': '0 0 20px rgba(192, 132, 252, 0.35)',
            }
        }
    }
}
