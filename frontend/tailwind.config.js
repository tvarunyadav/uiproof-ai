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
          hover: '#27272A',
        },
        border: {
          DEFAULT: '#27272A',
          strong: '#3F3F46',
          subtle: '#1F1F23',
        },
        accent: {
          DEFAULT: '#6366F1',
          hover: '#818CF8',
          subtle: 'rgba(99, 102, 241, 0.12)',
        },
        status: {
          success: '#22C55E',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
        },
        text: {
          primary: '#FAFAFA',
          secondary: '#A1A1AA',
          muted: '#71717A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
        xl: '10px',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.5)',
        glow: '0 0 15px -3px rgba(99, 102, 241, 0.25)',
      },
    },
  },
  plugins: [],
}
