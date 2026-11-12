import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { useFocusEffect } from "@react-navigation/native";

import { useAuth } from "../context/AuthContext";

import {
  deleteNotification,
  getNotifications,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  type Notification,
} from "../services/notificationService";

type NotificationFilter = "all" | "unread" | "read";

function getPriorityColor(priority: Notification["priority"]): string {
  switch (priority) {
    case "Critical":
      return "#DC2626";
    case "High":
      return "#EA580C";
    case "Medium":
      return "#D97706";
    default:
      return "#64748B";
  }
}

export default function AlertsScreen() {
  const {
    latestNotification,
    refreshUnreadCount,
  } = useAuth();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<NotificationFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMarkingAll, setIsMarkingAll] = useState(false);

  const loadNotifications = useCallback(async () => {
    try {
      const response = await getNotifications({
        page: 1,
        page_size: 50,
        sort_order: "newest",
        ...(filter === "unread"
          ? { is_read: false }
          : filter === "read"
            ? { is_read: true }
            : {}),
      });

      setNotifications(response.items);
      await refreshUnreadCount();
    } catch (error) {
      Alert.alert(
        "Unable to load alerts",
        error instanceof Error
          ? error.message
          : "Please try again.",
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [filter, refreshUnreadCount]);

  // Reload notifications whenever the Alerts tab becomes active.
  useFocusEffect(
    useCallback(() => {
      void loadNotifications();
    }, [loadNotifications]),
  );

  // Add new notifications received through the WebSocket.
  useEffect(() => {
    if (!latestNotification) {
      return;
    }

    if (filter === "unread" && latestNotification.is_read) {
      return;
    }

    if (filter === "read" && !latestNotification.is_read) {
      return;
    }

    setNotifications((current) => {
      const alreadyExists = current.some(
        (item) => item.id === latestNotification.id,
      );

      if (alreadyExists) {
        return current;
      }

      return [latestNotification, ...current];
    });
  }, [latestNotification, filter]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    void loadNotifications();
  };

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      const updatedNotification =
        await markNotificationAsRead(notificationId);

      setNotifications((current) =>
        current.map((item) =>
          item.id === notificationId
            ? updatedNotification
            : item,
        ),
      );

      await refreshUnreadCount();
    } catch (error) {
      Alert.alert(
        "Unable to update alert",
        error instanceof Error
          ? error.message
          : "Please try again.",
      );
    }
  };

  const handleMarkAllAsRead = async () => {
    if (isMarkingAll) {
      return;
    }

    setIsMarkingAll(true);

    try {
      await markAllNotificationsAsRead();

      setNotifications((current) =>
        current.map((item) => ({
          ...item,
          is_read: true,
          read_at: new Date().toISOString(),
        })),
      );

      await refreshUnreadCount();
    } catch (error) {
      Alert.alert(
        "Unable to update alerts",
        error instanceof Error
          ? error.message
          : "Please try again.",
      );
    } finally {
      setIsMarkingAll(false);
    }
  };

  const handleDelete = (notificationId: number) => {
    Alert.alert(
      "Delete notification",
      "Are you sure you want to delete this notification?",
      [
        {
          text: "Cancel",
          style: "cancel",
        },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await deleteNotification(notificationId);

              setNotifications((current) =>
                current.filter(
                  (item) => item.id !== notificationId,
                ),
              );

              await refreshUnreadCount();
            } catch (error) {
              Alert.alert(
                "Unable to delete notification",
                error instanceof Error
                  ? error.message
                  : "Please try again.",
              );
            }
          },
        },
      ],
    );
  };

  const renderNotification = ({
    item,
  }: {
    item: Notification;
  }) => {
    const priorityColor = getPriorityColor(item.priority);

    return (
      <View
        style={[
          styles.notificationCard,
          !item.is_read && styles.unreadCard,
        ]}
      >
        <View style={styles.notificationHeader}>
          <View style={styles.titleContainer}>
            <Text style={styles.notificationTitle}>
              {item.title}
            </Text>

            {!item.is_read && (
              <View style={styles.unreadDot} />
            )}
          </View>

          <Text
            style={[
              styles.priority,
              { color: priorityColor },
            ]}
          >
            {item.priority}
          </Text>
        </View>

        <Text style={styles.message}>
          {item.message}
        </Text>

        <View style={styles.metadata}>
          <Text style={styles.type}>
            {item.notification_type}
          </Text>

          <Text style={styles.date}>
            {new Date(item.created_at).toLocaleString()}
          </Text>
        </View>

        <View style={styles.actions}>
          {!item.is_read && (
            <TouchableOpacity
              style={styles.readButton}
              onPress={() => handleMarkAsRead(item.id)}
            >
              <Text style={styles.readButtonText}>
                Mark as read
              </Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => handleDelete(item.id)}
          >
            <Text style={styles.deleteButtonText}>
              Delete
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.heading}>Alerts</Text>
        <Text style={styles.subtitle}>
          Your business notifications
        </Text>
      </View>

      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[
            styles.filterButton,
            filter === "all" && styles.activeFilter,
          ]}
          onPress={() => setFilter("all")}
        >
          <Text
            style={[
              styles.filterText,
              filter === "all" && styles.activeFilterText,
            ]}
          >
            All
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.filterButton,
            filter === "unread" && styles.activeFilter,
          ]}
          onPress={() => setFilter("unread")}
        >
          <Text
            style={[
              styles.filterText,
              filter === "unread" && styles.activeFilterText,
            ]}
          >
            Unread
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.filterButton,
            filter === "read" && styles.activeFilter,
          ]}
          onPress={() => setFilter("read")}
        >
          <Text
            style={[
              styles.filterText,
              filter === "read" && styles.activeFilterText,
            ]}
          >
            Read
          </Text>
        </TouchableOpacity>

        <View style={styles.spacer} />

        {filter !== "read" && (
          <TouchableOpacity
            onPress={handleMarkAllAsRead}
            disabled={isMarkingAll}
          >
            <Text style={styles.markAllText}>
              {isMarkingAll ? "Updating..." : "Mark all read"}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {isLoading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#2563EB" />
          <Text style={styles.loadingText}>
            Loading alerts...
          </Text>
        </View>
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderNotification}
          contentContainerStyle={
            notifications.length === 0
              ? styles.emptyList
              : styles.listContent
          }
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              colors={["#2563EB"]}
            />
          }
          ListEmptyComponent={
            <View style={styles.centerContainer}>
              <Text style={styles.emptyTitle}>
                No notifications
              </Text>
              <Text style={styles.emptyMessage}>
                New business alerts will appear here.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F8FAFC",
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 55,
    paddingBottom: 18,
    backgroundColor: "#FFFFFF",
  },
  heading: {
    fontSize: 26,
    fontWeight: "700",
    color: "#0F172A",
  },
  subtitle: {
    fontSize: 14,
    color: "#64748B",
    marginTop: 5,
  },
  filterContainer: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#FFFFFF",
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
    marginBottom: 10,
  },
  filterButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    backgroundColor: "#F1F5F9",
  },
  activeFilter: {
    backgroundColor: "#2563EB",
  },
  filterText: {
    color: "#475569",
    fontSize: 13,
    fontWeight: "600",
  },
  activeFilterText: {
    color: "#FFFFFF",
  },
  spacer: {
    flex: 1,
  },
  markAllText: {
    color: "#2563EB",
    fontSize: 12,
    fontWeight: "600",
  },
  listContent: {
    padding: 14,
    paddingBottom: 25,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 20,
  },
  notificationCard: {
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },
  unreadCard: {
    // borderLeftWidth: 4,
    // borderLeftColor: "#2563EB",
  },
  notificationHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  titleContainer: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    marginRight: 8,
  },
  notificationTitle: {
    flexShrink: 1,
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    // backgroundColor: "#2563EB",
    marginLeft: 8,
  },
  priority: {
    fontSize: 11,
    fontWeight: "700",
  },
  message: {
    fontSize: 13,
    lineHeight: 20,
    color: "#475569",
    marginTop: 10,
  },
  metadata: {
    flexDirection: "row",
    justifyContent: "space-between",
    flexWrap: "wrap",
    marginTop: 12,
  },
  type: {
    fontSize: 11,
    fontWeight: "600",
    color: "#64748B",
  },
  date: {
    fontSize: 10,
    color: "#94A3B8",
  },
  actions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    marginTop: 14,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
  },
  readButton: {
    paddingHorizontal: 10,
    paddingVertical: 7,
    marginRight: 8,
  },
  readButtonText: {
    color: "#2563EB",
    fontSize: 12,
    fontWeight: "600",
  },
  deleteButton: {
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  deleteButtonText: {
    color: "#DC2626",
    fontSize: 12,
    fontWeight: "600",
  },
  centerContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  loadingText: {
    marginTop: 10,
    color: "#64748B",
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#334155",
    textAlign: "center",
  },
  emptyMessage: {
    fontSize: 13,
    color: "#64748B",
    textAlign: "center",
    marginTop: 8,
  },
});