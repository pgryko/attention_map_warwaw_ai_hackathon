import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { getAccessToken, clearTokens } from "../api/client";
import * as authApi from "../api/auth";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = getAccessToken();
      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.error("Failed to get user:", err);
          clearTokens();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    setError(null);
    try {
      await authApi.login({ email, password });
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const register = useCallback(
    async (email, password) => {
      setError(null);
      try {
        await authApi.register({ email, password });
        // Auto-login after registration
        return login(email, password);
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [login],
  );

  const logout = useCallback(() => {
    authApi.logout();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      return userData;
    } catch (err) {
      console.error("Failed to refresh user:", err);
      throw err;
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    isStaff: user?.is_staff || false,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
