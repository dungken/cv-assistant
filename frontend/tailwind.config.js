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
        canvas: 'var(--bg-primary)',
        secondary: 'var(--bg-secondary)',
        surface: 'var(--bg-surface)',
        'surface-hover': 'var(--bg-surface-hover)',
        'text-primary': 'rgb(var(--text-primary) / <alpha-value>)',
        'text-main': 'rgb(var(--text-primary) / <alpha-value>)',
        'text-secondary': 'rgb(var(--text-secondary) / <alpha-value>)',
        'text-muted': 'rgb(var(--text-secondary) / <alpha-value>)',
        'border-main': 'var(--border-main)',
        'border-subtle': 'var(--border-subtle)',
        overlay: 'var(--bg-overlay)',
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
