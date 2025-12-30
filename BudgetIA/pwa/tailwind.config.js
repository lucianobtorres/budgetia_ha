import { themeColors } from './theme.js';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // --- Semantic Tokens (The Truth) ---
        primary: {
          DEFAULT: '#059669', // Emerald 600
          hover: '#047857',   // Emerald 700
          light: '#10b981',   // Emerald 500
          soft: 'rgba(16, 185, 129, 0.1)', // Highlight/Ring
        },
        surface: {
          DEFAULT: themeColors.background, // Centrally managed
          card: themeColors.card,          // Centrally managed
          hover: themeColors.hover,        // Centrally managed (Slate 800)
          input: themeColors.card,         // Input BG (Matches card)
        },
        border: {
          DEFAULT: themeColors.border,     // Centrally managed (Slate 800)
          hover: '#3f3f46',   // Gray 700 - Keep or update? Let's leave for contrast or update to Slate 700 (#334155) if strictly needed.
        },
        text: {
          primary: themeColors.text.primary,
          secondary: themeColors.text.secondary,
          muted: themeColors.text.muted,
        },
        danger: {
          DEFAULT: '#ef4444', // Red 500
          soft: 'rgba(239, 68, 68, 0.1)',
          border: 'rgba(127, 29, 29, 0.3)',
        },
        
        // --- Legacy/Safety (Mapped to Semantics) ---
        emerald: {
          500: '#10b981',
          600: '#059669', // Mapped to primary
          700: '#047857',
          900: '#064e3b',
        },
        gray: {
            700: '#3f3f46', // Border hover
            800: '#27272a', // Border/Card
            900: themeColors.card, // Card fallback
            950: themeColors.background, // Deep BG fallback
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'], // Optional for Headers
      },
      dropShadow: {
        'glow': themeColors.effects.glow,
        'glow-subtle': themeColors.effects.glowSubtle,
      }
    },
  },
  plugins: [],
}
