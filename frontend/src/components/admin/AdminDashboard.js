import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { admin } from '../../utils/api';
import { 
  Users, Store, ShoppingBag, DollarSign, Heart, TrendingUp, 
  AlertTriangle, Bell, RefreshCw, Activity 
} from 'lucide-react';
import { toast } from 'sonner';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#84cc16'];

export default function AdminDashboard({ user, onLogout }) {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [activities, setActivities] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, analyticsRes, alertsRes, activityRes, itemsRes] = await Promise.all([
        admin.stats(),
        admin.analytics(),
        admin.alerts(),
        admin.activity(),
        admin.items(),
      ]);
      setStats(statsRes.data);
      setAnalytics(analyticsRes.data);
      setAlerts(alertsRes.data.alerts || []);
      setActivities(activityRes.data.activities || []);
      setItems(itemsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
    toast.success('Dashboard refreshed');
  };

  // Calculate discount level distribution
  const discountLevelStats = items.reduce((acc, item) => {
    const level = `Level ${item.discount_level}`;
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {});

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'order': return <ShoppingBag className="w-4 h-4 text-purple-500" />;
      case 'registration': return <Users className="w-4 h-4 text-emerald-500" />;
      case 'item': return <Store className="w-4 h-4 text-blue-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl p-8 text-white shadow-lg flex-1">
            <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
              System Overview
            </h2>
            <p className="text-purple-50 text-lg">Real-time analytics and monitoring</p>
          </div>
          <Button 
            variant="outline" 
            className="ml-4"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Loading dashboard...</p>
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
                      <p className="text-2xl font-bold text-gray-900">{stats.total_dacs}</p>
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
                      <p className="text-2xl font-bold text-gray-900">{stats.total_drlps}</p>
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
                      <p className="text-2xl font-bold text-gray-900">{stats.total_orders}</p>
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
                      <p className="text-2xl font-bold text-gray-900">{stats.total_items}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Charts Row */}
            {analytics && (
              <div className="grid lg:grid-cols-2 gap-6">
                {/* Orders Trend Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <TrendingUp className="w-5 h-5 text-blue-600" />
                      <span>Orders & Revenue (Last 30 Days)</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={analytics.orders_trend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fontSize: 10 }}
                          tickFormatter={(value) => value.slice(5)}
                        />
                        <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
                        <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
                        <Tooltip 
                          labelFormatter={(value) => `Date: ${value}`}
                          formatter={(value, name) => [
                            name === 'revenue' ? `$${value}` : value,
                            name === 'revenue' ? 'Revenue' : 'Orders'
                          ]}
                        />
                        <Legend />
                        <Line 
                          yAxisId="left"
                          type="monotone" 
                          dataKey="orders" 
                          stroke="#8b5cf6" 
                          strokeWidth={2}
                          dot={false}
                          name="Orders"
                        />
                        <Line 
                          yAxisId="right"
                          type="monotone" 
                          dataKey="revenue" 
                          stroke="#10b981" 
                          strokeWidth={2}
                          dot={false}
                          name="Revenue"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Category Breakdown Pie Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <ShoppingBag className="w-5 h-5 text-purple-600" />
                      <span>Items by Category</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={analytics.category_breakdown}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={80}
                          paddingAngle={2}
                          dataKey="count"
                          nameKey="category"
                          label={({ category, percent }) => 
                            percent > 0.05 ? `${category.slice(0, 10)}...` : ''
                          }
                          labelLine={false}
                        >
                          {analytics.category_breakdown.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value, name) => [value, name]} />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Top Retailers Bar Chart */}
            {analytics && analytics.top_retailers.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Store className="w-5 h-5 text-blue-600" />
                    <span>Top Retailers by Active Items</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={analytics.top_retailers} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis 
                        type="category" 
                        dataKey="name" 
                        tick={{ fontSize: 10 }} 
                        width={120}
                      />
                      <Tooltip />
                      <Bar dataKey="items" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Discount Model Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Discount Model Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-xs text-gray-600">Level 1</p>
                      <p className="text-lg font-bold text-blue-600">
                        {discountLevelStats['Level 1'] || 0}
                      </p>
                      <p className="text-xs text-gray-500">60% → 50%</p>
                    </div>
                    <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <p className="text-xs text-gray-600">Level 2</p>
                      <p className="text-lg font-bold text-purple-600">
                        {discountLevelStats['Level 2'] || 0}
                      </p>
                      <p className="text-xs text-gray-500">75% → 60%</p>
                    </div>
                    <div className="p-3 bg-pink-50 rounded-lg border border-pink-200">
                      <p className="text-xs text-gray-600">Level 3</p>
                      <p className="text-lg font-bold text-pink-600">
                        {discountLevelStats['Level 3'] || 0}
                      </p>
                      <p className="text-xs text-gray-500">90% → 75%</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Revenue & Charity + Alerts Row */}
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Revenue */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <DollarSign className="w-5 h-5 text-green-600" />
                    <span>Revenue</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">
                    ${stats.total_revenue.toFixed(2)}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Total platform revenue</p>
                </CardContent>
              </Card>

              {/* Charity */}
              <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-emerald-800">
                    <Heart className="w-5 h-5" />
                    <span>Charity Impact</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">DAC</span>
                    <span className="font-bold text-emerald-600">${stats.total_charity_dac.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">DRLP</span>
                    <span className="font-bold text-emerald-600">${stats.total_charity_drlp.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Round-up</span>
                    <span className="font-bold text-emerald-600">${stats.total_charity_roundup.toFixed(2)}</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between">
                    <span className="font-bold text-emerald-800">Total</span>
                    <span className="text-xl font-bold text-emerald-600">${stats.total_charity.toFixed(2)}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Alerts */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Bell className="w-5 h-5 text-orange-600" />
                    <span>System Alerts</span>
                    {alerts.length > 0 && (
                      <Badge className="ml-auto bg-orange-500">{alerts.length}</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {alerts.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center py-4">No active alerts</p>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {alerts.slice(0, 5).map((alert, index) => (
                        <div key={index} className="flex items-start space-x-2 text-sm">
                          <Badge className={`${getSeverityColor(alert.severity)} text-xs`}>
                            {alert.severity === 'critical' ? '!' : alert.severity === 'warning' ? '⚠' : 'i'}
                          </Badge>
                          <span className="text-gray-700 flex-1">{alert.message}</span>
                        </div>
                      ))}
                      {alerts.length > 5 && (
                        <p className="text-xs text-gray-400 text-center">
                          +{alerts.length - 5} more alerts
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-purple-600" />
                  <span>Recent Activity</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {activities.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No recent activity</p>
                ) : (
                  <div className="space-y-3">
                    {activities.slice(0, 10).map((activity, index) => (
                      <div key={index} className="flex items-center space-x-3 text-sm">
                        {getActivityIcon(activity.type)}
                        <span className="flex-1 text-gray-700">{activity.description}</span>
                        <span className="text-xs text-gray-400">
                          {activity.timestamp ? new Date(activity.timestamp).toLocaleString() : 'N/A'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </AdminLayout>
  );
}
