import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { orders as ordersApi } from '../../utils/api';
import { toast } from 'sonner';
import { Receipt, TrendingUp, Heart } from 'lucide-react';

export default function AdminTransactions({ user, onLogout }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await ordersApi.list();
      setOrders(response.data);
    } catch (error) {
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const totalRevenue = orders.reduce((sum, order) => sum + order.total, 0);
  const totalCharity = orders.reduce(
    (sum, order) => sum + order.charity_dac + order.charity_drlp + order.charity_roundup,
    0
  );

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Transactions
          </h1>
          <p className="text-gray-600 mt-1">View all orders and financial data</p>
        </div>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Receipt className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Transactions</p>
                  <p className="text-2xl font-bold text-gray-900">{orders.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-green-100 p-3 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">${totalRevenue.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-emerald-100 p-3 rounded-lg">
                  <Heart className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Charity Raised</p>
                  <p className="text-2xl font-bold text-gray-900">${totalCharity.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Transactions List */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading transactions...</p>
            ) : orders.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No transactions yet</p>
            ) : (
              <div className="space-y-3">
                {orders.map((order) => (
                  <div
                    key={order.id}
                    data-testid={`transaction-${order.id}`}
                    className="p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-gray-900">Order #{order.id.slice(0, 8)}</p>
                        <p className="text-sm text-gray-500">
                          {order.dac_name} → {order.drlp_name}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-gray-900">${order.total.toFixed(2)}</p>
                        <Badge className="mt-1 bg-blue-500">{order.status}</Badge>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 mt-3">
                      <div>
                        <span className="text-gray-500">Subtotal:</span> ${order.subtotal.toFixed(2)}
                      </div>
                      <div>
                        <span className="text-gray-500">Tax:</span> ${order.tax.toFixed(2)}
                      </div>
                      <div>
                        <span className="text-gray-500">Delivery:</span> ${order.delivery_fee.toFixed(2)}
                      </div>
                      <div className="text-emerald-600">
                        <span className="text-gray-500">Charity:</span> $
                        {(order.charity_dac + order.charity_drlp + order.charity_roundup).toFixed(2)}
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                      {new Date(order.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
