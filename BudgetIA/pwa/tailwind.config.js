/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Semantic Tokens for Theming
        primary: {
          DEFAULT: '#059669', // emerald-600
          hover: '#047857',   // emerald-700
          light: '#10b981',   // emerald-500
          soft: 'rgba(16, 185, 129, 0.1)', // emerald-500/10
        },
        surface: {
          DEFAULT: '#111827', // gray-900 (Page BG)
          card: 'rgba(17, 24, 39, 0.5)', // gray-900/50
          hover: '#1f2937',   // gray-800
        },
        border: {
          DEFAULT: '#1f2937', // gray-800
          hover: '#374151',   // gray-700
        },
        danger: {
          DEFAULT: '#ef4444', // red-500
          soft: 'rgba(239, 68, 68, 0.1)', // red-500/10
          border: 'rgba(127, 29, 29, 0.3)', // red-900/30
        }
      },
    },
  },
  plugins: [],
}
