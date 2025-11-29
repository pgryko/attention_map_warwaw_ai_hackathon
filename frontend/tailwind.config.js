/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Severity colors
        "severity-low": "#22c55e", // green-500
        "severity-medium": "#eab308", // yellow-500
        "severity-high": "#f97316", // orange-500
        "severity-critical": "#ef4444", // red-500
      },
    },
  },
  plugins: [],
};
