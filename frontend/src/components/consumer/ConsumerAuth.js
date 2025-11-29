import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { auth, charities as charitiesApi } from '../../utils/api';
import { toast } from 'sonner';
import { ShoppingCart, Eye, EyeOff } from 'lucide-react';

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
      coordinates: { lat: 0, lng: 0 }
    },
    dacsai_radius: 5.0,
  });
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const response = await auth.login({
          email: formData.email,
          password: formData.password,
          role: 'DAC',  // Filter by Consumer role
        });
        onLogin(response.data.access_token, response.data.user);
        toast.success('Welcome back!');
      } else {
        const response = await auth.register({
          ...formData,
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-2">
            <ShoppingCart className="w-8 h-8 text-emerald-600" />
          </div>
          <CardTitle className="text-3xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
            DealShaq Consumer
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
                    onClick={() => setShowForgotPassword(true)}
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
                  <Input
                    id="reg-password"
                    data-testid="register-password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="delivery-address">Delivery Address</Label>
                  <Input
                    id="delivery-address"
                    data-testid="register-address"
                    placeholder="123 Main St, City, State ZIP"
                    value={formData.delivery_location.address}
                    onChange={(e) => setFormData({
                      ...formData,
                      delivery_location: { ...formData.delivery_location, address: e.target.value }
                    })}
                  />
                  <p className="text-xs text-gray-500 mt-1">Used as center for your shopping area</p>
                </div>
                <div>
                  <Label htmlFor="dacsai-radius">Shopping Radius: {formData.dacsai_radius} miles</Label>
                  <Input
                    id="dacsai-radius"
                    data-testid="register-radius"
                    type="range"
                    min="0.1"
                    max="9.9"
                    step="0.1"
                    value={formData.dacsai_radius}
                    onChange={(e) => setFormData({ ...formData, dacsai_radius: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>0.1 mi</span>
                    <span>9.9 mi</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">DACSAI: Your Shopping Area of Interest</p>
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
    </div>
  );
}
