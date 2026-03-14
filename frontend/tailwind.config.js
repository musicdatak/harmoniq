/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#0a0a0f",
          surface: "#14141f",
          card: "#1a1a2e",
        },
        teal: {
          DEFAULT: "#00e5c7",
          50: "#e6fff9",
          100: "#b3ffef",
          200: "#80ffe5",
          300: "#4dffdb",
          400: "#1affd1",
          500: "#00e5c7",
          600: "#00b89f",
          700: "#008a77",
          800: "#005c50",
          900: "#002e28",
        },
        amber: {
          DEFAULT: "#f59e0b",
        },
        error: "#ef4444",
      },
      fontFamily: {
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
