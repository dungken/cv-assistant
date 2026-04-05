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
        accent: {
          primary: 'rgb(var(--accent-primary) / <alpha-value>)',
          secondary: 'rgb(var(--accent-secondary) / <alpha-value>)',
        },
        // Semantic variables from index.css
        canvas: 'rgb(var(--bg-primary) / <alpha-value>)',
        secondary: 'rgb(var(--bg-secondary) / <alpha-value>)',
        surface: {
          DEFAULT: 'rgb(var(--bg-surface) / <alpha-value>)',
          hover: 'rgb(var(--bg-surface-hover) / <alpha-value>)',
        },
        text: {
          primary: 'rgb(var(--text-primary) / <alpha-value>)',
          main: 'rgb(var(--text-primary) / <alpha-value>)',
          secondary: 'rgb(var(--text-secondary) / <alpha-value>)',
          muted: 'rgb(var(--text-secondary) / 0.6)',
        },
        // Using a flat key for borders to ensure @apply compatibility
        'main-border': 'rgb(var(--border-main) / <alpha-value>)',
        'subtle-border': 'rgb(var(--border-subtle) / <alpha-value>)',
        overlay: 'rgb(var(--bg-overlay) / <alpha-value>)',
      },
      // Adding custom opacities used in border-refinement
      opacity: {
        '8': '0.08',
        '12': '0.12',
        '15': '0.15',
      },
      borderRadius: {
        'xl': '1.25rem',
        '2xl': '1.75rem',
        '3xl': '2.25rem',
      },
    },
  },
  plugins: [],
}
