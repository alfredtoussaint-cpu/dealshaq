import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { orders as ordersApi } from '../../utils/api';
import { Badge } from '@/components/ui/badge';
import { Receipt, Package, Truck, MapPin } from 'lucide-react';
import { toast } from 'sonner';

export default function ConsumerOrders({ user, onLogout }) {
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
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-500',
      confirmed: 'bg-blue-500',
      preparing: 'bg-purple-500',
      ready: 'bg-green-500',
      completed: 'bg-gray-500',
    };
    return colors[status] || 'bg-gray-500';
  };

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            My Orders
          </h1>
          <p className="text-gray-600 mt-1">View your order history and track deliveries</p>
        </div>

        {/* Orders List */}
        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Loading orders...</p>
            </CardContent>
          </Card>
        ) : orders.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Receipt className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No orders yet</p>
              <p className="text-gray-400 text-sm mt-2">Your order history will appear here</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} data-testid={`order-${order.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">Order #{order.id.slice(0, 8)}</CardTitle>
                      <CardDescription>{new Date(order.created_at).toLocaleString()}</CardDescription>
                    </div>
                    <Badge className={getStatusColor(order.status)} data-testid={`order-status-${order.id}`}>
                      {order.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Retailer Info */}
                  <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <Package className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{order.drlp_name}</p>
                      <p className="text-sm text-gray-500">Retailer</p>
                    </div>
                  </div>

                  {/* Delivery Info */}
                  <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className={`p-2 rounded-lg ${order.delivery_method === 'delivery' ? 'bg-purple-100' : 'bg-emerald-100'}`}>
                      {order.delivery_method === 'delivery' ? (
                        <Truck className={`w-5 h-5 ${order.delivery_method === 'delivery' ? 'text-purple-600' : 'text-emerald-600'}`} />
                      ) : (
                        <MapPin className={`w-5 h-5 ${order.delivery_method === 'delivery' ? 'text-purple-600' : 'text-emerald-600'}`} />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 capitalize">{order.delivery_method}</p>
                      {order.delivery_method === 'delivery' ? (
                        <p className="text-sm text-gray-500">{order.delivery_address}</p>
                      ) : (
                        <p className="text-sm text-gray-500">Pickup at {new Date(order.pickup_time).toLocaleString()}</p>
                      )}
                    </div>
                  </div>

                  {/* Items */}
                  <div className="space-y-2">
                    <p className="font-medium text-sm text-gray-700">Items</p>
                    {order.items.map((item, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-gray-600">
                          {item.name} x{item.quantity}
                        </span>
                        <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  {/* Totals */}
                  <div className="border-t pt-3 space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Subtotal</span>
                      <span>${order.subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Tax</span>
                      <span>${order.tax.toFixed(2)}</span>
                    </div>
                    {order.delivery_fee > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Delivery Fee</span>
                        <span>${order.delivery_fee.toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-emerald-600">
                      <span>Charity Contributions</span>
                      <span>${(order.charity_dac + order.charity_drlp + order.charity_roundup).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold pt-2 border-t">
                      <span>Total</span>
                      <span data-testid={`order-total-${order.id}`}>${order.total.toFixed(2)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Charity Impact Summary */}
        {orders.length > 0 && (
          <Card className="bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200">
            <CardHeader>
              <CardTitle className="text-emerald-800">Your Charity Impact</CardTitle>
              <CardDescription>Total contributions through your orders</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-600">
                ${orders
                  .reduce((sum, order) => sum + order.charity_dac + order.charity_drlp + order.charity_roundup, 0)
                  .toFixed(2)}
              </div>
              <p className="text-sm text-gray-600 mt-2">Thank you for making a difference!</p>
            </CardContent>
          </Card>
        )}
      </div>
    </ConsumerLayout>
  );
}
