/**
 * Real-time Notification Bell Component
 * 
 * Shows notification count and dropdown with recent notifications.
 */

import { useState, useEffect, useRef } from 'react';
import { Bell, X, ExternalLink, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useWebSocket } from '../../utils/useWebSocket';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

export default function NotificationBell({ token }) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  const { 
    isConnected, 
    notifications, 
    lastNotification, 
    unreadCount,
    markAsRead,
    dismissNotification,
    clearNotifications 
  } = useWebSocket(token);

  // Show toast for new notifications
  useEffect(() => {
    if (lastNotification && lastNotification.type === 'new_rshd') {
      toast.success(lastNotification.title, {
        description: lastNotification.message,
        action: {
          label: 'View Deals',
          onClick: () => navigate('/consumer/radar')
        },
        duration: 8000,
      });
    }
  }, [lastNotification, navigate]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getDiscountColor = (level) => {
    switch (level) {
      case 3: return 'bg-red-500';
      case 2: return 'bg-amber-500';
      default: return 'bg-green-500';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <Button
        variant="ghost"
        size="icon"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell className={`w-5 h-5 ${isConnected ? 'text-gray-700' : 'text-gray-400'}`} />
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
        
        {/* Connection Status Dot */}
        <span 
          className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-gray-400'
          }`}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />
      </Button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-lg shadow-xl border z-50 max-h-[70vh] overflow-hidden">
          {/* Header */}
          <div className="p-3 border-b bg-gray-50 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              <p className="text-xs text-gray-500">
                {isConnected ? '🟢 Live updates active' : '⚪ Reconnecting...'}
              </p>
            </div>
            {notifications.length > 0 && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={clearNotifications}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear all
              </Button>
            )}
          </div>

          {/* Notification List */}
          <div className="overflow-y-auto max-h-96">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No notifications yet</p>
                <p className="text-sm mt-1">New deals will appear here in real-time</p>
              </div>
            ) : (
              notifications.map((notification, index) => (
                <div
                  key={notification.data?.rshd_id || index}
                  className={`p-3 border-b hover:bg-gray-50 transition-colors ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Discount Badge */}
                    <div className={`${getDiscountColor(notification.data?.discount_level)} text-white text-xs font-bold px-2 py-1 rounded`}>
                      {notification.data?.discount_percent || 50}%
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 text-sm truncate">
                        {notification.data?.item_name || 'New Deal'}
                      </p>
                      <p className="text-xs text-gray-600 truncate">
                        {notification.data?.drlp_name}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm font-bold text-emerald-600">
                          ${notification.data?.deal_price?.toFixed(2)}
                        </span>
                        <span className="text-xs text-gray-400 line-through">
                          ${notification.data?.regular_price?.toFixed(2)}
                        </span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTime(notification.timestamp)}
                        </span>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="w-6 h-6"
                        onClick={() => dismissNotification(notification.data?.rshd_id)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-2 border-t bg-gray-50">
              <Button 
                variant="ghost" 
                className="w-full text-sm text-emerald-600 hover:text-emerald-700"
                onClick={() => {
                  navigate('/consumer/radar');
                  setIsOpen(false);
                }}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View All Deals in Radar
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
