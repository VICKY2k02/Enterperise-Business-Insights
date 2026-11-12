
import * as SecureStore from "expo-secure-store";
import type { Notification } from "./notificationService";

const WS_BASE_URL = "ws://192.168.1.7:8000";
const TOKEN_KEY = "enterprise_business_insights_access_token";

interface WebSocketNotification extends Omit<Notification, "notification_type"> {
    type: Notification["notification_type"];
}

export interface NewNotificationEvent {
    event: "new_notification";
    notification: WebSocketNotification;
}

type NotificationCallback = (
    notification: Notification,
) => void;

type ConnectionCallback = (connected: boolean) => void;

let socket: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempts = 0;
let shouldReconnect = false;
let connectionId = 0;

let notificationCallback: NotificationCallback | null = null;
let connectionCallback: ConnectionCallback | null = null;

const MAX_RECONNECT_DELAY = 30000;

function clearReconnectTimer(): void {
    if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
}

function notifyConnectionStatus(connected: boolean): void {
    connectionCallback?.(connected);
}

function scheduleReconnect(): void {
    if (!shouldReconnect || reconnectTimer !== null) {
        return;
    }

    const delay = Math.min(
        1000 * 2 ** reconnectAttempts,
        MAX_RECONNECT_DELAY,
    );

    reconnectAttempts += 1;

    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        void connectNotificationSocket();
    }, delay);
}

async function connectNotificationSocket(): Promise<void> {
    if (!shouldReconnect || socket !== null) {
        return;
    }

    const currentConnectionId = connectionId;

    try {
        const token = await SecureStore.getItemAsync(TOKEN_KEY);

        if (
            !shouldReconnect ||
            currentConnectionId !== connectionId
        ) {
            return;
        }

        if (!token) {
            shouldReconnect = false;
            notifyConnectionStatus(false);
            return;
        }

        const newSocket = new WebSocket(
            `${WS_BASE_URL}/ws/notifications?token=${encodeURIComponent(token)}`,
        );

        socket = newSocket;

        newSocket.onopen = () => {
            if (
                socket !== newSocket ||
                currentConnectionId !== connectionId
            ) {
                newSocket.close();
                return;
            }

            reconnectAttempts = 0;
            notifyConnectionStatus(true);
        };

        newSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(
                    String(event.data),
                ) as NewNotificationEvent;

                if (
                    data.event === "new_notification" &&
                    data.notification
                ) {
                    const { type, ...notificationData } = data.notification;

                    notificationCallback?.({
                        ...notificationData,
                        notification_type: type,
                    });
                }
            } catch (error) {
                console.error(
                    "Unable to process notification:",
                    error,
                );
            }
        };

        newSocket.onerror = () => {
            notifyConnectionStatus(false);
        };

        newSocket.onclose = () => {
            if (socket !== newSocket) {
                return;
            }

            socket = null;
            notifyConnectionStatus(false);

            scheduleReconnect();
        };
    } catch (error) {
        console.error(
            "WebSocket connection failed:",
            error,
        );

        notifyConnectionStatus(false);
        scheduleReconnect();
    }
}

export function startNotificationSocket(
    onNotification: NotificationCallback,
    onConnectionChange?: ConnectionCallback,
): void {
    notificationCallback = onNotification;
    connectionCallback = onConnectionChange ?? null;

    if (shouldReconnect) {
        return;
    }

    shouldReconnect = true;
    reconnectAttempts = 0;
    connectionId += 1;

    void connectNotificationSocket();
}

export function stopNotificationSocket(): void {
    shouldReconnect = false;
    connectionId += 1;

    clearReconnectTimer();

    const currentSocket = socket;
    socket = null;

    if (currentSocket !== null) {
        currentSocket.onclose = null;
        currentSocket.onmessage = null;
        currentSocket.onerror = null;
        currentSocket.onopen = null;
        currentSocket.close();
    }

    notificationCallback = null;
    connectionCallback = null;

    reconnectAttempts = 0;
}
