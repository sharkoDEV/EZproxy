/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#0a0a0a",
        panel: "#111111",
        line: "#222222",
        neon: "#00ff99",
        magenta: "#ff00ff",
        ink: "#e0e0e0"
      },
      boxShadow: {
        glow: "0 0 30px rgba(0, 255, 153, 0.18)",
        magenta: "0 0 24px rgba(255, 0, 255, 0.18)"
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"]
      }
    }
  },
  plugins: []
};
