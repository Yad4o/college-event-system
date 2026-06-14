/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper:   '#FAF7F0',   // warm background
        card:    '#F1E9DA',   // card cream
        ink:     '#1A1A2E',   // near-black text / headers
        rust:    '#FF6B35',   // primary accent — bulletin orange
        pine:    '#2D6A4F',   // secondary accent — confirmed / open
        alert:   '#E63946',   // error / cancelled
        gold:    '#E0A458',   // tertiary — badges, certificates
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        sans:    ['Inter', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      boxShadow: {
        pin: '0 1px 2px rgba(26,26,46,0.06), 0 4px 12px rgba(26,26,46,0.06)',
        'pin-hover': '0 4px 8px rgba(26,26,46,0.08), 0 12px 24px rgba(26,26,46,0.10)',
      },
    },
  },
  plugins: [],
}
