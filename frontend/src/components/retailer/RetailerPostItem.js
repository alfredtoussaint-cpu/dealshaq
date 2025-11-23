import { useState, useEffect } from 'react';
import RetailerLayout from './RetailerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { rshd, drlp } from '../../utils/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { Package, Camera, Barcode } from 'lucide-react';

const CATEGORIES = [
  { value: 'Produce', subcategories: ['Fruits', 'Vegetables', 'Organic'] },
  { value: 'Dairy', subcategories: ['Milk', 'Cheese', 'Yogurt'] },
  { value: 'Meat & Seafood', subcategories: ['Beef', 'Chicken', 'Fish'] },
  { value: 'Bakery', subcategories: ['Bread', 'Pastries', 'Cakes'] },
  { value: 'Frozen', subcategories: ['Ice Cream', 'Meals', 'Vegetables'] },
  { value: 'Pantry', subcategories: ['Pasta', 'Rice', 'Canned Goods'] },
  { value: 'Beverages', subcategories: ['Juice', 'Soda', 'Water'] },
  { value: 'Snacks', subcategories: ['Chips', 'Candy', 'Nuts'] },
];

export default function RetailerPostItem({ user, onLogout }) {
  const navigate = useNavigate();
  const [hasLocation, setHasLocation] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    subcategory: '',
    regular_price: '',
    discount_level: '1',
    quantity: '',
    barcode: '',
    weight: '',
    image_url: '',
    is_taxable: true,
  });

  // Calculate discounts based on selected level
  const getDiscountInfo = () => {
    const level = parseInt(formData.discount_level);
    const discountMap = {
      1: { drlp: 60, consumer: 50 },
      2: { drlp: 75, consumer: 60 },
      3: { drlp: 90, consumer: 75 },
    };
    return discountMap[level] || { drlp: 0, consumer: 0 };
  };

  const calculateDealPrice = () => {
    if (!formData.regular_price) return '0.00';
    const price = parseFloat(formData.regular_price);
    const discountInfo = getDiscountInfo();
    return (price * (1 - discountInfo.consumer / 100)).toFixed(2);
  };
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkLocation();
  }, []);

  const checkLocation = async () => {
    try {
      await drlp.myLocation();
      setHasLocation(true);
    } catch (error) {
      setHasLocation(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!hasLocation) {
      toast.error('Please set up your location first');
      return;
    }

    setLoading(true);

    try {
      await rshd.create({
        ...formData,
        regular_price: parseFloat(formData.regular_price),
        discount_level: parseInt(formData.discount_level),
        quantity: parseInt(formData.quantity),
        weight: formData.weight ? parseFloat(formData.weight) : null,
      });
      toast.success('Deal posted successfully!');
      navigate('/retailer/inventory');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to post deal');
    } finally {
      setLoading(false);
    }
  };

  const selectedCategoryObj = CATEGORIES.find((c) => c.value === formData.category);

  if (!hasLocation) {
    return (
      <RetailerLayout user={user} onLogout={onLogout}>
        <Card>
          <CardHeader>
            <CardTitle>Setup Required</CardTitle>
            <CardDescription>Please set up your store location first</CardDescription>
          </CardHeader>
          <CardContent>
            <SetupLocationForm onComplete={() => setHasLocation(true)} />
          </CardContent>
        </Card>
      </RetailerLayout>
    );
  }

  return (
    <RetailerLayout user={user} onLogout={onLogout}>
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Post New Deal
          </h1>
          <p className="text-gray-600 mt-1">Create a hot deal for customers</p>
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Deal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <Label htmlFor="name">Item Name *</Label>
                  <Input
                    id="name"
                    data-testid="item-name"
                    placeholder="Fresh Organic Apples"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>

                <div className="md:col-span-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    data-testid="item-description"
                    placeholder="5 lb bag of fresh organic apples"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>

                <div>
                  <Label htmlFor="category">Category *</Label>
                  <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value, subcategory: '' })}>
                    <SelectTrigger data-testid="item-category">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.value}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="subcategory">Subcategory</Label>
                  <Select
                    value={formData.subcategory}
                    onValueChange={(value) => setFormData({ ...formData, subcategory: value })}
                    disabled={!formData.category}
                  >
                    <SelectTrigger data-testid="item-subcategory">
                      <SelectValue placeholder="Select subcategory" />
                    </SelectTrigger>
                    <SelectContent>
                      {selectedCategoryObj?.subcategories.map((sub) => (
                        <SelectItem key={sub} value={sub}>
                          {sub}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="regular_price">Regular Price *</Label>
                  <Input
                    id="regular_price"
                    data-testid="item-regular-price"
                    type="number"
                    step="0.01"
                    placeholder="9.99"
                    value={formData.regular_price}
                    onChange={(e) => setFormData({ ...formData, regular_price: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="discount_level">Discount Level *</Label>
                  <Select value={formData.discount_level} onValueChange={(value) => setFormData({ ...formData, discount_level: value })}>
                    <SelectTrigger data-testid="item-discount-level">
                      <SelectValue placeholder="Select level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Level 1 - You: 60% → Consumer: 50%</SelectItem>
                      <SelectItem value="2">Level 2 - You: 75% → Consumer: 60%</SelectItem>
                      <SelectItem value="3">Level 3 - You: 90% → Consumer: 75%</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-1">
                    You discount to DealShaq, consumer sees mapped discount
                  </p>
                </div>

                <div className="md:col-span-2 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-2">Pricing Preview</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-600">Regular Price:</p>
                      <p className="font-bold text-gray-900">${formData.regular_price || '0.00'}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Consumer Deal Price:</p>
                      <p className="font-bold text-emerald-600">${calculateDealPrice()}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Your Discount to DealShaq:</p>
                      <p className="font-bold text-blue-600">{getDiscountInfo().drlp}%</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Consumer Sees:</p>
                      <p className="font-bold text-emerald-600">{getDiscountInfo().consumer}% OFF</p>
                    </div>
                  </div>
                </div>

                <div>
                  <Label htmlFor="quantity">Quantity Available *</Label>
                  <Input
                    id="quantity"
                    data-testid="item-quantity"
                    type="number"
                    placeholder="50"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="barcode">Barcode (UPC/PLU)</Label>
                  <div className="flex space-x-2">
                    <Input
                      id="barcode"
                      data-testid="item-barcode"
                      placeholder="012345678901"
                      value={formData.barcode}
                      onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    />
                    <Button type="button" variant="outline" size="icon">
                      <Barcode className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <Label htmlFor="weight">Weight (lbs, optional)</Label>
                  <Input
                    id="weight"
                    data-testid="item-weight"
                    type="number"
                    step="0.01"
                    placeholder="5.0"
                    value={formData.weight}
                    onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                  />
                </div>

                <div>
                  <Label htmlFor="image_url">Image URL</Label>
                  <div className="flex space-x-2">
                    <Input
                      id="image_url"
                      data-testid="item-image-url"
                      placeholder="https://..."
                      value={formData.image_url}
                      onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                    />
                    <Button type="button" variant="outline" size="icon">
                      <Camera className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              <Button
                data-testid="post-item-btn"
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? 'Posting...' : 'Post Deal'}
              </Button>
            </CardContent>
          </Card>
        </form>
      </div>
    </RetailerLayout>
  );
}

function SetupLocationForm({ onComplete }) {
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    charity_id: '',
  });
  const [charities, setCharities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCharities();
  }, []);

  const loadCharities = async () => {
    try {
      const { charities: charitiesApi } = await import('../../utils/api');
      const response = await charitiesApi.list();
      setCharities(response.data);
    } catch (error) {
      console.error('Failed to load charities:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await drlp.createLocation({
        ...formData,
        coordinates: { lat: 0, lng: 0 },
        operating_hours: '9 AM - 9 PM',
      });
      toast.success('Location set up successfully!');
      onComplete();
    } catch (error) {
      toast.error('Failed to set up location');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="location-name">Store Name</Label>
        <Input
          id="location-name"
          data-testid="location-name"
          placeholder="Downtown Grocery"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />
      </div>
      <div>
        <Label htmlFor="location-address">Address</Label>
        <Input
          id="location-address"
          data-testid="location-address"
          placeholder="123 Main St, City, State ZIP"
          value={formData.address}
          onChange={(e) => setFormData({ ...formData, address: e.target.value })}
          required
        />
      </div>
      <div>
        <Label htmlFor="location-charity">Partner Charity</Label>
        <Select value={formData.charity_id} onValueChange={(value) => setFormData({ ...formData, charity_id: value })}>
          <SelectTrigger data-testid="location-charity">
            <SelectValue placeholder="Select charity" />
          </SelectTrigger>
          <SelectContent>
            {charities.map((charity) => (
              <SelectItem key={charity.id} value={charity.id}>
                {charity.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? 'Setting up...' : 'Set Up Location'}
      </Button>
    </form>
  );
}
