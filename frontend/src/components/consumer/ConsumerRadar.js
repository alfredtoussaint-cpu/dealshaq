import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Radar, Store, Clock, Tag, ShoppingCart, RefreshCw, MapPin, AlertCircle, Loader2, Percent } from 'lucide-react';
import { toast } from 'sonner';
import { rshd, dacRetailers } from '../../utils/api';

export default function ConsumerRadar({ user, onLogout }) {
  const [items, setItems] = useState([]);
  const [retailers, setRetailers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [hasDeliveryLocation, setHasDeliveryLocation] = useState(false);

  const categories = [
    'All Categories', 'Fruits', 'Vegetables', 'Dairy & Eggs', 'Meat & Poultry',
    'Seafood', 'Bakery', 'Deli', 'Frozen Foods', 'Beverages',
    'Snacks & Candy', 'Breakfast & Cereal', 'Canned & Jarred Goods',
    'Pasta, Rice & Grains', 'Oils, Sauces & Spices', 'Baking Supplies',
    'International Foods', 'Baby & Kids', 'Health & Wellness',
    'Household & Cleaning', 'Personal Care', 'Pet Supplies', 'Miscellaneous'
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Get DACDRLP-List to check if user has retailers
      const retailersResponse = await dacRetailers.list();
      const retailerData = retailersResponse.data;
      const activeRetailers = (retailerData.retailers || []).filter(r => !r.manually_removed);
      setRetailers(activeRetailers);
      setHasDeliveryLocation(!!retailerData.dacsai_center);
      
      // Get RSHDs - filter to only show from retailers in DACDRLP-List
      const rshdResponse = await rshd.list();
      const allItems = rshdResponse.data || [];
      
      // Filter to only show items from retailers in user's DACDRLP-List
      const retailerIds = new Set(activeRetailers.map(r => r.drlp_id));
      const filteredItems = allItems.filter(item => retailerIds.has(item.drlp_id));
      
      setItems(filteredItems);
    } catch (error) {
      console.error('Failed to load radar data:', error);
      toast.error('Failed to load deals');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
    toast.success('Deals refreshed');
  };

  // Filter items by category
  const filteredItems = selectedCategory === 'all' 
    ? items 
    : items.filter(item => item.category === selectedCategory);

  // Get discount badge color
  const getDiscountBadge = (level) => {
    switch(level) {
      case 1: return { text: '50% OFF', color: 'bg-yellow-500' };
      case 2: return { text: '60% OFF', color: 'bg-orange-500' };
      case 3: return { text: '75% OFF', color: 'bg-red-500' };
      default: return { text: 'DEAL', color: 'bg-emerald-500' };
    }
  };

  // Get retailer name by ID
  const getRetailerName = (drlpId) => {
    const retailer = retailers.find(r => r.drlp_id === drlpId);
    return retailer?.drlp_name || 'Unknown Store';
  };

  if (loading) {
    return (
      <ConsumerLayout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        </div>
      </ConsumerLayout>
    );
  }

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Radar className="w-6 h-6 text-emerald-600" />
              <h1 className="text-2xl font-bold text-gray-900">Deal Radar</h1>
            </div>
            <p className="text-gray-600 mt-1">
              Live deals from your {retailers.length} local retailers
            </p>
          </div>
          <div className="flex gap-2">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.slice(1).map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button 
              variant="outline" 
              size="icon"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* No Location Warning */}
        {!hasDeliveryLocation && (
          <Alert className="bg-amber-50 border-amber-200">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              Set your delivery location in <strong>Settings</strong> to see deals from nearby retailers.
            </AlertDescription>
          </Alert>
        )}

        {/* No Retailers Warning */}
        {hasDeliveryLocation && retailers.length === 0 && (
          <Alert className="bg-blue-50 border-blue-200">
            <Store className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              No retailers in your area yet. Visit <strong>My Retailers</strong> to add stores manually.
            </AlertDescription>
          </Alert>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-emerald-600">{filteredItems.length}</p>
              <p className="text-sm text-gray-500">Active Deals</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-emerald-600">{retailers.length}</p>
              <p className="text-sm text-gray-500">Your Retailers</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-orange-500">
                {filteredItems.filter(i => i.discount_level >= 2).length}
              </p>
              <p className="text-sm text-gray-500">Hot Deals (60%+)</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-500">
                {filteredItems.filter(i => i.discount_level === 3).length}
              </p>
              <p className="text-sm text-gray-500">Super Deals (75%)</p>
            </CardContent>
          </Card>
        </div>

        {/* Deals Grid */}
        {filteredItems.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Radar className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Deals Available</h3>
              <p className="text-gray-500">
                {selectedCategory === 'all' 
                  ? 'Check back later for new deals from your local retailers'
                  : `No ${selectedCategory} deals right now. Try a different category.`}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map((item) => {
              const discount = getDiscountBadge(item.discount_level);
              return (
                <Card key={item.id} className="hover:shadow-lg transition-shadow overflow-hidden">
                  <div className={`${discount.color} text-white text-center py-1 text-sm font-bold`}>
                    {discount.text}
                  </div>
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{item.name}</CardTitle>
                        <CardDescription className="flex items-center gap-1 mt-1">
                          <Store className="w-3 h-3" />
                          {getRetailerName(item.drlp_id)}
                        </CardDescription>
                      </div>
                      <Badge variant="outline">{item.category}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {/* Price */}
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-emerald-600">
                        ${item.discounted_price?.toFixed(2)}
                      </span>
                      <span className="text-sm text-gray-400 line-through">
                        ${item.original_price?.toFixed(2)}
                      </span>
                    </div>

                    {/* Details */}
                    <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Tag className="w-3 h-3" />
                        {item.quantity} left
                      </span>
                      {item.expiry_date && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Expires: {new Date(item.expiry_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {/* Attributes */}
                    <div className="flex flex-wrap gap-1">
                      {item.attributes?.organic && (
                        <Badge className="bg-green-100 text-green-700 text-xs">🌿 Organic</Badge>
                      )}
                      {item.attributes?.local && (
                        <Badge className="bg-blue-100 text-blue-700 text-xs">📍 Local</Badge>
                      )}
                    </div>

                    {/* Action */}
                    <Button className="w-full bg-emerald-600 hover:bg-emerald-700">
                      <ShoppingCart className="w-4 h-4 mr-2" />
                      Add to Cart
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </ConsumerLayout>
  );
}
