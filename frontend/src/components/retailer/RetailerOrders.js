import { useState, useEffect } from 'react';
import RetailerLayout from './RetailerLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { orders as ordersApi } from '../../utils/api';
import { toast } from 'sonner';
import { Receipt, Truck, MapPin } from 'lucide-react';

export default function RetailerOrders({ user, onLogout }) {
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

  return (
    <RetailerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Orders
          </h1>
          <p className="text-gray-600 mt-1">Manage customer orders and fulfillment</p>
        </div>

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
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} data-testid={`retailer-order-${order.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">Order #{order.id.slice(0, 8)}</CardTitle>
                      <p className="text-sm text-gray-500">{order.dac_name}</p>
                    </div>
                    <Badge className="bg-blue-500">{order.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm">
                    {order.delivery_method === 'delivery' ? (
                      <Truck className="w-4 h-4 text-purple-600" />
                    ) : (
                      <MapPin className="w-4 h-4 text-emerald-600" />
                    )}
                    <span className="capitalize">{order.delivery_method}</span>
                    {order.delivery_method === 'pickup' && order.pickup_time && (
                      <span className="text-gray-500">• {new Date(order.pickup_time).toLocaleString()}</span>
                    )}
                  </div>
                  <div className="space-y-1 text-sm">
                    {order.items.map((item, idx) => (
                      <div key={idx} className="flex justify-between">
                        <span className="text-gray-600">{item.name} x{item.quantity}</span>
                        <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="border-t pt-2 flex justify-between font-bold">
                    <span>Total</span>
                    <span>${order.total.toFixed(2)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </RetailerLayout>
  );
}
