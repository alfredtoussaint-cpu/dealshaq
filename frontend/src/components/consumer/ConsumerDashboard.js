import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { rshd, notifications as notificationsApi } from '../../utils/api';
import { useNavigate } from 'react-router-dom';
import { ShoppingBag, Heart, Bell, TrendingDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function ConsumerDashboard({ user, onLogout }) {
  const [featuredDeals, setFeaturedDeals] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [dealsRes, notifsRes] = await Promise.all([
        rshd.list(),
        notificationsApi.list(),
      ]);
      setFeaturedDeals(dealsRes.data.slice(0, 6));
      setNotifications(notifsRes.data.filter(n => !n.read).slice(0, 5));
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-8 text-white shadow-lg">
          <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            Welcome back, {user.name}! 👋
          </h2>
          <p className="text-emerald-50 text-lg">Local retailers are posting deals that match your favorites</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              data-testid="dashboard-browse-btn"
              onClick={() => navigate('/consumer/browse')}
              className="bg-white text-emerald-600 hover:bg-emerald-50"
            >
              <ShoppingBag className="w-4 h-4 mr-2" />
              Browse Deals
            </Button>
            <Button
              data-testid="dashboard-favorites-btn"
              onClick={() => navigate('/consumer/favorites')}
              variant="outline"
              className="border-white text-white hover:bg-white/10"
            >
              <Heart className="w-4 h-4 mr-2" />
              My Favorites
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-emerald-100 p-3 rounded-lg">
                  <TrendingDown className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active Deals</p>
                  <p className="text-2xl font-bold text-gray-900" data-testid="active-deals-count">{featuredDeals.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Bell className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">New Alerts</p>
                  <p className="text-2xl font-bold text-gray-900" data-testid="new-alerts-count">{notifications.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <Heart className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Charity Impact</p>
                  <p className="text-2xl font-bold text-gray-900">$0.00</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Featured Deals */}
        <Card>
          <CardHeader>
            <CardTitle>Featured Deals</CardTitle>
            <CardDescription>Hot deals from your local retailers</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading deals...</p>
            ) : featuredDeals.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No deals available yet</p>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {featuredDeals.map((deal) => (
                  <div
                    key={deal.id}
                    data-testid={`deal-card-${deal.id}`}
                    className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => navigate('/consumer/browse')}
                  >
                    <div className="aspect-video bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center">
                      {deal.image_url ? (
                        <img src={deal.image_url} alt={deal.name} className="w-full h-full object-cover" />
                      ) : (
                        <ShoppingBag className="w-16 h-16 text-emerald-400" />
                      )}
                    </div>
                    <div className="p-4">
                      <Badge className="mb-2 bg-red-500">{deal.consumer_discount_percent}% OFF</Badge>
                      <h3 className="font-bold text-gray-900 mb-1">{deal.name}</h3>
                      <p className="text-sm text-gray-600 mb-2">{deal.drlp_name}</p>
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-bold text-emerald-600">${deal.deal_price}</span>
                        <span className="text-sm text-gray-500 line-through">${deal.regular_price}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Notifications */}
        {notifications.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Notifications</CardTitle>
              <CardDescription>New deals matching your favorites</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    data-testid={`notification-${notif.id}`}
                    className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg"
                  >
                    <Bell className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{notif.message}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(notif.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                onClick={() => navigate('/consumer/notifications')}
                variant="outline"
                className="w-full mt-4"
                data-testid="view-all-notifications-btn"
              >
                View All Notifications
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </ConsumerLayout>
  );
}
