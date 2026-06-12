/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          deep: '#0a0a0f',
          base: '#0f0f14',
          surface: '#16161d',
          hover: '#1e1e28',
        },
        text: {
          primary: '#e8e6e3',
          secondary: '#8b8994',
          muted: '#4a4853',
        },
        accent: {
          DEFAULT: '#c9a855',
          hover: '#dbb960',
          dim: '#2a2418',
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', 'serif'],
        sans: ['"Noto Sans SC"', 'sans-serif'],
      },
      borderRadius: {
        card: '12px',
      },
      animation: {
        blink: 'blink 0.8s step-end infinite',
      },
      keyframes: {
        blink: {
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
