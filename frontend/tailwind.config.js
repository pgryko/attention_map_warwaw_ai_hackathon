/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Severity colors
        "severity-low": "#22c55e", // green-500
        "severity-medium": "#eab308", // yellow-500
        "severity-high": "#f97316", // orange-500
        "severity-critical": "#ef4444", // red-500
        // Status colors
        "status-new": "#ef4444",
        "status-verified": "#f59e0b",
        "status-progress": "#3b82f6",
        "status-resolved": "#10b981",
        "status-rejected": "#6b7280",
      },
    },
  },
  plugins: [],
};
