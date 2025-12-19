import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Store, MapPin, Plus, X, Navigation, Settings2, AlertCircle, CheckCircle, Search, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import ConsumerLayout from './ConsumerLayout';
import { dacRetailers, drlp } from '../../utils/api';

export default function ConsumerRetailers({ user, onLogout }) {
  const [retailers, setRetailers] = useState([]);
  const [availableRetailers, setAvailableRetailers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dacsaiRad, setDacsaiRad] = useState(user?.dacsai_rad || 5.0);
  const [hasDeliveryLocation, setHasDeliveryLocation] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [pendingRadius, setPendingRadius] = useState(dacsaiRad);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadRetailers();
    loadAvailableRetailers();
  }, []);

  const loadRetailers = async () => {
    try {
      setLoading(true);
      const response = await dacRetailers.list();
      const data = response.data;
      
      // Filter out manually_removed retailers for display
      const activeRetailers = (data.retailers || []).filter(r => !r.manually_removed);
      setRetailers(activeRetailers);
      setDacsaiRad(data.dacsai_rad || 5.0);
      setPendingRadius(data.dacsai_rad || 5.0);
      setHasDeliveryLocation(!!data.dacsai_center);
    } catch (error) {
      console.error('Failed to load retailers:', error);
      toast.error('Failed to load your retailer list');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableRetailers = async () => {
    try {
      const response = await drlp.locations();
      setAvailableRetailers(response.data || []);
    } catch (error) {
      console.error('Failed to load available retailers:', error);
    }
  };

  const handleAddRetailer = async (drlpId, drlpName) => {
    try {
      setUpdating(true);
      await dacRetailers.add(drlpId);
      toast.success(`${drlpName} that is domiciled outside your shopping area of interest has been added to your retailer list.`);
      setAddDialogOpen(false);
      loadRetailers();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to add retailer';
      toast.error(message);
    } finally {
      setUpdating(false);
    }
  };

  const handleRemoveRetailer = async (drlpId, drlpName, insideDacsai) => {
    try {
      setUpdating(true);
      await dacRetailers.remove(drlpId);
      const locationText = insideDacsai 
        ? 'that is domiciled within your shopping area of interest has been removed from'
        : 'that is domiciled outside your shopping area of interest has been removed from';
      toast.success(`${drlpName} ${locationText} your retailer list. You'll no longer receive notifications from this store.`);
      loadRetailers();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to remove retailer';
      toast.error(message);
    } finally {
      setUpdating(false);
    }
  };

  const handleUpdateRadius = async () => {
    if (!hasDeliveryLocation) {
      toast.error('Please set your delivery location in Settings first');
      return;
    }
    
    try {
      setUpdating(true);
      const response = await dacRetailers.updateDacsai(pendingRadius);
      setDacsaiRad(pendingRadius);
      toast.success(`Shopping area updated to ${pendingRadius} miles. ${response.data.retailers_count} retailers in range.`);
      setSettingsDialogOpen(false);
      loadRetailers();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to update shopping area';
      toast.error(message);
    } finally {
      setUpdating(false);
    }
  };

  // Filter retailers not already in the list for "Add" dialog
  // A retailer is available to add if:
  // 1. Not in the list at all, OR
  // 2. In the list but marked as manually_removed (can be re-added)
  const retailersNotInList = availableRetailers.filter(
    ar => {
      const existingRetailer = retailers.find(r => r.drlp_id === (ar.user_id || ar.drlp_id));
      // Available if not in list OR if in list but manually removed
      return !existingRetailer || existingRetailer.manually_removed;
    }
  );

  const filteredAvailable = retailersNotInList.filter(r =>
    r.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.address?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Separate retailers by type
  const insideDacsai = retailers.filter(r => r.inside_dacsai && !r.manually_added);
  const manuallyAdded = retailers.filter(r => r.manually_added);
  const manuallyRemoved = retailers.filter(r => r.manually_removed);

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
            <h1 className="text-2xl font-bold text-gray-900">My Retailers</h1>
            <p className="text-gray-600 mt-1">
              Manage which stores you receive deal notifications from
            </p>
          </div>
          <div className="flex gap-2">
            <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Settings2 className="w-4 h-4 mr-2" />
                  DACSAI: {dacsaiRad} mi
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Shopping Area Settings</DialogTitle>
                  <DialogDescription>
                    Adjust your DACSAI (Shopping Area of Interest) radius to control which retailers are automatically included.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-6 py-4">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">DACSAI Radius</span>
                      <span className="text-lg font-bold text-emerald-600">{pendingRadius} miles</span>
                    </div>
                    <Slider
                      value={[pendingRadius]}
                      onValueChange={(value) => setPendingRadius(value[0])}
                      min={0.1}
                      max={9.9}
                      step={0.1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>0.1 mi</span>
                      <span>9.9 mi</span>
                    </div>
                  </div>
                  {!hasDeliveryLocation && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        You need to set your delivery location in Settings before updating your shopping area.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSettingsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleUpdateRadius} 
                    disabled={updating || !hasDeliveryLocation}
                  >
                    {updating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    Update Radius
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Retailer
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>Add a Retailer</DialogTitle>
                  <DialogDescription>
                    Add retailers outside your shopping area to receive their notifications.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      placeholder="Search retailers..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {filteredAvailable.length === 0 ? (
                      <p className="text-center text-gray-500 py-4">
                        {searchTerm ? 'No retailers found' : 'All available retailers are in your list'}
                      </p>
                    ) : (
                      filteredAvailable.map((retailer) => (
                        <div
                          key={retailer.user_id || retailer.drlp_id}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                        >
                          <div className="flex items-center gap-3">
                            <div className="bg-emerald-100 p-2 rounded-lg">
                              <Store className="w-4 h-4 text-emerald-600" />
                            </div>
                            <div>
                              <p className="font-medium text-sm">{retailer.name}</p>
                              <p className="text-xs text-gray-500">{retailer.address}</p>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAddRetailer(retailer.user_id || retailer.drlp_id, retailer.name || retailer.drlp_name)}
                            disabled={updating}
                          >
                            {updating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* No Delivery Location Warning */}
        {!hasDeliveryLocation && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Set your delivery location</strong> in Settings to automatically discover nearby retailers within your DACSAI.
            </AlertDescription>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-emerald-100 p-2 rounded-lg">
                  <Store className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{retailers.length}</p>
                  <p className="text-sm text-gray-500">Active Retailers</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Navigation className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{dacsaiRad} mi</p>
                  <p className="text-sm text-gray-500">DACSAI Radius</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-purple-100 p-2 rounded-lg">
                  <Plus className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{manuallyAdded.length}</p>
                  <p className="text-sm text-gray-500">Manually Added</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-red-100 p-2 rounded-lg">
                  <X className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{manuallyRemoved.length}</p>
                  <p className="text-sm text-gray-500">Manually Removed</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Retailers List */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList>
            <TabsTrigger value="all">All ({retailers.length})</TabsTrigger>
            <TabsTrigger value="local">In DACSAI ({insideDacsai.length})</TabsTrigger>
            <TabsTrigger value="added">Manually Added ({manuallyAdded.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-4">
            <RetailersList 
              retailers={retailers} 
              onRemove={handleRemoveRetailer}
              updating={updating}
            />
          </TabsContent>

          <TabsContent value="local" className="mt-4">
            <RetailersList 
              retailers={insideDacsai} 
              onRemove={handleRemoveRetailer}
              updating={updating}
              emptyMessage="No retailers found in your shopping area"
            />
          </TabsContent>

          <TabsContent value="added" className="mt-4">
            <RetailersList 
              retailers={manuallyAdded} 
              onRemove={handleRemoveRetailer}
              updating={updating}
              emptyMessage="You haven't manually added any retailers"
            />
          </TabsContent>
        </Tabs>
      </div>
    </ConsumerLayout>
  );
}

function RetailersList({ retailers, onRemove, updating, emptyMessage = 'No retailers found' }) {
  if (retailers.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Store className="w-12 h-12 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">{emptyMessage}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {retailers.map((retailer) => (
        <Card key={retailer.drlp_id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="bg-emerald-100 p-3 rounded-lg">
                  <Store className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{retailer.drlp_name}</h3>
                    {retailer.manually_added && (
                      <Badge variant="secondary" className="text-xs">
                        Added
                      </Badge>
                    )}
                    {retailer.inside_dacsai && !retailer.manually_added && (
                      <Badge variant="outline" className="text-xs text-emerald-600 border-emerald-200">
                        In DACSAI
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                    <MapPin className="w-3 h-3" />
                    <span>{retailer.distance?.toFixed(1) || '?'} miles away</span>
                  </div>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={() => onRemove(retailer.drlp_id, retailer.drlp_name, retailer.inside_dacsai)}
                disabled={updating}
              >
                {updating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <X className="w-4 h-4" />
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
