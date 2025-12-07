import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { rshd } from '../../utils/api';
import { ShoppingBag, Search, MapPin } from 'lucide-react';
import { toast } from 'sonner';

// DealShaq 20-Category Taxonomy
const CATEGORIES = [
  "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
  "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
  "Snacks & Candy", "Frozen Foods", "Beverages",
  "Alcoholic Beverages", "Deli & Prepared Foods",
  "Breakfast & Cereal", "Pasta, Rice & Grains",
  "Oils, Sauces & Spices", "Baby & Kids",
  "Health & Nutrition", "Household Essentials",
  "Personal Care", "Pet Supplies"
];

export default function ConsumerBrowse({ user, onLogout }) {
  const [deals, setDeals] = useState([]);
  const [filteredDeals, setFilteredDeals] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDeals();
  }, []);

  useEffect(() => {
    filterDeals();
  }, [deals, selectedCategory, searchQuery]);

  const loadDeals = async () => {
    try {
      const response = await rshd.list();
      setDeals(response.data);
    } catch (error) {
      toast.error('Failed to load deals');
    } finally {
      setLoading(false);
    }
  };

  const filterDeals = () => {
    let filtered = deals;

    if (selectedCategory !== 'all') {
      filtered = filtered.filter((d) => d.category === selectedCategory);
    }

    if (searchQuery) {
      filtered = filtered.filter(
        (d) =>
          d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          d.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredDeals(filtered);
  };

  const addToCart = (deal) => {
    const existingItem = cart.find((item) => item.rshd_id === deal.id);
    if (existingItem) {
      setCart(
        cart.map((item) =>
          item.rshd_id === deal.id ? { ...item, quantity: item.quantity + 1 } : item
        )
      );
    } else {
      setCart([...cart, { rshd_id: deal.id, name: deal.name, price: deal.deal_price, quantity: 1 }]);
    }
    toast.success(`${deal.name} added to cart`);
  };

  const goToCheckout = () => {
    if (cart.length === 0) {
      toast.error('Your cart is empty');
      return;
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    window.location.href = '/consumer/checkout';
  };

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Surplus-Centric Info Banner */}
        <Card className="bg-gradient-to-r from-blue-50 to-emerald-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <Search className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-bold text-gray-900 mb-1">Surplus-Centric Model</h4>
                <p className="text-sm text-gray-600">
                  These deals were posted by local retailers with urgent items that must move fast. 
                  You're seeing them because they match your DACFI-List favorites. 
                  No searching needed - deals come to you! 🎯
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
              Browse Deals
            </h1>
            <p className="text-gray-600 mt-1">Find amazing discounts on quality groceries</p>
          </div>
          {cart.length > 0 && (
            <Button
              data-testid="checkout-btn"
              onClick={goToCheckout}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <ShoppingBag className="w-4 h-4 mr-2" />
              Checkout ({cart.length})
            </Button>
          )}
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  data-testid="search-input"
                  placeholder="Search deals..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger data-testid="category-filter">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Deals Grid */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading deals...</p>
          </div>
        ) : filteredDeals.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <ShoppingBag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No deals found</p>
              <p className="text-gray-400 text-sm mt-2">Try adjusting your filters</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredDeals.map((deal) => (
              <Card
                key={deal.id}
                data-testid={`deal-card-${deal.id}`}
                className="overflow-hidden hover:shadow-xl transition-all duration-300"
              >
                <div className="aspect-square bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center relative">
                  {deal.image_url ? (
                    <img src={deal.image_url} alt={deal.name} className="w-full h-full object-cover" />
                  ) : (
                    <ShoppingBag className="w-20 h-20 text-emerald-400" />
                  )}
                  <Badge className="absolute top-3 right-3 bg-red-500 text-white font-bold">
                    {deal.consumer_discount_percent}% OFF
                  </Badge>
                </div>
                <CardContent className="p-4">
                  <Badge variant="outline" className="mb-2 text-xs">
                    {deal.category}
                  </Badge>
                  <h3 className="font-bold text-gray-900 mb-1 line-clamp-1" data-testid={`deal-name-${deal.id}`}>
                    {deal.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-1 line-clamp-1">{deal.description}</p>
                  <div className="flex items-center text-xs text-gray-500 mb-3">
                    <MapPin className="w-3 h-3 mr-1" />
                    {deal.drlp_name}
                  </div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl font-bold text-emerald-600">${deal.deal_price}</span>
                      <span className="text-sm text-gray-500 line-through">${deal.regular_price}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">{deal.quantity} available</span>
                    <Button
                      data-testid={`add-to-cart-${deal.id}`}
                      size="sm"
                      onClick={() => addToCart(deal)}
                      disabled={deal.quantity === 0}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      Add to Cart
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </ConsumerLayout>
  );
}
