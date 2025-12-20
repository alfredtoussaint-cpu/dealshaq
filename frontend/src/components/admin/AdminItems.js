import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { admin } from '../../utils/api';
import { toast } from 'sonner';
import { 
  Package, Search, Eye, Ban, CheckCircle, Store, 
  DollarSign, Calendar, Tag, AlertTriangle 
} from 'lucide-react';

const CATEGORIES = [
  "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
  "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
  "Snacks & Candy", "Frozen Foods", "Beverages",
  "Deli & Prepared Foods", "Breakfast & Cereal",
  "Pasta, Rice & Grains", "Oils, Sauces & Spices",
  "Baby & Kids", "Health & Nutrition", "Household Essentials",
  "Personal Care", "Pet Supplies", "Miscellaneous"
];

export default function AdminItems({ user, onLogout }) {
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadItems();
  }, []);

  useEffect(() => {
    filterItems();
  }, [items, searchTerm, categoryFilter, statusFilter]);

  const loadItems = async () => {
    try {
      const response = await admin.items();
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  const filterItems = () => {
    let filtered = [...items];
    
    // Filter by category
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(i => i.category === categoryFilter);
    }
    
    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(i => i.status === statusFilter);
    }
    
    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(i => 
        i.name?.toLowerCase().includes(term) ||
        i.drlp_name?.toLowerCase().includes(term)
      );
    }
    
    setFilteredItems(filtered);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'available':
        return <Badge className="bg-green-500">Available</Badge>;
      case 'unavailable':
        return <Badge className="bg-gray-500">Unavailable</Badge>;
      case 'admin_removed':
        return <Badge className="bg-red-500">Admin Removed</Badge>;
      default:
        return <Badge className="bg-gray-400">{status}</Badge>;
    }
  };

  const getDiscountBadge = (level) => {
    switch (level) {
      case 1: return <Badge className="bg-yellow-500">50% OFF</Badge>;
      case 2: return <Badge className="bg-orange-500">60% OFF</Badge>;
      case 3: return <Badge className="bg-red-500">75% OFF</Badge>;
      default: return <Badge className="bg-gray-500">DEAL</Badge>;
    }
  };

  const handleViewDetails = (item) => {
    setSelectedItem(item);
    setShowDetailsModal(true);
  };

  const handleToggleStatus = async (itemId, currentStatus) => {
    const newStatus = currentStatus === 'available' ? 'admin_removed' : 'available';
    const action = newStatus === 'admin_removed' ? 'remove' : 'restore';
    
    if (!window.confirm(`Are you sure you want to ${action} this item?`)) {
      return;
    }
    
    setActionLoading(true);
    try {
      await admin.updateItemStatus(itemId, newStatus);
      toast.success(`Item ${action}d successfully`);
      
      // Update local state
      setItems(items.map(i => 
        i.id === itemId ? { ...i, status: newStatus } : i
      ));
      
      if (selectedItem && selectedItem.id === itemId) {
        setSelectedItem({ ...selectedItem, status: newStatus });
      }
    } catch (error) {
      toast.error(`Failed to ${action} item`);
    } finally {
      setActionLoading(false);
    }
  };

  const isExpiringSoon = (expiryDate) => {
    if (!expiryDate) return false;
    try {
      const expiry = new Date(expiryDate);
      const now = new Date();
      const daysUntil = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));
      return daysUntil <= 2 && daysUntil >= 0;
    } catch {
      return false;
    }
  };

  const stats = {
    total: items.length,
    available: items.filter(i => i.status === 'available').length,
    removed: items.filter(i => i.status === 'admin_removed').length,
    expiringSoon: items.filter(i => isExpiringSoon(i.expiry_date)).length,
  };

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Item Management
          </h1>
          <p className="text-gray-600 mt-1">View and manage all RSHD items</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                <p className="text-sm text-gray-500">Total Items</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{stats.available}</p>
                <p className="text-sm text-gray-500">Available</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{stats.removed}</p>
                <p className="text-sm text-gray-500">Admin Removed</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">{stats.expiringSoon}</p>
                <p className="text-sm text-gray-500">Expiring Soon</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search by item name or retailer..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-full lg:w-48">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {CATEGORIES.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full lg:w-40">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="available">Available</SelectItem>
                  <SelectItem value="unavailable">Unavailable</SelectItem>
                  <SelectItem value="admin_removed">Admin Removed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Showing {filteredItems.length} of {items.length} items
            </p>
          </CardContent>
        </Card>

        {/* Items List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Package className="w-5 h-5 text-purple-600" />
              <span>RSHD Items</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading items...</p>
            ) : filteredItems.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No items found</p>
            ) : (
              <div className="space-y-3">
                {filteredItems.map((item) => (
                  <div
                    key={item.id}
                    className={`p-4 rounded-lg border transition hover:shadow-md ${
                      item.status === 'admin_removed' 
                        ? 'bg-red-50 border-red-200' 
                        : isExpiringSoon(item.expiry_date)
                        ? 'bg-orange-50 border-orange-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="font-medium text-gray-900">{item.name}</h4>
                          {getDiscountBadge(item.discount_level)}
                          {isExpiringSoon(item.expiry_date) && (
                            <Badge className="bg-orange-500 flex items-center">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              Expiring Soon
                            </Badge>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Store className="w-3 h-3 mr-1" />
                            {item.drlp_name}
                          </span>
                          <span className="flex items-center">
                            <Tag className="w-3 h-3 mr-1" />
                            {item.category}
                          </span>
                          <span className="flex items-center">
                            <DollarSign className="w-3 h-3 mr-1" />
                            <span className="line-through text-gray-400 mr-1">${item.regular_price?.toFixed(2)}</span>
                            <span className="text-emerald-600 font-medium">${item.deal_price?.toFixed(2)}</span>
                          </span>
                          <span className="flex items-center">
                            <Package className="w-3 h-3 mr-1" />
                            Qty: {item.quantity}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {getStatusBadge(item.status)}
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleViewDetails(item)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleToggleStatus(item.id, item.status)}
                          className={item.status === 'available' ? 'text-red-600' : 'text-green-600'}
                          disabled={actionLoading}
                        >
                          {item.status === 'available' ? (
                            <Ban className="w-4 h-4" />
                          ) : (
                            <CheckCircle className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Item Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Item Details</DialogTitle>
          </DialogHeader>
          {selectedItem && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">{selectedItem.name}</h3>
                {getStatusBadge(selectedItem.status)}
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Retailer</p>
                  <p className="font-medium">{selectedItem.drlp_name}</p>
                </div>
                <div>
                  <p className="text-gray-500">Category</p>
                  <p className="font-medium">{selectedItem.category}</p>
                </div>
                <div>
                  <p className="text-gray-500">Regular Price</p>
                  <p className="font-medium">${selectedItem.regular_price?.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Deal Price</p>
                  <p className="font-medium text-emerald-600">${selectedItem.deal_price?.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Discount Level</p>
                  <div>{getDiscountBadge(selectedItem.discount_level)}</div>
                </div>
                <div>
                  <p className="text-gray-500">Quantity</p>
                  <p className="font-medium">{selectedItem.quantity}</p>
                </div>
                <div>
                  <p className="text-gray-500">Barcode</p>
                  <p className="font-medium">{selectedItem.barcode || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Expiry Date</p>
                  <p className={`font-medium ${isExpiringSoon(selectedItem.expiry_date) ? 'text-orange-600' : ''}`}>
                    {selectedItem.expiry_date 
                      ? new Date(selectedItem.expiry_date).toLocaleDateString()
                      : 'N/A'}
                  </p>
                </div>
                <div className="col-span-2">
                  <p className="text-gray-500">Posted At</p>
                  <p className="font-medium">
                    {selectedItem.posted_at 
                      ? new Date(selectedItem.posted_at).toLocaleString()
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {selectedItem.description && (
                <div>
                  <p className="text-gray-500 text-sm">Description</p>
                  <p className="text-sm">{selectedItem.description}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            {selectedItem && (
              <Button
                variant={selectedItem.status === 'available' ? 'destructive' : 'default'}
                onClick={() => handleToggleStatus(selectedItem.id, selectedItem.status)}
                disabled={actionLoading}
              >
                {selectedItem.status === 'available' ? (
                  <>
                    <Ban className="w-4 h-4 mr-2" />
                    Remove Item
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Restore Item
                  </>
                )}
              </Button>
            )}
            <Button variant="outline" onClick={() => setShowDetailsModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminLayout>
  );
}
