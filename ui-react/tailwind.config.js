/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
      },
      colors: {
        background: '#F3F4F6',
        surface: '#FFFFFF',
        primary: {
          500: '#FF6857',
          600: '#e55a4a',
        },
        secondary: {
          orange: '#FFA94D',
          teal: '#4DB6AC',
          blue: '#4A90E2',
          mint: '#E6F6F1',
        },
        neutral: {
          900: '#1F2937',
          700: '#4B5563',
          500: '#9CA3AF',
          300: '#E5E7EB',
          100: '#F3F4F6',
        },
        semantic: {
          success: '#22C55E',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
          purple: '#8B5CF6',
        }
      }
    },
  },
  plugins: [],
}
