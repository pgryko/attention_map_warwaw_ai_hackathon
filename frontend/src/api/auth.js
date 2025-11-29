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
  const data = await fetchApi("/auth/token/pair", {
    method: "POST",
    body: JSON.stringify({ email, password }),
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
 */
export async function getLeaderboard(limit = 10) {
  return fetchApi(`/auth/leaderboard?limit=${limit}`);
}

/**
 * Get all available badges.
 */
export async function getAllBadges() {
  return fetchApi("/auth/badges");
}
