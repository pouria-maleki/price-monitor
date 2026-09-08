/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0b1120",
          panel: "#111827",
          card: "#161f31",
        },
      },
    },
  },
  plugins: [],
};
