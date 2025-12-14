
tailwind.config = {
    theme: {
        extend: {
            colors: {
                background: '#0F0B1E',
                primary: {
                    DEFAULT: '#6D28D9',
                    hover: '#9333EA', // Using the end of the gradient as hover/lighter shade for now
                    light: '#A855F7', // Secondary accent
                },
                secondary: {
                    DEFAULT: '#A855F7',
                },
                text: {
                    primary: '#FFFFFF',
                    secondary: '#C4B5FD',
                },
                card: {
                    DEFAULT: '#1E1B3A',
                    border: '#1E1B3A',
                },
                cta: {
                    DEFAULT: '#7C3AED',
                    hover: '#6D28D9',
                }
            }
        }
    }
}
