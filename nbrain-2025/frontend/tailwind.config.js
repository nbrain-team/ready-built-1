/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#313d74',
        'primary-light': '#e8eaf6',
        secondary: '#4b5563',
      },
    },
  },
  plugins: [],
} 