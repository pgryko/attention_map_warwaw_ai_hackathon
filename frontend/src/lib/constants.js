// API Configuration
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// Event Categories
export const EVENT_CATEGORIES = {
  fire: { label: "Fire", icon: "🔥", color: "#ef4444" },
  accident: { label: "Accident", icon: "🚗", color: "#f59e0b" },
  infrastructure: { label: "Infrastructure", icon: "🚧", color: "#f97316" },
  environment: { label: "Environment", icon: "🌳", color: "#22c55e" },
  safety: { label: "Safety", icon: "⚠️", color: "#eab308" },
  other: { label: "Other", icon: "📍", color: "#3b82f6" },
};

// Event Statuses
export const EVENT_STATUSES = {
  new: {
    label: "New",
    color: "#ef4444",
    bgColor: "bg-red-100 dark:bg-red-900",
  },
  verified: {
    label: "Verified",
    color: "#f59e0b",
    bgColor: "bg-amber-100 dark:bg-amber-900",
  },
  in_progress: {
    label: "In Progress",
    color: "#3b82f6",
    bgColor: "bg-blue-100 dark:bg-blue-900",
  },
  resolved: {
    label: "Resolved",
    color: "#22c55e",
    bgColor: "bg-emerald-100 dark:bg-emerald-900",
  },
  rejected: {
    label: "Rejected",
    color: "#6b7280",
    bgColor: "bg-gray-100 dark:bg-gray-800",
  },
};

// Severity Levels
export const SEVERITY_LEVELS = {
  1: { label: "Low", color: "#22c55e" },
  2: { label: "Medium", color: "#eab308" },
  3: { label: "High", color: "#f97316" },
  4: { label: "Critical", color: "#ef4444" },
};

// Time Filters
export const TIME_FILTERS = {
  "": { label: "All Time", hours: null },
  "1h": { label: "Last Hour", hours: 1 },
  "24h": { label: "Last 24 Hours", hours: 24 },
  "7d": { label: "Last 7 Days", hours: 168 },
  "30d": { label: "Last 30 Days", hours: 720 },
};

// Map Configuration
export const MAP_CONFIG = {
  defaultCenter: [52.2297, 21.0122], // Warsaw
  defaultZoom: 13,
  tileLayer: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
};

// Query Keys for TanStack Query
export const QUERY_KEYS = {
  events: "events",
  event: "event",
  clusters: "clusters",
  stats: "stats",
  user: "user",
  userStats: "userStats",
  leaderboard: "leaderboard",
  badges: "badges",
};

// Local Storage Keys
export const STORAGE_KEYS = {
  accessToken: "access_token",
  refreshToken: "refresh_token",
  theme: "theme",
};
