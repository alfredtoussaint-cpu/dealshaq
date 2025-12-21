import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { retailer } from '../../utils/api';
import { toast } from 'sonner';
import { 
  AlertTriangle, Clock, CheckCircle, XCircle, Rocket, 
  Store, Image, Package, Settings
} from 'lucide-react';

export default function SandboxBanner({ user, onStatusChange }) {
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);

  const storeStatus = user?.store_status;

  useEffect(() => {
    if (storeStatus && storeStatus !== 'live') {
      loadReadiness();
    } else {
      setLoading(false);
    }
  }, [storeStatus]);

  const loadReadiness = async () => {
    try {
      const response = await retailer.launchReadiness();
      setReadiness(response.data);
    } catch (error) {
      console.error('Failed to load launch readiness:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestGoLive = async () => {
    if (!window.confirm('Request to go live? An admin will review your store before it becomes visible to consumers.')) {
      return;
    }
    
    setRequesting(true);
    try {
      await retailer.requestGoLive();
      toast.success('Go-live request submitted! An admin will review your store.');
      loadReadiness();
      if (onStatusChange) onStatusChange();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit go-live request');
    } finally {
      setRequesting(false);
    }
  };

  // Don't show banner for live stores or legacy stores without status
  if (!storeStatus || storeStatus === 'live') {
    return null;
  }

  if (loading) {
    return null;
  }

  // Status-specific rendering
  if (storeStatus === 'pending_approval') {
    return (
      <div className="bg-orange-500 text-white px-4 py-3 rounded-lg mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Clock className="w-5 h-5" />
            <div>
              <p className="font-medium">Registration Pending Approval</p>
              <p className="text-sm text-orange-100">An admin is reviewing your application. You'll be notified once approved.</p>
            </div>
          </div>
          <Badge className="bg-orange-600">Pending</Badge>
        </div>
      </div>
    );
  }

  if (storeStatus === 'pending_live') {
    return (
      <div className="bg-blue-500 text-white px-4 py-3 rounded-lg mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Rocket className="w-5 h-5" />
            <div>
              <p className="font-medium">Go-Live Request Submitted</p>
              <p className="text-sm text-blue-100">An admin is reviewing your store. You'll go live once approved!</p>
            </div>
          </div>
          <Badge className="bg-blue-600">Under Review</Badge>
        </div>
      </div>
    );
  }

  if (storeStatus === 'rejected') {
    return (
      <div className="bg-red-500 text-white px-4 py-3 rounded-lg mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <XCircle className="w-5 h-5" />
            <div>
              <p className="font-medium">Registration Rejected</p>
              <p className="text-sm text-red-100">
                {user?.rejection_reason || 'Your application was not approved. Please contact support.'}
              </p>
            </div>
          </div>
          <Badge className="bg-red-600">Rejected</Badge>
        </div>
      </div>
    );
  }

  if (storeStatus === 'suspended') {
    return (
      <div className="bg-gray-700 text-white px-4 py-3 rounded-lg mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <p className="font-medium">Store Suspended</p>
              <p className="text-sm text-gray-300">Your store has been suspended. Please contact support.</p>
            </div>
          </div>
          <Badge className="bg-gray-600">Suspended</Badge>
        </div>
      </div>
    );
  }

  // Sandbox mode - show checklist and go-live button
  if (storeStatus === 'sandbox') {
    const checklistItems = [
      { key: 'store_hours_configured', label: 'Store hours configured', icon: Settings, required: true },
      { key: 'logo_uploaded', label: 'Store logo uploaded', icon: Image, required: true },
      { key: 'minimum_items_posted', label: `At least 2 items posted (qty ≥ 5)`, icon: Package, required: true },
    ];

    const completedCount = checklistItems.filter(item => readiness?.[item.key]).length;
    const totalRequired = checklistItems.filter(item => item.required).length;
    const progressPercent = (completedCount / totalRequired) * 100;

    return (
      <Card className="bg-yellow-50 border-yellow-300 mb-6">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="bg-yellow-500 p-2 rounded-lg">
                <Store className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-yellow-800 flex items-center">
                  🧪 SANDBOX MODE
                  <Badge className="ml-2 bg-yellow-500">Testing</Badge>
                </h3>
                <p className="text-sm text-yellow-700">
                  Your store is not visible to consumers. Complete the checklist to go live.
                </p>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-yellow-700 mb-1">
              <span>Launch Readiness</span>
              <span>{completedCount}/{totalRequired} completed</span>
            </div>
            <Progress value={progressPercent} className="h-2 bg-yellow-200" />
          </div>

          {/* Checklist */}
          <div className="space-y-2 mb-4">
            {checklistItems.map((item) => {
              const isComplete = readiness?.[item.key];
              const Icon = item.icon;
              return (
                <div
                  key={item.key}
                  className={`flex items-center space-x-2 p-2 rounded ${
                    isComplete ? 'bg-green-100 text-green-800' : 'bg-white text-gray-600'
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <XCircle className="w-4 h-4 text-gray-400" />
                  )}
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{item.label}</span>
                  {item.required && !isComplete && (
                    <Badge variant="outline" className="text-xs ml-auto">Required</Badge>
                  )}
                </div>
              );
            })}
          </div>

          {/* Items Info */}
          {readiness && (
            <p className="text-xs text-yellow-700 mb-4">
              Current items with qty ≥ 5: <strong>{readiness.items_count}</strong> / {readiness.items_required} required
            </p>
          )}

          {/* Go Live Button */}
          <Button
            onClick={handleRequestGoLive}
            disabled={!readiness?.ready_to_go_live || requesting}
            className={`w-full ${
              readiness?.ready_to_go_live 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            <Rocket className="w-4 h-4 mr-2" />
            {requesting ? 'Submitting...' : readiness?.ready_to_go_live ? 'Request to Go Live' : 'Complete Checklist to Go Live'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return null;
}
