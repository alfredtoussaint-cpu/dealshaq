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
import { Store, Eye, EyeOff } from 'lucide-react';

export default function RetailerAuth({ onLogin }) {
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
  });
  const [loading, setLoading] = useState(false);

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!resetEmail) {
      toast.error('Please enter your email address');
      return;
    }
    
    try {
      const response = await auth.requestPasswordReset({ email: resetEmail, role: 'DRLP' });
      toast.success('Password reset instructions sent to ' + resetEmail);
      setShowForgotPassword(false);
      setResetEmail('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email');
    }
  };

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
          role: 'DRLP',  // Filter by Retailer role
        });
        onLogin(response.data.access_token, response.data.user);
        toast.success('Welcome back!');
      } else {
        const response = await auth.register({
          ...formData,
          role: 'DRLP',
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-2">
            <Store className="w-8 h-8 text-blue-600" />
          </div>
          <CardTitle className="text-3xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
            DealShaq Retailer
          </CardTitle>
          <CardDescription className="text-base">Post deals and manage your inventory</CardDescription>
        </CardHeader>

        <CardContent>
          <Tabs value={isLogin ? 'login' : 'register'} onValueChange={(v) => setIsLogin(v === 'login')}>
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="login" data-testid="retailer-login-tab">Login</TabsTrigger>
              <TabsTrigger value="register" data-testid="retailer-register-tab">Register</TabsTrigger>
            </TabsList>

            <form onSubmit={handleSubmit} className="space-y-4">
              <TabsContent value="login" className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    data-testid="retailer-login-email"
                    type="email"
                    placeholder="retailer@example.com"
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
                      data-testid="retailer-login-password"
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      className="pr-10"
                    />
                    <button
                      type="button"
                      data-testid="retailer-toggle-password"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <button
                    type="button"
                    data-testid="retailer-forgot-password-link"
                    onClick={() => {
                      setResetEmail(formData.email);
                      setShowForgotPassword(true);
                    }}
                    className="text-sm text-blue-600 hover:text-blue-700 mt-1"
                  >
                    Forgot password?
                  </button>
                </div>
              </TabsContent>

              <TabsContent value="register" className="space-y-4">
                <div>
                  <Label htmlFor="reg-name">Store Name</Label>
                  <Input
                    id="reg-name"
                    data-testid="retailer-register-name"
                    placeholder="My Grocery Store"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-email">Email</Label>
                  <Input
                    id="reg-email"
                    data-testid="retailer-register-email"
                    type="email"
                    placeholder="retailer@example.com"
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
                      data-testid="retailer-register-password"
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      className="pr-10"
                    />
                    <button
                      type="button"
                      data-testid="retailer-toggle-register-password"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div>
                  <Label htmlFor="charity">Partner Charity</Label>
                  <Select
                    value={formData.charity_id}
                    onValueChange={(value) => setFormData({ ...formData, charity_id: value })}
                  >
                    <SelectTrigger data-testid="retailer-register-charity">
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
                data-testid="retailer-auth-submit-btn"
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700"
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
                data-testid="retailer-reset-email"
                type="email"
                placeholder="retailer@example.com"
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
                data-testid="retailer-send-reset-btn"
                type="submit"
                className="flex-1 bg-blue-600 hover:bg-blue-700"
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
