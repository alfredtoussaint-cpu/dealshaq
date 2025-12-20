/**
 * React Hook for WebSocket Notifications
 * 
 * Provides easy integration of real-time notifications in React components.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import wsService from './websocket';

/**
 * Hook to manage WebSocket connection and notifications
 * @param {string} token - JWT authentication token
 * @returns {object} - WebSocket state and methods
 */
export function useWebSocket(token) {
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [lastNotification, setLastNotification] = useState(null);
  const tokenRef = useRef(token);

  // Update token ref when it changes
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  // Connect to WebSocket when token is available
  useEffect(() => {
    if (!token) {
      wsService.disconnect();
      return;
    }

    // Connection status handler
    const handleConnection = (data) => {
      setIsConnected(data.status === 'connected');
    };

    // New RSHD notification handler
    const handleNewRshd = (data) => {
      console.log('New RSHD notification received:', data);
      setLastNotification(data);
      setNotifications(prev => [data, ...prev].slice(0, 50)); // Keep last 50
    };

    // Subscribe to events
    const unsubConnection = wsService.on('connection', handleConnection);
    const unsubRshd = wsService.on('new_rshd', handleNewRshd);
    const unsubConnected = wsService.on('connected', () => setIsConnected(true));

    // Connect
    wsService.connect(token);

    // Cleanup on unmount
    return () => {
      unsubConnection();
      unsubRshd();
      unsubConnected();
    };
  }, [token]);

  // Mark notification as read
  const markAsRead = useCallback((notificationId) => {
    wsService.markAsRead(notificationId);
    setNotifications(prev => 
      prev.map(n => 
        n.data?.rshd_id === notificationId || n.notification_id === notificationId
          ? { ...n, is_read: true }
          : n
      )
    );
  }, []);

  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setLastNotification(null);
  }, []);

  // Dismiss a specific notification
  const dismissNotification = useCallback((notificationId) => {
    setNotifications(prev => prev.filter(n => 
      n.data?.rshd_id !== notificationId && n.notification_id !== notificationId
    ));
  }, []);

  return {
    isConnected,
    notifications,
    lastNotification,
    unreadCount: notifications.filter(n => !n.is_read).length,
    markAsRead,
    clearNotifications,
    dismissNotification,
    getStatus: () => wsService.getStatus(),
  };
}

/**
 * Hook for notification toast display
 * Auto-shows toast when new notification arrives
 */
export function useNotificationToast(lastNotification, showToast) {
  useEffect(() => {
    if (lastNotification && lastNotification.type === 'new_rshd') {
      const data = lastNotification.data || {};
      showToast?.({
        title: lastNotification.title || '🔥 New Deal!',
        description: lastNotification.message || `${data.item_name} - ${data.discount_percent}% OFF`,
        action: data.rshd_id ? {
          label: 'View',
          onClick: () => window.location.href = `/consumer/radar`
        } : undefined
      });
    }
  }, [lastNotification, showToast]);
}

export default useWebSocket;
