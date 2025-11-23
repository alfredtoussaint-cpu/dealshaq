import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { admin } from '../../utils/api';
import { Users, Store, ShoppingBag, DollarSign, Heart, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminDashboard({ user, onLogout }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await admin.stats();
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl p-8 text-white shadow-lg">
          <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            System Overview
          </h2>
          <p className="text-purple-50 text-lg">Real-time analytics and monitoring</p>
        </div>

        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Loading statistics...</p>
            </CardContent>
          </Card>
        ) : stats ? (
          <>
            {/* Main Stats */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-emerald-100 p-3 rounded-lg">
                      <Users className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total DACs</p>
                      <p className="text-2xl font-bold text-gray-900" data-testid="total-dacs">{stats.total_dacs}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-blue-100 p-3 rounded-lg">
                      <Store className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total DRLPs</p>
                      <p className="text-2xl font-bold text-gray-900" data-testid="total-drlps">{stats.total_drlps}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-purple-100 p-3 rounded-lg">
                      <ShoppingBag className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Orders</p>
                      <p className="text-2xl font-bold text-gray-900" data-testid="total-orders">{stats.total_orders}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-orange-100 p-3 rounded-lg">
                      <TrendingUp className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Active Items</p>
                      <p className="text-2xl font-bold text-gray-900" data-testid="total-items">{stats.total_items}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Revenue & Charity */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <DollarSign className="w-5 h-5 text-green-600" />
                    <span>Revenue Overview</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Revenue</span>
                      <span className="text-2xl font-bold text-green-600" data-testid="total-revenue">
                        ${stats.total_revenue.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-emerald-800">
                    <Heart className="w-5 h-5" />
                    <span>Charity Impact</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">DAC Contributions</span>
                    <span className="font-bold text-emerald-600" data-testid="charity-dac">
                      ${stats.total_charity_dac.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">DRLP Contributions</span>
                    <span className="font-bold text-emerald-600" data-testid="charity-drlp">
                      ${stats.total_charity_drlp.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Round-up Donations</span>
                    <span className="font-bold text-emerald-600" data-testid="charity-roundup">
                      ${stats.total_charity_roundup.toFixed(2)}
                    </span>
                  </div>
                  <div className="border-t pt-3 flex justify-between">
                    <span className="font-bold text-emerald-800">Total Charity</span>
                    <span className="text-2xl font-bold text-emerald-600" data-testid="total-charity">
                      ${stats.total_charity.toFixed(2)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        ) : null}
      </div>
    </AdminLayout>
  );
}
