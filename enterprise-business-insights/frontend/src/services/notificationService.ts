
import * as SecureStore from "expo-secure-store";

const API_BASE_URL = "http://192.168.1.7:8000";
const TOKEN_KEY = "enterprise_business_insights_access_token";

export type NotificationType =
  | "Revenue"
  | "Sales"
  | "Order"
  | "Customer"
  | "System";

export type NotificationPriority =
  | "Low"
  | "Medium"
  | "High"
  | "Critical";

export interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  related_entity_id: number | null;
  related_entity_type: string | null;
  recipient_user_id: number;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface NotificationMessage {
  message: string;
}

export interface NotificationFilters {
  page?: number;
  page_size?: number;
  type?: NotificationType;
  priority?: NotificationPriority;
  is_read?: boolean;
  sort_order?: "newest" | "oldest";
}

async function getAccessToken(): Promise<string> {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);

  if (!token) {
    throw new Error("Your session has expired. Please log in again.");
  }

  return token;
}

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data.detail ?? `Request failed. HTTP ${response.status}`;
  } catch {
    return `Request failed. HTTP ${response.status}`;
  }
}

async function authenticatedRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getAccessToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (response.status === 401) {
    throw new Error("Authentication failed. Please log in again.");
  }

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as T;
}

export async function getNotifications(
  filters: NotificationFilters = {},
): Promise<NotificationListResponse> {
  const params = new URLSearchParams();

  params.append("page", String(filters.page ?? 1));
  params.append("page_size", String(filters.page_size ?? 20));
  params.append("sort_order", filters.sort_order ?? "newest");

  if (filters.type) {
    params.append("type", filters.type);
  }

  if (filters.priority) {
    params.append("priority", filters.priority);
  }

  if (filters.is_read !== undefined) {
    params.append("is_read", String(filters.is_read));
  }

  return authenticatedRequest<NotificationListResponse>(
    `/api/notifications?${params.toString()}`,
  );
}

export async function getUnreadCount(): Promise<UnreadCountResponse> {
  return authenticatedRequest<UnreadCountResponse>(
    "/api/notifications/unread-count",
  );
}

export async function markNotificationAsRead(
  notificationId: number,
): Promise<Notification> {
  return authenticatedRequest<Notification>(
    `/api/notifications/${notificationId}/read`,
    {
      method: "PATCH",
    },
  );
}

export async function markAllNotificationsAsRead(): Promise<NotificationMessage> {
  return authenticatedRequest<NotificationMessage>(
    "/api/notifications/read-all",
    {
      method: "PATCH",
    },
  );
}

export async function deleteNotification(
  notificationId: number,
): Promise<NotificationMessage> {
  return authenticatedRequest<NotificationMessage>(
    `/api/notifications/${notificationId}`,
    {
      method: "DELETE",
    },
  );
}
