import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { admin } from '../../utils/api';
import { toast } from 'sonner';
import { 
  ClipboardCheck, Clock, CheckCircle, XCircle, Store, Mail, 
  Phone, MapPin, Calendar, Package, Eye, AlertTriangle, Rocket
} from 'lucide-react';

export default function AdminApprovals({ user, onLogout }) {
  const [pendingData, setPendingData] = useState({ pending_registration: [], pending_go_live: [], total_pending: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedRetailer, setSelectedRetailer] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [retailerDetails, setRetailerDetails] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [rejectType, setRejectType] = useState(''); // 'registration' or 'go_live'
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('registration');

  useEffect(() => {
    loadPendingApprovals();
  }, []);

  const loadPendingApprovals = async () => {
    try {
      const response = await admin.pendingApprovals();
      setPendingData(response.data);
    } catch (error) {
      toast.error('Failed to load pending approvals');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (retailer) => {
    setSelectedRetailer(retailer);
    setShowDetailsModal(true);
    try {
      const response = await admin.retailerDetails(retailer.id);
      setRetailerDetails(response.data);
    } catch (error) {
      toast.error('Failed to load retailer details');
    }
  };

  const handleApproveRegistration = async (retailerId) => {
    if (!window.confirm('Approve this retailer registration? They will enter sandbox mode.')) return;
    
    setActionLoading(true);
    try {
      await admin.approveRegistration(retailerId);
      toast.success('Registration approved! Retailer is now in sandbox mode.');
      loadPendingApprovals();
      setShowDetailsModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve registration');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApproveGoLive = async (retailerId) => {
    if (!window.confirm('Approve this retailer to go live? Their items will be visible to consumers.')) return;
    
    setActionLoading(true);
    try {
      await admin.approveGoLive(retailerId);
      toast.success('Retailer is now LIVE! Their items are visible to consumers.');
      loadPendingApprovals();
      setShowDetailsModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve go-live request');
    } finally {
      setActionLoading(false);
    }
  };

  const openRejectModal = (retailer, type) => {
    setSelectedRetailer(retailer);
    setRejectType(type);
    setRejectReason('');
    setShowRejectModal(true);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }
    
    setActionLoading(true);
    try {
      if (rejectType === 'registration') {
        await admin.rejectRegistration(selectedRetailer.id, rejectReason);
        toast.success('Registration rejected');
      } else {
        await admin.rejectGoLive(selectedRetailer.id, rejectReason);
        toast.success('Go-live request rejected. Retailer returned to sandbox.');
      }
      loadPendingApprovals();
      setShowRejectModal(false);
      setShowDetailsModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject');
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-amber-600 rounded-2xl p-8 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                Pending Approvals
              </h2>
              <p className="text-orange-50 text-lg">Review and approve retailer applications</p>
            </div>
            {pendingData.total_pending > 0 && (
              <div className="bg-white/20 rounded-full px-4 py-2">
                <span className="text-2xl font-bold">{pendingData.total_pending}</span>
                <span className="ml-2">pending</span>
              </div>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-2 gap-4">
          <Card className={pendingData.pending_registration.length > 0 ? 'border-orange-300 bg-orange-50' : ''}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-orange-100 p-3 rounded-lg">
                  <ClipboardCheck className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Registration Approvals</p>
                  <p className="text-2xl font-bold text-orange-600">{pendingData.pending_registration.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={pendingData.pending_go_live.length > 0 ? 'border-blue-300 bg-blue-50' : ''}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Rocket className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Go-Live Requests</p>
                  <p className="text-2xl font-bold text-blue-600">{pendingData.pending_go_live.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="registration" className="relative">
              Registration
              {pendingData.pending_registration.length > 0 && (
                <Badge className="ml-2 bg-orange-500">{pendingData.pending_registration.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="go_live" className="relative">
              Go-Live
              {pendingData.pending_go_live.length > 0 && (
                <Badge className="ml-2 bg-blue-500">{pendingData.pending_go_live.length}</Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Registration Approvals Tab */}
          <TabsContent value="registration" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <ClipboardCheck className="w-5 h-5 text-orange-600" />
                  <span>New Retailer Registrations</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <p className="text-center text-gray-500 py-8">Loading...</p>
                ) : pendingData.pending_registration.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                    <p className="text-gray-500">No pending registration approvals</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {pendingData.pending_registration.map((retailer) => (
                      <div
                        key={retailer.id}
                        className="p-4 bg-orange-50 rounded-lg border border-orange-200"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <Store className="w-4 h-4 text-orange-600" />
                              <h4 className="font-medium text-gray-900">{retailer.name}</h4>
                              <Badge className="bg-orange-500">Pending</Badge>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mt-2">
                              <span className="flex items-center">
                                <Mail className="w-3 h-3 mr-1" />
                                {retailer.email}
                              </span>
                              <span className="flex items-center">
                                <Calendar className="w-3 h-3 mr-1" />
                                {formatDate(retailer.created_at)}
                              </span>
                              {retailer.business_phone && (
                                <span className="flex items-center">
                                  <Phone className="w-3 h-3 mr-1" />
                                  {retailer.business_phone}
                                </span>
                              )}
                              {retailer.business_address && (
                                <span className="flex items-center">
                                  <MapPin className="w-3 h-3 mr-1" />
                                  {retailer.business_address}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <Button variant="ghost" size="sm" onClick={() => handleViewDetails(retailer)}>
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              className="bg-green-600 hover:bg-green-700"
                              onClick={() => handleApproveRegistration(retailer.id)}
                              disabled={actionLoading}
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => openRejectModal(retailer, 'registration')}
                              disabled={actionLoading}
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Reject
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

          {/* Go-Live Requests Tab */}
          <TabsContent value="go_live" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Rocket className="w-5 h-5 text-blue-600" />
                  <span>Go-Live Requests</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <p className="text-center text-gray-500 py-8">Loading...</p>
                ) : pendingData.pending_go_live.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                    <p className="text-gray-500">No pending go-live requests</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {pendingData.pending_go_live.map((retailer) => (
                      <div
                        key={retailer.id}
                        className="p-4 bg-blue-50 rounded-lg border border-blue-200"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <Store className="w-4 h-4 text-blue-600" />
                              <h4 className="font-medium text-gray-900">{retailer.name}</h4>
                              <Badge className="bg-blue-500">Ready to Go Live</Badge>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mt-2">
                              <span className="flex items-center">
                                <Mail className="w-3 h-3 mr-1" />
                                {retailer.email}
                              </span>
                              <span className="flex items-center">
                                <Package className="w-3 h-3 mr-1" />
                                {retailer.items_count || 0} items posted
                              </span>
                              <span className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                Requested: {formatDate(retailer.go_live_requested_at)}
                              </span>
                              {retailer.store_hours && (
                                <span className="flex items-center text-green-600">
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Store hours set
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <Button variant="ghost" size="sm" onClick={() => handleViewDetails(retailer)}>
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              className="bg-green-600 hover:bg-green-700"
                              onClick={() => handleApproveGoLive(retailer.id)}
                              disabled={actionLoading}
                            >
                              <Rocket className="w-4 h-4 mr-1" />
                              Go Live
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => openRejectModal(retailer, 'go_live')}
                              disabled={actionLoading}
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Reject
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
        </Tabs>
      </div>

      {/* Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Retailer Application Details</DialogTitle>
          </DialogHeader>
          {retailerDetails ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Business Name</p>
                  <p className="font-medium">{retailerDetails.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{retailerDetails.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Business Phone</p>
                  <p className="font-medium">{retailerDetails.business_phone || 'Not provided'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Business Type</p>
                  <p className="font-medium">{retailerDetails.business_type || 'Not specified'}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-500">Business Address</p>
                  <p className="font-medium">{retailerDetails.business_address || 'Not provided'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Registered</p>
                  <p className="font-medium">{formatDate(retailerDetails.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Store Status</p>
                  <Badge className={
                    retailerDetails.store_status === 'pending_approval' ? 'bg-orange-500' :
                    retailerDetails.store_status === 'pending_live' ? 'bg-blue-500' :
                    retailerDetails.store_status === 'sandbox' ? 'bg-yellow-500' :
                    retailerDetails.store_status === 'live' ? 'bg-green-500' : 'bg-gray-500'
                  }>
                    {retailerDetails.store_status?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
                  </Badge>
                </div>
              </div>

              {/* Items Preview */}
              {retailerDetails.items?.length > 0 && (
                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-2">Posted Items ({retailerDetails.items.length})</h4>
                  <div className="max-h-40 overflow-y-auto space-y-1">
                    {retailerDetails.items.slice(0, 10).map((item, i) => (
                      <div key={i} className="flex justify-between text-sm p-2 bg-gray-50 rounded">
                        <span>{item.name}</span>
                        <span className="text-gray-500">Qty: {item.quantity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-8">Loading details...</p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailsModal(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Modal */}
      <Dialog open={showRejectModal} onOpenChange={setShowRejectModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              <span>Reject {rejectType === 'registration' ? 'Registration' : 'Go-Live Request'}</span>
            </DialogTitle>
            <DialogDescription>
              Please provide a reason for rejection. This will be visible to the retailer.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Enter rejection reason..."
              rows={4}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectModal(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleReject} disabled={actionLoading}>
              {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminLayout>
  );
}
