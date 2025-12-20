import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { admin } from '../../utils/api';
import { toast } from 'sonner';
import { 
  Users, Mail, Search, Eye, UserX, UserCheck, Plus, 
  MapPin, ShoppingBag, Store, Calendar, AlertTriangle 
} from 'lucide-react';

export default function AdminUsers({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetails, setUserDetails] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showCreateAdminModal, setShowCreateAdminModal] = useState(false);
  const [newAdmin, setNewAdmin] = useState({ name: '', email: '', password: '' });
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    filterUsers();
  }, [users, searchTerm, roleFilter]);

  const loadUsers = async () => {
    try {
      const response = await admin.users();
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const filterUsers = () => {
    let filtered = [...users];
    
    // Filter by role
    if (roleFilter !== 'all') {
      filtered = filtered.filter(u => u.role === roleFilter);
    }
    
    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(u => 
        u.name?.toLowerCase().includes(term) ||
        u.email?.toLowerCase().includes(term)
      );
    }
    
    setFilteredUsers(filtered);
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      DAC: 'bg-emerald-500',
      DRLP: 'bg-blue-500',
      Admin: 'bg-purple-500',
    };
    return colors[role] || 'bg-gray-500';
  };

  const getStatusBadge = (status) => {
    if (status === 'suspended') {
      return <Badge className="bg-red-500 ml-2">Suspended</Badge>;
    }
    return null;
  };

  const handleViewDetails = async (userId) => {
    try {
      setSelectedUser(userId);
      setShowDetailsModal(true);
      const response = await admin.userDetails(userId);
      setUserDetails(response.data);
    } catch (error) {
      toast.error('Failed to load user details');
      setShowDetailsModal(false);
    }
  };

  const handleToggleStatus = async (userId, currentStatus) => {
    const newStatus = currentStatus === 'suspended' ? 'active' : 'suspended';
    const action = newStatus === 'suspended' ? 'suspend' : 'activate';
    
    if (!window.confirm(`Are you sure you want to ${action} this user?`)) {
      return;
    }
    
    setActionLoading(true);
    try {
      await admin.updateUserStatus(userId, newStatus);
      toast.success(`User ${action}d successfully`);
      
      // Update local state
      setUsers(users.map(u => 
        u.id === userId ? { ...u, account_status: newStatus } : u
      ));
      
      if (userDetails && userDetails.id === userId) {
        setUserDetails({ ...userDetails, account_status: newStatus });
      }
    } catch (error) {
      toast.error(`Failed to ${action} user`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateAdmin = async () => {
    if (!newAdmin.name || !newAdmin.email || !newAdmin.password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    if (newAdmin.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    
    setActionLoading(true);
    try {
      await admin.createAdmin({
        name: newAdmin.name,
        email: newAdmin.email,
        password: newAdmin.password,
        role: 'Admin'
      });
      toast.success('Admin account created successfully');
      setShowCreateAdminModal(false);
      setNewAdmin({ name: '', email: '', password: '' });
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create admin account');
    } finally {
      setActionLoading(false);
    }
  };

  const usersByRole = {
    DAC: filteredUsers.filter(u => u.role === 'DAC'),
    DRLP: filteredUsers.filter(u => u.role === 'DRLP'),
    Admin: filteredUsers.filter(u => u.role === 'Admin'),
  };

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
              User Management
            </h1>
            <p className="text-gray-600 mt-1">View and manage all platform users</p>
          </div>
          <Button onClick={() => setShowCreateAdminModal(true)} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="w-4 h-4 mr-2" />
            Create Admin
          </Button>
        </div>

        {/* Search and Filter */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="Filter by role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  <SelectItem value="DAC">Consumers (DAC)</SelectItem>
                  <SelectItem value="DRLP">Retailers (DRLP)</SelectItem>
                  <SelectItem value="Admin">Administrators</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Showing {filteredUsers.length} of {users.length} users
            </p>
          </CardContent>
        </Card>

        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Loading users...</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Consumers */}
            {(roleFilter === 'all' || roleFilter === 'DAC') && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5 text-emerald-600" />
                    <span>Consumers (DAC)</span>
                    <Badge className="ml-auto bg-emerald-500">{usersByRole.DAC.length}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {usersByRole.DAC.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">No consumers found</p>
                  ) : (
                    <div className="space-y-2">
                      {usersByRole.DAC.map((u) => (
                        <div
                          key={u.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                        >
                          <div className="flex-1">
                            <div className="flex items-center">
                              <p className="font-medium text-gray-900">{u.name}</p>
                              {getStatusBadge(u.account_status)}
                            </div>
                            <p className="text-sm text-gray-500 flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {u.email}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewDetails(u.id)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleToggleStatus(u.id, u.account_status)}
                              className={u.account_status === 'suspended' ? 'text-green-600' : 'text-red-600'}
                            >
                              {u.account_status === 'suspended' ? (
                                <UserCheck className="w-4 h-4" />
                              ) : (
                                <UserX className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Retailers */}
            {(roleFilter === 'all' || roleFilter === 'DRLP') && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Store className="w-5 h-5 text-blue-600" />
                    <span>Retailers (DRLP)</span>
                    <Badge className="ml-auto bg-blue-500">{usersByRole.DRLP.length}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {usersByRole.DRLP.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">No retailers found</p>
                  ) : (
                    <div className="space-y-2">
                      {usersByRole.DRLP.map((u) => (
                        <div
                          key={u.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                        >
                          <div className="flex-1">
                            <div className="flex items-center">
                              <p className="font-medium text-gray-900">{u.name}</p>
                              {getStatusBadge(u.account_status)}
                            </div>
                            <p className="text-sm text-gray-500 flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {u.email}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleViewDetails(u.id)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleToggleStatus(u.id, u.account_status)}
                              className={u.account_status === 'suspended' ? 'text-green-600' : 'text-red-600'}
                            >
                              {u.account_status === 'suspended' ? (
                                <UserCheck className="w-4 h-4" />
                              ) : (
                                <UserX className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Admins */}
            {(roleFilter === 'all' || roleFilter === 'Admin') && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5 text-purple-600" />
                    <span>Administrators</span>
                    <Badge className="ml-auto bg-purple-500">{usersByRole.Admin.length}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {usersByRole.Admin.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">No admins found</p>
                  ) : (
                    <div className="space-y-2">
                      {usersByRole.Admin.map((u) => (
                        <div
                          key={u.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-gray-900">{u.name}</p>
                            <p className="text-sm text-gray-500 flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {u.email}
                            </p>
                          </div>
                          <Badge className={getRoleBadgeColor(u.role)}>{u.role}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>

      {/* User Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
          </DialogHeader>
          {userDetails ? (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-medium">{userDetails.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{userDetails.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Role</p>
                  <Badge className={getRoleBadgeColor(userDetails.role)}>{userDetails.role}</Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <Badge className={userDetails.account_status === 'suspended' ? 'bg-red-500' : 'bg-green-500'}>
                    {userDetails.account_status || 'Active'}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Joined</p>
                  <p className="font-medium flex items-center">
                    <Calendar className="w-3 h-3 mr-1" />
                    {userDetails.created_at ? new Date(userDetails.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>

              {/* DAC-specific info */}
              {userDetails.role === 'DAC' && (
                <>
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                      <MapPin className="w-4 h-4 mr-2" />
                      Delivery Location
                    </h4>
                    {userDetails.delivery_location ? (
                      <p className="text-sm text-gray-600">{userDetails.delivery_location.address}</p>
                    ) : (
                      <p className="text-sm text-gray-400">Not set</p>
                    )}
                  </div>
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                      <ShoppingBag className="w-4 h-4 mr-2" />
                      Order History
                    </h4>
                    <p className="text-sm text-gray-600">{userDetails.order_count || 0} orders placed</p>
                  </div>
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2">Retailer List</h4>
                    {userDetails.retailer_list?.length > 0 ? (
                      <div className="space-y-1">
                        {userDetails.retailer_list.map((r, i) => (
                          <p key={i} className="text-sm text-gray-600">• {r.drlp_name}</p>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">No retailers in list</p>
                    )}
                  </div>
                </>
              )}

              {/* DRLP-specific info */}
              {userDetails.role === 'DRLP' && (
                <>
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                      <MapPin className="w-4 h-4 mr-2" />
                      Store Location
                    </h4>
                    {userDetails.location ? (
                      <p className="text-sm text-gray-600">{userDetails.location.address}</p>
                    ) : (
                      <p className="text-sm text-gray-400">Not set</p>
                    )}
                  </div>
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2">Active Items ({userDetails.item_count || 0})</h4>
                    {userDetails.items?.length > 0 ? (
                      <div className="max-h-40 overflow-y-auto space-y-1">
                        {userDetails.items.slice(0, 10).map((item, i) => (
                          <div key={i} className="flex justify-between text-sm">
                            <span className="text-gray-600">{item.name}</span>
                            <span className="text-emerald-600">${item.deal_price?.toFixed(2)}</span>
                          </div>
                        ))}
                        {userDetails.items.length > 10 && (
                          <p className="text-xs text-gray-400">+{userDetails.items.length - 10} more items</p>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">No active items</p>
                    )}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-gray-500">Loading...</div>
          )}
          <DialogFooter>
            {userDetails && userDetails.role !== 'Admin' && (
              <Button
                variant={userDetails.account_status === 'suspended' ? 'default' : 'destructive'}
                onClick={() => handleToggleStatus(userDetails.id, userDetails.account_status)}
                disabled={actionLoading}
              >
                {userDetails.account_status === 'suspended' ? (
                  <>
                    <UserCheck className="w-4 h-4 mr-2" />
                    Activate Account
                  </>
                ) : (
                  <>
                    <UserX className="w-4 h-4 mr-2" />
                    Suspend Account
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

      {/* Create Admin Modal */}
      <Dialog open={showCreateAdminModal} onOpenChange={setShowCreateAdminModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Admin Account</DialogTitle>
            <DialogDescription>
              Create a new administrator account with full system access.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Name</label>
              <Input
                value={newAdmin.name}
                onChange={(e) => setNewAdmin({ ...newAdmin, name: e.target.value })}
                placeholder="Admin name"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Email</label>
              <Input
                type="email"
                value={newAdmin.email}
                onChange={(e) => setNewAdmin({ ...newAdmin, email: e.target.value })}
                placeholder="admin@example.com"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Password</label>
              <Input
                type="password"
                value={newAdmin.password}
                onChange={(e) => setNewAdmin({ ...newAdmin, password: e.target.value })}
                placeholder="Minimum 8 characters"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateAdminModal(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateAdmin} 
              disabled={actionLoading}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {actionLoading ? 'Creating...' : 'Create Admin'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminLayout>
  );
}
