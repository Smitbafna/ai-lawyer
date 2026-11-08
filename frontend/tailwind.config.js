/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
    "./src/index.css",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f5efe6",
        card: "#fffbf8",
        primary: "#38251d",
        "primary-hover": "#51382b",
        secondary: "#6d5040",
        accent: "#a87952",
        foreground: "#302019",
        "muted-foreground": "#817268",
        border: "#e6d9ca",
        "input-bg": "#faf7f2",
      },
    },
  },
  plugins: [],
}
