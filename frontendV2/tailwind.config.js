/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 金融主题色彩
        'market-green': '#10b981',
        'market-red': '#ef4444',
        'market-blue': '#3b82f6',
        'market-gray': '#6b7280',
        'market-dark': '#1f2937',
        'market-light': '#f9fafb',
      },
      borderRadius: {
        '4xl': '2rem',
      }
    },
  },
  plugins: [],
}