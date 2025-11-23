import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { notifications as notificationsApi, rshd } from '../../utils/api';
import { Bell, BellOff, Check } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';

export default function ConsumerNotifications({ user, onLogout }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await notificationsApi.list();
      setNotifications(response.data);
    } catch (error) {
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications(
        notifications.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    } catch (error) {
      toast.error('Failed to mark as read');
    }
  };

  const markAllAsRead = async () => {
    try {
      const unread = notifications.filter((n) => !n.read);
      await Promise.all(unread.map((n) => notificationsApi.markRead(n.id)));
      setNotifications(notifications.map((n) => ({ ...n, read: true })));
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
              Notifications
            </h1>
            <p className="text-gray-600 mt-1">
              {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up!'}
            </p>
          </div>
          {unreadCount > 0 && (
            <Button
              data-testid="mark-all-read-btn"
              onClick={markAllAsRead}
              variant="outline"
            >
              <Check className="w-4 h-4 mr-2" />
              Mark All Read
            </Button>
          )}
        </div>

        {/* Notifications List */}
        <Card>
          <CardHeader>
            <CardTitle>Deal Alerts</CardTitle>
            <CardDescription>New deals matching your favorite categories</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading notifications...</p>
            ) : notifications.length === 0 ? (
              <div className="text-center py-12">
                <BellOff className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No notifications yet</p>
                <p className="text-gray-400 text-sm mt-2">Add favorites to start receiving deal alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    data-testid={`notification-${notif.id}`}
                    className={`flex items-start space-x-4 p-4 rounded-lg border transition-all ${
                      notif.read
                        ? 'bg-gray-50 border-gray-200'
                        : 'bg-blue-50 border-blue-200 shadow-sm'
                    }`}
                  >
                    <div
                      className={`p-2 rounded-lg ${
                        notif.read ? 'bg-gray-200' : 'bg-blue-100'
                      }`}
                    >
                      <Bell
                        className={`w-5 h-5 ${
                          notif.read ? 'text-gray-500' : 'text-blue-600'
                        }`}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-1">
                        <p
                          className={`text-sm ${
                            notif.read ? 'text-gray-700' : 'text-gray-900 font-medium'
                          }`}
                          data-testid={`notification-message-${notif.id}`}
                        >
                          {notif.message}
                        </p>
                        {!notif.read && (
                          <Badge className="ml-2 bg-blue-500">New</Badge>
                        )}
                      </div>
                      <p className="text-xs text-gray-500">
                        {new Date(notif.created_at).toLocaleString()}
                      </p>
                      {!notif.read && (
                        <Button
                          data-testid={`mark-read-${notif.id}`}
                          size="sm"
                          variant="ghost"
                          onClick={() => markAsRead(notif.id)}
                          className="mt-2 text-blue-600 hover:text-blue-700"
                        >
                          <Check className="w-3 h-3 mr-1" />
                          Mark as read
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <div className="bg-emerald-100 p-2 rounded-lg">
                <Bell className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h4 className="font-bold text-gray-900 mb-1">Stay Updated</h4>
                <p className="text-sm text-gray-600">
                  Get instant notifications when retailers post deals that match your favorite categories.
                  Never miss out on great savings again!
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ConsumerLayout>
  );
}
