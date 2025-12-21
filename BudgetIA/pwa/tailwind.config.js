/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // You can add custom tokens here if needed to match Streamlit or a new design system
      },
    },
  },
  plugins: [],
}
