
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import * as SecureStore from "expo-secure-store";

import {
  getCurrentUser,
  login as loginRequest,
  type AuthUser,
} from "../services/authService";

import {
  getUnreadCount,
  type Notification,
} from "../services/notificationService";

import {
  startNotificationSocket,
  stopNotificationSocket,
} from "../services/notificationSocket";

const TOKEN_KEY = "enterprise_business_insights_access_token";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  unreadCount: number;
  latestNotification: Notification | null;
  isNotificationConnected: boolean;
  refreshUnreadCount: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [latestNotification, setLatestNotification] =
    useState<Notification | null>(null);

  const [isNotificationConnected, setIsNotificationConnected] =
    useState(false);

  const refreshUnreadCount = useCallback(async () => {
    try {
      const result = await getUnreadCount();
      setUnreadCount(result.unread_count);
    } catch (error) {
      console.error("Unable to refresh unread count:", error);
    }
  }, []);

  const logout = useCallback(async () => {

    // Stop real-time notifications immediately.
    stopNotificationSocket();

    setIsNotificationConnected(false);
    setUnreadCount(0);
    setLatestNotification(null);

    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setUser(null);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await loginRequest(email.trim(), password);

      // Save the token securely before updating the signed-in state.
      await SecureStore.setItemAsync(TOKEN_KEY, result.access_token);
      setUser(result.user);
    },
    [],
  );

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      try {
        const token = await SecureStore.getItemAsync(TOKEN_KEY);

        if (!token) {
          return;
        }

        const currentUser = await getCurrentUser(token);

        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        // A missing, invalid, or expired session must not remain active.
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  // Start and stop the WebSocket based on authentication.
  useEffect(() => {
    if (!user) {
      stopNotificationSocket();
      setIsNotificationConnected(false);
      setUnreadCount(0);
      setLatestNotification(null);
      return;
    }

    let isActive = true;

    // Load the existing unread notification count.
    void refreshUnreadCount();

    // Connect to the authenticated notification WebSocket.
    startNotificationSocket(
      (notification) => {
        if (!isActive) {
          return;
        }

        setLatestNotification(notification);

        setUnreadCount((currentCount) =>
          currentCount + (notification.is_read ? 0 : 1),
        );
      },
      (connected) => {
        if (isActive) {
          setIsNotificationConnected(connected);
        }
      },
    );

    return () => {
      isActive = false;
      stopNotificationSocket();
    };
  }, [user, refreshUnreadCount]);

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    unreadCount,
    latestNotification,
    isNotificationConnected,
    refreshUnreadCount,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
