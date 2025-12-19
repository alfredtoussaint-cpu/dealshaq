import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { userSettings, dacRetailers, auth } from '../../utils/api';
import { Settings, Save, MapPin, Navigation, Loader2, CheckCircle, AlertCircle, User, Lock, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function ConsumerSettings({ user, onLogout }) {
  const [autoThreshold, setAutoThreshold] = useState('0');
  const [saving, setSaving] = useState(false);
  
  // Location settings
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [coordinates, setCoordinates] = useState(null);
  
  // Password change settings
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [dacsaiRad, setDacsaiRad] = useState(5.0);
  const [geocoding, setGeocoding] = useState(false);
  const [geocodeError, setGeocodeError] = useState('');
  const [savingLocation, setSavingLocation] = useState(false);
  const [currentUser, setCurrentUser] = useState(user);

  useEffect(() => {
    // Load current user settings
    if (user?.auto_favorite_threshold !== undefined) {
      setAutoThreshold(String(user.auto_favorite_threshold));
    }
    if (user?.delivery_location?.address) {
      setDeliveryAddress(user.delivery_location.address);
      setCoordinates(user.delivery_location.coordinates);
    }
    if (user?.dacsai_rad !== undefined) {
      setDacsaiRad(user.dacsai_rad);
    }
    
    // Fetch fresh user data
    fetchCurrentUser();
  }, [user]);

  const fetchCurrentUser = async () => {
    try {
      const response = await auth.me();
      const userData = response.data;
      setCurrentUser(userData);
      
      if (userData.delivery_location?.address) {
        setDeliveryAddress(userData.delivery_location.address);
        setCoordinates(userData.delivery_location.coordinates);
      }
      if (userData.dacsai_rad !== undefined) {
        setDacsaiRad(userData.dacsai_rad);
      }
      if (userData.auto_favorite_threshold !== undefined) {
        setAutoThreshold(String(userData.auto_favorite_threshold));
      }
    } catch (error) {
      console.error('Failed to fetch user data:', error);
    }
  };

  // Geocode address to coordinates
  const geocodeAddress = async (address) => {
    if (!address || address.trim().length < 5) {
      setGeocodeError('Please enter a complete address');
      return null;
    }
    
    setGeocoding(true);
    setGeocodeError('');
    
    try {
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
        const coords = { lat: parseFloat(lat), lng: parseFloat(lon) };
        setCoordinates(coords);
        return coords;
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
    if (deliveryAddress && deliveryAddress.trim().length >= 5) {
      await geocodeAddress(deliveryAddress);
    }
  };

  const handleSaveAutoThreshold = async () => {
    setSaving(true);
    try {
      await userSettings.updateAutoThreshold({
        auto_favorite_threshold: parseInt(autoThreshold)
      });
      toast.success('Smart Favorites settings saved!');
      
      // Update user in localStorage
      const updatedUser = { ...currentUser, auto_favorite_threshold: parseInt(autoThreshold) };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setCurrentUser(updatedUser);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLocation = async () => {
    if (!deliveryAddress) {
      toast.error('Please enter a delivery address');
      return;
    }

    setSavingLocation(true);
    
    try {
      // Geocode if not already done
      let coords = coordinates;
      if (!coords || !coords.lat) {
        coords = await geocodeAddress(deliveryAddress);
        if (!coords) {
          setSavingLocation(false);
          return;
        }
      }

      // First update delivery location
      await dacRetailers.updateLocation({
        address: deliveryAddress,
        coordinates: coords
      });
      
      // Then update DACSAI radius (this will recalculate DACDRLP-List)
      const response = await dacRetailers.updateDacsai(dacsaiRad);
      
      toast.success(`Location and DACSAI updated! ${response.data.retailers_count} retailers in your area.`);
      
      // Update user in localStorage
      const updatedUser = { 
        ...currentUser, 
        delivery_location: { address: deliveryAddress, coordinates: coords },
        dacsai_rad: dacsaiRad
      };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setCurrentUser(updatedUser);
      setCoordinates(coords);
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to save location settings';
      toast.error(message);
    } finally {
      setSavingLocation(false);
    }
  };

  const handleChangePassword = async () => {
    // Validation
    if (!currentPassword) {
      toast.error('Please enter your current password');
      return;
    }
    if (!newPassword) {
      toast.error('Please enter a new password');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (currentPassword === newPassword) {
      toast.error('New password must be different from current password');
      return;
    }

    setChangingPassword(true);
    
    try {
      await auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      
      toast.success('Password changed successfully!');
      
      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to change password';
      toast.error(message);
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <ConsumerLayout user={currentUser} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Manage your DealShaq preferences</p>
        </div>

        {/* Location & DACSAI Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <MapPin className="w-5 h-5 text-emerald-600" />
              <CardTitle>Shopping Area (DACSAI)</CardTitle>
            </div>
            <CardDescription>
              Set your delivery location and shopping radius to receive notifications from nearby retailers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Current Status */}
            {coordinates?.lat ? (
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Your shopping area is set: {dacsaiRad} mile radius from your delivery location
                </AlertDescription>
              </Alert>
            ) : (
              <Alert className="bg-amber-50 border-amber-200">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  Set your delivery location to start receiving notifications from nearby retailers
                </AlertDescription>
              </Alert>
            )}

            {/* Delivery Address */}
            <div className="space-y-2">
              <Label htmlFor="delivery-address" className="text-sm font-medium">
                Delivery Address
              </Label>
              <div className="relative">
                <Input
                  id="delivery-address"
                  placeholder="123 Main St, City, State ZIP"
                  value={deliveryAddress}
                  onChange={(e) => {
                    setDeliveryAddress(e.target.value);
                    setCoordinates(null); // Reset coordinates when address changes
                  }}
                  onBlur={handleAddressBlur}
                  className={geocodeError ? 'border-red-500 pr-20' : coordinates?.lat ? 'border-green-500 pr-20' : 'pr-20'}
                />
                {geocoding && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-emerald-600" />
                )}
                {!geocoding && coordinates?.lat && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-600 text-xs font-medium">✓ Verified</span>
                )}
              </div>
              {geocodeError && (
                <p className="text-xs text-red-500">{geocodeError}</p>
              )}
              <p className="text-xs text-gray-500">This is the center point of your shopping area</p>
            </div>

            {/* DACSAI Radius */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium flex items-center gap-2">
                  <Navigation className="w-4 h-4 text-emerald-600" />
                  DACSAI Radius
                </Label>
                <span className="text-lg font-bold text-emerald-600">{dacsaiRad} miles</span>
              </div>
              <Slider
                value={[dacsaiRad]}
                onValueChange={(value) => setDacsaiRad(value[0])}
                min={0.1}
                max={9.9}
                step={0.1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0.1 mi (nearby only)</span>
                <span>9.9 mi (wider area)</span>
              </div>
              <p className="text-xs text-gray-500">
                Retailers within this radius are automatically added to your DACDRLP-List
              </p>
            </div>

            <Button 
              onClick={handleSaveLocation} 
              disabled={savingLocation || (!deliveryAddress)}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              {savingLocation ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Location Settings
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Smart Favorites Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Settings className="w-5 h-5 text-emerald-600" />
              <CardTitle>Smart Favorites</CardTitle>
            </div>
            <CardDescription>
              DealShaq can automatically add items to your favorites based on your purchase history
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <Label className="text-base font-medium text-gray-900">
                How many separate days would you want to be buying a non-favorite item, before you want DealShaq to add that item to your favorites list?
              </Label>
              
              <RadioGroup value={autoThreshold} onValueChange={setAutoThreshold} className="space-y-3">
                <div className="flex items-center space-x-3 border rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                  <RadioGroupItem value="6" id="threshold-6" />
                  <Label htmlFor="threshold-6" className="flex-1 cursor-pointer">
                    <div className="font-medium">6 separate days</div>
                    <div className="text-sm text-gray-500">More selective - only add frequently purchased items</div>
                  </Label>
                </div>

                <div className="flex items-center space-x-3 border rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                  <RadioGroupItem value="3" id="threshold-3" />
                  <Label htmlFor="threshold-3" className="flex-1 cursor-pointer">
                    <div className="font-medium">3 separate days</div>
                    <div className="text-sm text-gray-500">Balanced - add items you buy regularly</div>
                  </Label>
                </div>

                <div className="flex items-center space-x-3 border rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                  <RadioGroupItem value="0" id="threshold-never" />
                  <Label htmlFor="threshold-never" className="flex-1 cursor-pointer">
                    <div className="font-medium">Never (0 days)</div>
                    <div className="text-sm text-gray-500">I will manage my favorites manually</div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">How It Works</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• DealShaq tracks items you purchase that are not in your favorites</li>
                <li>• When you buy an item on {autoThreshold === '0' ? 'N/A (disabled)' : `${autoThreshold} separate days`}, it is automatically added</li>
                <li>• Auto-added items appear with a date stamp in your favorites list</li>
                <li>• You can remove any item (manual or auto-added) at any time</li>
                <li>• This feature runs daily at 11 PM</li>
              </ul>
            </div>

            <Button 
              onClick={handleSaveAutoThreshold} 
              disabled={saving}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save Smart Favorites Settings'}
            </Button>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-emerald-600" />
              <CardTitle>Account Information</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-gray-500">Email</Label>
                <p className="text-base font-medium">{currentUser?.email}</p>
              </div>
              <div>
                <Label className="text-sm text-gray-500">Name</Label>
                <p className="text-base font-medium">{currentUser?.name}</p>
              </div>
              <div>
                <Label className="text-sm text-gray-500">Role</Label>
                <p className="text-base font-medium">Consumer (DAC)</p>
              </div>
              <div>
                <Label className="text-sm text-gray-500">DACSAI Radius</Label>
                <p className="text-base font-medium">{currentUser?.dacsai_rad || 5.0} miles</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Lock className="w-5 h-5 text-emerald-600" />
              <CardTitle>Change Password</CardTitle>
            </div>
            <CardDescription>
              Update your account password
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Current Password */}
            <div className="space-y-2">
              <Label htmlFor="current-password">Current Password</Label>
              <div className="relative">
                <Input
                  id="current-password"
                  type={showCurrentPassword ? 'text' : 'password'}
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <div className="relative">
                <Input
                  id="new-password"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Enter new password (min 8 characters)"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {newPassword && newPassword.length < 8 && (
                <p className="text-xs text-red-500">Password must be at least 8 characters</p>
              )}
            </div>

            {/* Confirm New Password */}
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm New Password</Label>
              <Input
                id="confirm-password"
                type="password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="text-xs text-red-500">Passwords do not match</p>
              )}
            </div>

            <Button 
              onClick={handleChangePassword} 
              disabled={changingPassword || !currentPassword || !newPassword || newPassword.length < 8 || newPassword !== confirmPassword}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              {changingPassword ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Changing Password...
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4 mr-2" />
                  Change Password
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    </ConsumerLayout>
  );
}
