import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { auth, charities as charitiesApi } from '../../utils/api';
import { toast } from 'sonner';
import { ShoppingCart, Eye, EyeOff, MapPin, Navigation, Loader2 } from 'lucide-react';
import Logo from '../Logo';

export default function ConsumerAuth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [charities, setCharities] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    charity_id: '',
    delivery_location: {
      address: '',
      coordinates: { lat: null, lng: null }
    },
    dacsai_rad: 5.0,
  });
  const [geocoding, setGeocoding] = useState(false);
  const [geocodeError, setGeocodeError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCharities();
  }, []);

  const loadCharities = async () => {
    try {
      const response = await charitiesApi.list();
      setCharities(response.data);
    } catch (error) {
      console.error('Failed to load charities:', error);
    }
  };

  // Geocode address to coordinates using a free geocoding service
  const geocodeAddress = async (address) => {
    if (!address || address.trim().length < 5) {
      return null;
    }
    
    setGeocoding(true);
    setGeocodeError('');
    
    try {
      // Using Nominatim (OpenStreetMap) for geocoding - free, no API key required
      const encodedAddress = encodeURIComponent(address);
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodedAddress}&limit=1`,
        { headers: { 'User-Agent': 'DealShaq-App' } }
      );
      
      if (!response.ok) {
        throw new Error('Geocoding service unavailable');
      }
      
      const data = await response.json();
      
      if (data && data.length > 0) {
        const { lat, lon } = data[0];
        return { lat: parseFloat(lat), lng: parseFloat(lon) };
      } else {
        setGeocodeError('Address not found. Please enter a valid address.');
        return null;
      }
    } catch (error) {
      console.error('Geocoding error:', error);
      setGeocodeError('Unable to verify address. Please try again.');
      return null;
    } finally {
      setGeocoding(false);
    }
  };

  const handleAddressBlur = async () => {
    const address = formData.delivery_location.address;
    if (address && address.trim().length >= 5) {
      const coordinates = await geocodeAddress(address);
      if (coordinates) {
        setFormData({
          ...formData,
          delivery_location: { 
            address: address,
            coordinates 
          }
        });
        setGeocodeError('');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const response = await auth.login({
          email: formData.email,
          password: formData.password,
          role: 'DAC',
        });
        onLogin(response.data.access_token, response.data.user);
        toast.success('Welcome back!');
      } else {
        // Validate required fields for registration
        if (!formData.delivery_location.address) {
          toast.error('Delivery address is required');
          setLoading(false);
          return;
        }
        
        // Geocode address if not already done
        let coordinates = formData.delivery_location.coordinates;
        if (!coordinates || !coordinates.lat || !coordinates.lng) {
          coordinates = await geocodeAddress(formData.delivery_location.address);
          if (!coordinates) {
            toast.error('Please enter a valid delivery address');
            setLoading(false);
            return;
          }
        }
        
        const response = await auth.register({
          ...formData,
          delivery_location: {
            address: formData.delivery_location.address,
            coordinates
          },
          role: 'DAC',
        });
        onLogin(response.data.access_token, response.data.user);
        toast.success('Account created successfully!');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!resetEmail) {
      toast.error('Please enter your email address');
      return;
    }
    
    try {
      const response = await auth.requestPasswordReset({ email: resetEmail, role: 'DAC' });
      toast.success('Password reset instructions sent to ' + resetEmail);
      setShowForgotPassword(false);
      setResetEmail('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-2">
            <Logo size="large" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-700">
            Consumer Portal
          </CardTitle>
          <CardDescription className="text-base">Join the smart shopping revolution</CardDescription>
        </CardHeader>

        <CardContent>
          <Tabs value={isLogin ? 'login' : 'register'} onValueChange={(v) => setIsLogin(v === 'login')}>
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
              <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
            </TabsList>

            <form onSubmit={handleSubmit} className="space-y-4">
              <TabsContent value="login" className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    data-testid="login-email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      data-testid="login-password"
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      className="pr-10"
                    />
                    <button
                      type="button"
                      data-testid="toggle-password"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <button
                    type="button"
                    data-testid="forgot-password-link"
                    onClick={() => {
                      setResetEmail(formData.email);
                      setShowForgotPassword(true);
                    }}
                    className="text-sm text-emerald-600 hover:text-emerald-700 mt-1"
                  >
                    Forgot password?
                  </button>
                </div>
              </TabsContent>

              <TabsContent value="register" className="space-y-4">
                <div>
                  <Label htmlFor="reg-name">Full Name</Label>
                  <Input
                    id="reg-name"
                    data-testid="register-name"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-email">Email</Label>
                  <Input
                    id="reg-email"
                    data-testid="register-email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-password">Password</Label>
                  <div className="relative">
                    <Input
                      id="reg-password"
                      data-testid="register-password"
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      className="pr-10"
                    />
                    <button
                      type="button"
                      data-testid="toggle-register-password"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-emerald-600" />
                    <Label htmlFor="delivery-address">Delivery Address <span className="text-red-500">*</span></Label>
                  </div>
                  <div className="relative">
                    <Input
                      id="delivery-address"
                      data-testid="register-address"
                      placeholder="123 Main St, City, State ZIP"
                      value={formData.delivery_location.address}
                      onChange={(e) => setFormData({
                        ...formData,
                        delivery_location: { ...formData.delivery_location, address: e.target.value, coordinates: { lat: null, lng: null } }
                      })}
                      onBlur={handleAddressBlur}
                      required
                      className={geocodeError ? 'border-red-500' : formData.delivery_location.coordinates?.lat ? 'border-green-500' : ''}
                    />
                    {geocoding && (
                      <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-emerald-600" />
                    )}
                    {!geocoding && formData.delivery_location.coordinates?.lat && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500 text-xs">✓ Verified</span>
                    )}
                  </div>
                  {geocodeError && (
                    <p className="text-xs text-red-500">{geocodeError}</p>
                  )}
                  <p className="text-xs text-gray-500">This is the center of your shopping area (DACSAI)</p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Navigation className="w-4 h-4 text-emerald-600" />
                    <Label htmlFor="dacsai-radius">DACSAI Radius: <span className="font-bold text-emerald-600">{formData.dacsai_rad} miles</span></Label>
                  </div>
                  <Input
                    id="dacsai-radius"
                    data-testid="register-radius"
                    type="range"
                    min="0.1"
                    max="9.9"
                    step="0.1"
                    value={formData.dacsai_rad}
                    onChange={(e) => setFormData({ ...formData, dacsai_rad: parseFloat(e.target.value) })}
                    className="w-full accent-emerald-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>0.1 mi (nearby only)</span>
                    <span>9.9 mi (wider area)</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    Retailers within this radius will be added to your list automatically
                  </p>
                </div>
                <div>
                  <Label htmlFor="charity">Preferred Charity</Label>
                  <Select
                    value={formData.charity_id}
                    onValueChange={(value) => setFormData({ ...formData, charity_id: value })}
                  >
                    <SelectTrigger data-testid="register-charity">
                      <SelectValue placeholder="Select a charity" />
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
              </TabsContent>

              <Button
                data-testid="auth-submit-btn"
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-700"
                disabled={loading}
              >
                {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
              </Button>
            </form>
          </Tabs>
        </CardContent>
      </Card>

      {/* Forgot Password Modal */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password</DialogTitle>
            <DialogDescription>
              Enter your email address and we'll send you password reset instructions.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleForgotPassword} className="space-y-4">
            <div>
              <Label htmlFor="reset-email">Email Address</Label>
              <Input
                id="reset-email"
                data-testid="reset-email"
                type="email"
                placeholder="you@example.com"
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
                required
              />
            </div>
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowForgotPassword(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                data-testid="send-reset-btn"
                type="submit"
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              >
                Send Reset Link
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
