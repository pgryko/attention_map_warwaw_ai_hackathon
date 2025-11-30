import { fetchApi, setTokens, clearTokens } from "./client";

/**
 * Register a new user.
 */
export async function register({ email, password }) {
  const data = await fetchApi("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    skipAuth: true,
  });
  return data;
}

/**
 * Login and get JWT tokens.
 */
export async function login({ email, password }) {
  // JWT endpoint uses username - derive from email if @ present
  const username = email.includes("@") ? email.split("@")[0] : email;
  const data = await fetchApi("/token/pair", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    skipAuth: true,
  });
  setTokens(data.access, data.refresh);
  return data;
}

/**
 * Logout - clear tokens.
 */
export function logout() {
  clearTokens();
}

/**
 * Get current user profile.
 */
export async function getCurrentUser() {
  return fetchApi("/auth/me");
}

/**
 * Update current user profile.
 */
export async function updateProfile(data) {
  return fetchApi("/auth/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Get current user's gamification stats.
 */
export async function getUserStats() {
  return fetchApi("/auth/me/stats");
}

/**
 * Get leaderboard.
 * @param {number} limit - Maximum number of users to return
 * @param {number|null} days - Filter by activity in last N days (null for all time)
 */
export async function getLeaderboard(limit = 10, days = null) {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (days) {
    params.append("days", days.toString());
  }
  return fetchApi(`/auth/leaderboard?${params.toString()}`);
}

/**
 * Get all available badges.
 */
export async function getAllBadges() {
  return fetchApi("/auth/badges");
}
