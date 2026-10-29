/** @type {import('tailwindcss').Config} */

// The zinc scale is driven by CSS variables so the whole UI can switch between
// dark and light mode by swapping variable values (see globals.css).
const zincShade = (n) => `rgb(var(--zinc-${n}) / <alpha-value>)`;

module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'rgba(var(--background), <alpha-value>)',
        foreground: 'rgba(var(--foreground), <alpha-value>)',
        zinc: {
          50: zincShade(50), 100: zincShade(100), 200: zincShade(200), 300: zincShade(300), 400: zincShade(400),
          500: zincShade(500), 600: zincShade(600), 700: zincShade(700), 800: zincShade(800), 900: zincShade(900), 950: zincShade(950),
        },
        primary: {
          DEFAULT: '#6366f1', // Indigo
          dark: '#4f46e5',
        },
        secondary: {
          DEFAULT: '#a855f7', // Violet
          dark: '#9333ea',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
