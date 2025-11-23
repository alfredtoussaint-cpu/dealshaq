import { useState, useEffect } from 'react';
import RetailerLayout from './RetailerLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { rshd } from '../../utils/api';
import { toast } from 'sonner';
import { Package, Edit, Trash2 } from 'lucide-react';

export default function RetailerInventory({ user, onLogout }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      const response = await rshd.myItems();
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this item?')) return;

    try {
      await rshd.delete(id);
      toast.success('Item deleted');
      loadItems();
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  return (
    <RetailerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Inventory Management
          </h1>
          <p className="text-gray-600 mt-1">View and manage your posted deals</p>
        </div>

        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Loading inventory...</p>
            </CardContent>
          </Card>
        ) : items.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No items posted yet</p>
              <p className="text-gray-400 text-sm mt-2">Start posting deals to reach more customers</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((item) => (
              <Card key={item.id} data-testid={`inventory-item-${item.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg line-clamp-1">{item.name}</CardTitle>
                      <Badge variant="outline" className="mt-2">{item.category}</Badge>
                    </div>
                    <div className="space-x-1">
                      <Badge className="bg-blue-500 text-xs">L{item.discount_level}</Badge>
                      <Badge className="bg-red-500 text-xs">{item.consumer_discount_percent}% OFF</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold text-emerald-600">${item.deal_price}</span>
                    <span className="text-sm text-gray-500 line-through">${item.regular_price}</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>Quantity: {item.quantity}</p>
                    <p>Status: {item.status}</p>
                    <p className="text-xs text-gray-500 mt-1">Posted: {new Date(item.posted_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      data-testid={`delete-item-${item.id}`}
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDelete(item.id)}
                      className="flex-1"
                    >
                      <Trash2 className="w-3 h-3 mr-1" />
                      Delete
                    </Button>
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
