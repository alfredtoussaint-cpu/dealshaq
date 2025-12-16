import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { userSettings } from '../../utils/api';
import { Settings, Save } from 'lucide-react';
import { toast } from 'sonner';

export default function ConsumerSettings({ user, onLogout }) {
  const [autoThreshold, setAutoThreshold] = useState('0');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Load current user settings
    if (user?.auto_favorite_threshold !== undefined) {
      setAutoThreshold(String(user.auto_favorite_threshold));
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await userSettings.updateAutoThreshold({
        auto_favorite_threshold: parseInt(autoThreshold)
      });
      toast.success('Settings saved successfully!');
      
      // Update user in localStorage
      const updatedUser = { ...user, auto_favorite_threshold: parseInt(autoThreshold) };
      localStorage.setItem('user', JSON.stringify(updatedUser));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Settings
          </h1>
          <p className="text-gray-600 mt-1">Manage your DealShaq preferences</p>
        </div>

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
                    <div className="text-sm text-gray-500">I'll manage my favorites manually</div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">How It Works</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• DealShaq tracks items you purchase that aren't in your favorites</li>
                <li>• When you buy an item on {autoThreshold === '0' ? 'N/A (disabled)' : `${autoThreshold} separate days`}, it's automatically added</li>
                <li>• Auto-added items appear with a date stamp in your favorites list</li>
                <li>• You can remove any item (manual or auto-added) at any time</li>
                <li>• This feature runs daily at 11 PM</li>
              </ul>
            </div>

            <Button 
              onClick={handleSave} 
              disabled={saving}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-sm text-gray-500">Email</Label>
              <p className="text-base font-medium">{user?.email}</p>
            </div>
            <div>
              <Label className="text-sm text-gray-500">Name</Label>
              <p className="text-base font-medium">{user?.name}</p>
            </div>
            <div>
              <Label className="text-sm text-gray-500">Role</Label>
              <p className="text-base font-medium">Consumer (DAC)</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </ConsumerLayout>
  );
}
