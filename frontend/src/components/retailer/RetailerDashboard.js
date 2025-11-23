import { useState, useEffect } from 'react';
import RetailerLayout from './RetailerLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { rshd, orders as ordersApi } from '../../utils/api';
import { useNavigate } from 'react-router-dom';
import { Package, ShoppingBag, DollarSign, Plus } from 'lucide-react';

export default function RetailerDashboard({ user, onLogout }) {
  const [stats, setStats] = useState({ items: 0, orders: 0, revenue: 0 });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [itemsRes, ordersRes] = await Promise.all([
        rshd.myItems(),
        ordersApi.list(),
      ]);
      const revenue = ordersRes.data.reduce((sum, order) => sum + order.total, 0);
      setStats({
        items: itemsRes.data.length,
        orders: ordersRes.data.length,
        revenue,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <RetailerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl p-8 text-white shadow-lg">
          <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            Welcome, {user.name}!
          </h2>
          <p className="text-blue-50 text-lg">Manage your deals and reach more customers</p>
          <Button
            data-testid="post-deal-btn"
            onClick={() => navigate('/retailer/post-item')}
            className="mt-6 bg-white text-blue-600 hover:bg-blue-50"
          >
            <Plus className="w-4 h-4 mr-2" />
            Post New Deal
          </Button>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Package className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active Deals</p>
                  <p className="text-2xl font-bold text-gray-900" data-testid="active-items-count">{stats.items}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-green-100 p-3 rounded-lg">
                  <ShoppingBag className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Orders</p>
                  <p className="text-2xl font-bold text-gray-900" data-testid="total-orders-count">{stats.orders}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <DollarSign className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Revenue</p>
                  <p className="text-2xl font-bold text-gray-900" data-testid="total-revenue">${stats.revenue.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </RetailerLayout>
  );
}
