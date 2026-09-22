/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#09090B',
        surface: {
          DEFAULT: '#111113',
          raised: '#18181B',
          hover: '#222225',
        },
        border: {
          DEFAULT: '#27272A',
          subtle: '#1F1F23',
        },
        accent: {
          DEFAULT: '#6366F1',
          hover: '#818CF8',
          subtle: 'rgba(99, 102, 241, 0.1)',
        },
        status: {
          success: '#22C55E',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
        },
        text: {
          primary: '#FAFAFA',
          secondary: '#D4D4D8',
          muted: '#A1A1AA',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '8px',
        lg: '10px',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.4)',
        glow: '0 0 15px -3px rgba(99, 102, 241, 0.2)',
      },
    },
  },
  plugins: [],
}
