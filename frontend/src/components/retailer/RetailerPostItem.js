import { useState, useEffect, useRef } from 'react';
import RetailerLayout from './RetailerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { rshd, drlp, barcode, ocr } from '../../utils/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { Package, Camera, Barcode, Upload, Loader2 } from 'lucide-react';

// DealShaq 20-Category Taxonomy (Top-level only)
const CATEGORIES = [
  "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
  "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
  "Snacks & Candy", "Frozen Foods", "Beverages",
  "Deli & Prepared Foods", "Breakfast & Cereal", 
  "Pasta, Rice & Grains", "Oils, Sauces & Spices", 
  "Baby & Kids", "Health & Nutrition", "Household Essentials",
  "Personal Care", "Pet Supplies", "Miscellaneous"
];

export default function RetailerPostItem({ user, onLogout }) {
  const navigate = useNavigate();
  const [hasLocation, setHasLocation] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    regular_price: '',
    discount_level: '1',
    quantity: '',
    barcode: '',
    weight: '',
    image_url: '',
    is_taxable: true,
    attributes: {},
  });
  const [scanning, setScanning] = useState(false);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const [barcodeInput, setBarcodeInput] = useState('');
  const priceImageRef = useRef(null);
  const productImageRef = useRef(null);

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

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data:image/xxx;base64, prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  // Real barcode lookup using Open Food Facts API
  const handleBarcodeLookup = async () => {
    const barcodeToLookup = barcodeInput || formData.barcode;
    if (!barcodeToLookup) {
      toast.error('Please enter a barcode number');
      return;
    }
    
    setScanning(true);
    try {
      const response = await barcode.lookup(barcodeToLookup);
      const product = response.data.product;
      
      if (product) {
        setFormData({
          ...formData,
          name: product.name || formData.name,
          category: product.category || formData.category,
          barcode: barcodeToLookup,
          weight: product.weight?.toString() || formData.weight,
          description: product.description || formData.description,
          image_url: product.image_url || formData.image_url,
          attributes: {
            ...formData.attributes,
            organic: product.is_organic || false,
            brand: product.brand || '',
          }
        });
        toast.success(`Product found: ${product.name}`);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Product not found in database';
      toast.error(errorMsg);
      // Still set the barcode even if product not found
      setFormData({ ...formData, barcode: barcodeToLookup });
    } finally {
      setScanning(false);
      setBarcodeInput('');
    }
  };

  // OCR price extraction from image
  const handlePriceImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error('Please upload a JPEG, PNG, or WEBP image');
      return;
    }
    
    setOcrProcessing(true);
    try {
      const imageBase64 = await fileToBase64(file);
      const response = await ocr.extractPrice(imageBase64);
      
      if (response.data.success && response.data.extracted) {
        const extracted = response.data.extracted;
        
        if (extracted.price) {
          // Clean the price (remove $ and other characters)
          const cleanPrice = extracted.price.replace(/[^0-9.]/g, '');
          setFormData({
            ...formData,
            regular_price: cleanPrice,
            name: extracted.product_name || formData.name,
          });
          toast.success(`Price extracted: $${cleanPrice}`);
        } else if (extracted.raw_text) {
          toast.info('Could not extract structured price. Please check the image.');
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to extract price from image';
      toast.error(errorMsg);
    } finally {
      setOcrProcessing(false);
      // Reset file input
      if (priceImageRef.current) {
        priceImageRef.current.value = '';
      }
    }
  };

  // Product image analysis
  const handleProductImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error('Please upload a JPEG, PNG, or WEBP image');
      return;
    }
    
    setScanning(true);
    try {
      const imageBase64 = await fileToBase64(file);
      const response = await ocr.analyzeProduct(imageBase64);
      
      if (response.data.success && response.data.product) {
        const product = response.data.product;
        
        setFormData({
          ...formData,
          name: product.product_name || formData.name,
          category: product.category || formData.category,
          description: product.description || formData.description,
          attributes: {
            ...formData.attributes,
            organic: product.is_organic || false,
            brand: product.brand || '',
          }
        });
        toast.success('Product information extracted from image');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to analyze product image';
      toast.error(errorMsg);
    } finally {
      setScanning(false);
      if (productImageRef.current) {
        productImageRef.current.value = '';
      }
    }
  };

  // Legacy mock scan (kept for fallback/demo)
    // Simulate barcode scanning
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock product data (in real implementation, call backend API)
    const mockProducts = [
      { name: 'Organic Honeycrisp Apples 5lb', category: 'Fruits', barcode: '012345678901', weight: 5.0 },
      { name: 'Grass-Fed Ground Beef 1lb', category: 'Meat & Poultry', barcode: '098765432109', weight: 1.0 },
      { name: 'Greek Yogurt 32oz', category: 'Dairy & Eggs', barcode: '555666777888', weight: 2.0 },
    ];
    const product = mockProducts[Math.floor(Math.random() * mockProducts.length)];
    
    setFormData({
      ...formData,
      name: product.name,
      category: product.category,
      barcode: product.barcode,
      weight: product.weight.toString(),
    });
    setScanning(false);
    toast.success('Barcode scanned! Product info auto-populated');
  };

  // Mock OCR price scan function
  const handlePriceScan = async () => {
    setOcrProcessing(true);
    // Simulate OCR processing
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock extracted price (in real implementation, call OCR API)
    const mockPrice = (Math.random() * 20 + 5).toFixed(2);
    
    setFormData({
      ...formData,
      regular_price: mockPrice,
    });
    setOcrProcessing(false);
    toast.success(`Price extracted: $${mockPrice}`);
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
      const payload = {
        name: formData.name,
        description: formData.description || '',
        category: formData.category,
        subcategory: '',  // Optional, not used in matching
        regular_price: parseFloat(formData.regular_price),
        discount_level: parseInt(formData.discount_level),
        quantity: parseInt(formData.quantity),
        barcode: formData.barcode || '',
        weight: formData.weight ? parseFloat(formData.weight) : null,
        image_url: formData.image_url || '',
        is_taxable: formData.is_taxable,
        attributes: formData.attributes || {},
      };
      
      await rshd.create(payload);
      toast.success('RSHD posted successfully! DACs with matching favorites will be notified.');
      navigate('/retailer/inventory');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to post RSHD');
    } finally {
      setLoading(false);
    }
  };

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
            Post RSHD Item
          </h1>
          <p className="text-gray-600 mt-1">Post a Retailer Sizzling Hot Deal that must move fast. We'll match it to interested DACs.</p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Step 1: Barcode Capture */}
          <Card className="mb-4">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Barcode className="w-5 h-5" />
                <span>Step 1: Scan Barcode</span>
              </CardTitle>
              <CardDescription>Auto-populate product name and category</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Button
                  type="button"
                  onClick={handleBarcodeScan}
                  disabled={scanning}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  data-testid="scan-barcode-btn"
                >
                  {scanning ? (
                    <>
                      <span className="animate-spin mr-2">⟳</span>
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Barcode className="w-4 h-4 mr-2" />
                      Scan Barcode
                    </>
                  )}
                </Button>
                <span className="text-gray-500 py-2">or</span>
                <Input
                  placeholder="Enter barcode manually"
                  value={formData.barcode}
                  onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                  className="flex-1"
                  data-testid="manual-barcode"
                />
              </div>
              {formData.name && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm font-medium text-green-800">✓ Product Found</p>
                  <p className="text-sm text-green-700 mt-1">{formData.name}</p>
                  <p className="text-xs text-green-600 mt-1">Category: {formData.category}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 2: Price & Details */}
          <Card className="mb-4">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Camera className="w-5 h-5" />
                <span>Step 2: Capture Price</span>
              </CardTitle>
              <CardDescription>Scan price label or enter manually</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Button
                  type="button"
                  onClick={handlePriceScan}
                  disabled={ocrProcessing}
                  variant="outline"
                  className="flex-1"
                  data-testid="scan-price-btn"
                >
                  {ocrProcessing ? (
                    <>
                      <span className="animate-spin mr-2">⟳</span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Camera className="w-4 h-4 mr-2" />
                      Scan Price Label
                    </>
                  )}
                </Button>
                <span className="text-gray-500 py-2">or</span>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="$0.00"
                  value={formData.regular_price}
                  onChange={(e) => setFormData({ ...formData, regular_price: e.target.value })}
                  className="flex-1"
                  data-testid="manual-price"
                  required
                />
              </div>
            </CardContent>
          </Card>

          {/* Step 3: Deal Configuration */}
          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Step 3: Configure Deal</CardTitle>
              <CardDescription>Set discount level and quantity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <Label htmlFor="name">Item Name * {formData.name && <span className="text-green-600 text-xs">(Auto-populated)</span>}</Label>
                  <Input
                    id="name"
                    data-testid="item-name"
                    placeholder="Will be auto-filled by barcode scan"
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
                  <Label htmlFor="category">Category * (Top-level only)</Label>
                  <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                    <SelectTrigger data-testid="item-category">
                      <SelectValue placeholder="Select from 20 categories" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-1">20-category taxonomy for efficient matching</p>
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
