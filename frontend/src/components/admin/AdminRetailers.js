import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { admin } from '../../utils/api';
import { toast } from 'sonner';
import { 
  Store, Search, Eye, UserX, UserCheck, MapPin, Package, 
  ShoppingBag, DollarSign, Users, TrendingUp, Calendar, Clock
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line
} from 'recharts';

export default function AdminRetailers({ user, onLogout }) {
  const [retailers, setRetailers] = useState([]);
  const [filteredRetailers, setFilteredRetailers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRetailer, setSelectedRetailer] = useState(null);
  const [retailerDetails, setRetailerDetails] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('list');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterRetailers();
  }, [retailers, searchTerm]);

  const loadData = async () => {
    try {
      const [retailersRes, analyticsRes] = await Promise.all([
        admin.retailers(),
        admin.retailerAnalytics()
      ]);
      setRetailers(retailersRes.data);
      setAnalytics(analyticsRes.data);
    } catch (error) {
      toast.error('Failed to load retailer data');
    } finally {
      setLoading(false);
    }
  };

  const filterRetailers = () => {
    if (!searchTerm) {
      setFilteredRetailers(retailers);
      return;
    }
    const term = searchTerm.toLowerCase();
    setFilteredRetailers(retailers.filter(r => 
      r.name?.toLowerCase().includes(term) ||
      r.store_name?.toLowerCase().includes(term) ||
      r.email?.toLowerCase().includes(term) ||
      r.address?.toLowerCase().includes(term)
    ));
  };

  const handleViewDetails = async (retailerId) => {
    try {
      setSelectedRetailer(retailerId);
      setShowDetailsModal(true);
      const response = await admin.retailerDetails(retailerId);
      setRetailerDetails(response.data);
    } catch (error) {
      toast.error('Failed to load retailer details');
      setShowDetailsModal(false);
    }
  };

  const handleToggleStatus = async (retailerId, currentStatus) => {
    const newStatus = currentStatus === 'suspended' ? 'active' : 'suspended';
    const action = newStatus === 'suspended' ? 'suspend' : 'activate';
    
    if (!window.confirm(`Are you sure you want to ${action} this retailer? ${newStatus === 'suspended' ? 'All their items will be marked as unavailable.' : 'Their items will be restored.'}`)) {
      return;
    }
    
    setActionLoading(true);
    try {
      await admin.updateRetailerStatus(retailerId, newStatus);
      toast.success(`Retailer ${action}d successfully`);
      
      setRetailers(retailers.map(r => 
        r.id === retailerId ? { ...r, account_status: newStatus } : r
      ));
      
      if (retailerDetails && retailerDetails.id === retailerId) {
        setRetailerDetails({ ...retailerDetails, account_status: newStatus });
      }
    } catch (error) {
      toast.error(`Failed to ${action} retailer`);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'suspended') {
      return <Badge className="bg-red-500">Suspended</Badge>;
    }
    return <Badge className="bg-green-500">Active</Badge>;
  };

  // Summary stats
  const totalRetailers = retailers.length;
  const activeRetailers = retailers.filter(r => r.active_items > 0).length;
  const suspendedRetailers = retailers.filter(r => r.account_status === 'suspended').length;
  const totalItems = retailers.reduce((sum, r) => sum + r.active_items, 0);

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl p-8 text-white shadow-lg">
          <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            Retailer Management
          </h2>
          <p className="text-blue-50 text-lg">Monitor and manage all DRLPs on the platform</p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="list">Retailer List</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          {/* Retailer List Tab */}
          <TabsContent value="list" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-blue-100 p-3 rounded-lg">
                      <Store className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Retailers</p>
                      <p className="text-2xl font-bold text-gray-900">{totalRetailers}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-green-100 p-3 rounded-lg">
                      <TrendingUp className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Active Retailers</p>
                      <p className="text-2xl font-bold text-green-600">{activeRetailers}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-red-100 p-3 rounded-lg">
                      <UserX className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Suspended</p>
                      <p className="text-2xl font-bold text-red-600">{suspendedRetailers}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-purple-100 p-3 rounded-lg">
                      <Package className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Items</p>
                      <p className="text-2xl font-bold text-purple-600">{totalItems}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Search */}
            <Card>
              <CardContent className="pt-6">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search by name, email, or address..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Showing {filteredRetailers.length} of {retailers.length} retailers
                </p>
              </CardContent>
            </Card>

            {/* Retailers List */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Store className="w-5 h-5 text-blue-600" />
                  <span>All Retailers (DRLPs)</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <p className="text-center text-gray-500 py-8">Loading retailers...</p>
                ) : filteredRetailers.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No retailers found</p>
                ) : (
                  <div className="space-y-3">
                    {filteredRetailers.map((retailer) => (
                      <div
                        key={retailer.id}
                        className={`p-4 rounded-lg border transition hover:shadow-md ${
                          retailer.account_status === 'suspended'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <h4 className="font-medium text-gray-900">{retailer.store_name || retailer.name}</h4>
                              {getStatusBadge(retailer.account_status)}
                            </div>
                            <p className="text-sm text-gray-500 mb-2">{retailer.email}</p>
                            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                              <span className="flex items-center">
                                <MapPin className="w-3 h-3 mr-1" />
                                {retailer.address || 'No address'}
                              </span>
                              <span className="flex items-center">
                                <Package className="w-3 h-3 mr-1" />
                                {retailer.active_items} items
                              </span>
                              <span className="flex items-center">
                                <ShoppingBag className="w-3 h-3 mr-1" />
                                {retailer.total_orders} orders
                              </span>
                              <span className="flex items-center">
                                <DollarSign className="w-3 h-3 mr-1" />
                                ${retailer.total_revenue?.toFixed(2)}
                              </span>
                              <span className="flex items-center">
                                <Users className="w-3 h-3 mr-1" />
                                {retailer.consumer_reach} consumers
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewDetails(retailer.id)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleToggleStatus(retailer.id, retailer.account_status)}
                              className={retailer.account_status === 'suspended' ? 'text-green-600' : 'text-red-600'}
                              disabled={actionLoading}
                            >
                              {retailer.account_status === 'suspended' ? (
                                <UserCheck className="w-4 h-4" />
                              ) : (
                                <UserX className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            {analytics && (
              <>
                {/* Summary Stats */}
                <div className="grid md:grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-4xl font-bold text-blue-600">{analytics.total_retailers}</p>
                        <p className="text-gray-600">Total Retailers</p>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-4xl font-bold text-green-600">{analytics.active_retailers}</p>
                        <p className="text-gray-600">With Active Items</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Top Retailers by Items */}
                {analytics.top_by_items?.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <Package className="w-5 h-5 text-purple-600" />
                        <span>Top Retailers by Active Items</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={analytics.top_by_items} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" tick={{ fontSize: 10 }} />
                          <YAxis 
                            type="category" 
                            dataKey="name" 
                            tick={{ fontSize: 10 }} 
                            width={120}
                          />
                          <Tooltip />
                          <Bar dataKey="items" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                )}

                {/* Top Retailers by Sales */}
                {analytics.top_by_sales?.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <DollarSign className="w-5 h-5 text-green-600" />
                        <span>Top Retailers by Revenue</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={analytics.top_by_sales} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
                          <YAxis 
                            type="category" 
                            dataKey="name" 
                            tick={{ fontSize: 10 }} 
                            width={120}
                          />
                          <Tooltip formatter={(value) => [`$${value}`, 'Revenue']} />
                          <Bar dataKey="revenue" fill="#10b981" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                )}

                {/* Registrations Trend */}
                {analytics.registrations_trend && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <Calendar className="w-5 h-5 text-blue-600" />
                        <span>New Retailer Registrations (Last 30 Days)</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={analytics.registrations_trend}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="date" 
                            tick={{ fontSize: 10 }}
                            tickFormatter={(value) => value.slice(5)}
                          />
                          <YAxis tick={{ fontSize: 10 }} />
                          <Tooltip labelFormatter={(value) => `Date: ${value}`} />
                          <Line 
                            type="monotone" 
                            dataKey="count" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            dot={false}
                            name="Registrations"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Retailer Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Retailer Details</DialogTitle>
          </DialogHeader>
          {retailerDetails ? (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Store Name</p>
                  <p className="font-medium">{retailerDetails.location?.name || retailerDetails.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{retailerDetails.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  {getStatusBadge(retailerDetails.account_status)}
                </div>
                <div>
                  <p className="text-sm text-gray-500">Joined</p>
                  <p className="font-medium flex items-center">
                    <Calendar className="w-3 h-3 mr-1" />
                    {retailerDetails.created_at ? new Date(retailerDetails.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Location Info */}
              {retailerDetails.location && (
                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    Store Location
                  </h4>
                  <p className="text-sm text-gray-600">{retailerDetails.location.address || 'No address set'}</p>
                  {retailerDetails.location.operating_hours && (
                    <p className="text-sm text-gray-500 mt-1 flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {retailerDetails.location.operating_hours}
                    </p>
                  )}
                </div>
              )}

              {/* Performance Stats */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-3">Performance Metrics</h4>
                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-purple-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-purple-600">{retailerDetails.active_items_count}</p>
                    <p className="text-xs text-gray-600">Active Items</p>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-blue-600">{retailerDetails.total_orders}</p>
                    <p className="text-xs text-gray-600">Total Orders</p>
                  </div>
                  <div className="bg-green-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-600">${retailerDetails.total_revenue?.toFixed(2)}</p>
                    <p className="text-xs text-gray-600">Revenue</p>
                  </div>
                  <div className="bg-orange-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-orange-600">{retailerDetails.consumer_reach}</p>
                    <p className="text-xs text-gray-600">Consumers</p>
                  </div>
                </div>
              </div>

              {/* Active Items */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-2">Active Items ({retailerDetails.active_items_count})</h4>
                {retailerDetails.items?.length > 0 ? (
                  <div className="max-h-40 overflow-y-auto space-y-1">
                    {retailerDetails.items.filter(i => i.status === 'available').slice(0, 10).map((item, i) => (
                      <div key={i} className="flex justify-between text-sm p-2 bg-gray-50 rounded">
                        <span className="text-gray-700">{item.name}</span>
                        <span className="text-emerald-600 font-medium">${item.deal_price?.toFixed(2)}</span>
                      </div>
                    ))}
                    {retailerDetails.active_items_count > 10 && (
                      <p className="text-xs text-gray-400 text-center">+{retailerDetails.active_items_count - 10} more items</p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">No active items</p>
                )}
              </div>

              {/* Consumers */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-2">Consumers with this Retailer ({retailerDetails.consumer_reach})</h4>
                {retailerDetails.consumers?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {retailerDetails.consumers.slice(0, 10).map((consumer, i) => (
                      <Badge key={i} variant="outline" className="bg-gray-50">
                        {consumer.name}
                      </Badge>
                    ))}
                    {retailerDetails.consumer_reach > 10 && (
                      <Badge variant="outline" className="bg-gray-100">
                        +{retailerDetails.consumer_reach - 10} more
                      </Badge>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">No consumers have this retailer in their list</p>
                )}
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-gray-500">Loading...</div>
          )}
          <DialogFooter>
            {retailerDetails && (
              <Button
                variant={retailerDetails.account_status === 'suspended' ? 'default' : 'destructive'}
                onClick={() => handleToggleStatus(retailerDetails.id, retailerDetails.account_status)}
                disabled={actionLoading}
              >
                {retailerDetails.account_status === 'suspended' ? (
                  <>
                    <UserCheck className="w-4 h-4 mr-2" />
                    Activate Retailer
                  </>
                ) : (
                  <>
                    <UserX className="w-4 h-4 mr-2" />
                    Suspend Retailer
                  </>
                )}
              </Button>
            )}
            <Button variant="outline" onClick={() => setShowDetailsModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminLayout>
  );
}
