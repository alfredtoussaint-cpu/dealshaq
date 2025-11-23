import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { admin } from '../../utils/api';
import { toast } from 'sonner';
import { Users, Mail } from 'lucide-react';

export default function AdminUsers({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

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

  const getRoleBadgeColor = (role) => {
    const colors = {
      DAC: 'bg-emerald-500',
      DRLP: 'bg-blue-500',
      Admin: 'bg-purple-500',
    };
    return colors[role] || 'bg-gray-500';
  };

  const usersByRole = {
    DAC: users.filter(u => u.role === 'DAC'),
    DRLP: users.filter(u => u.role === 'DRLP'),
    Admin: users.filter(u => u.role === 'Admin'),
  };

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            User Management
          </h1>
          <p className="text-gray-600 mt-1">View and manage all platform users</p>
        </div>

        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Loading users...</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Consumers */}
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
                  <p className="text-gray-500 text-center py-4">No consumers registered</p>
                ) : (
                  <div className="space-y-2">
                    {usersByRole.DAC.map((u) => (
                      <div
                        key={u.id}
                        data-testid={`user-${u.id}`}
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

            {/* Retailers */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Users className="w-5 h-5 text-blue-600" />
                  <span>Retailers (DRLP)</span>
                  <Badge className="ml-auto bg-blue-500">{usersByRole.DRLP.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {usersByRole.DRLP.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No retailers registered</p>
                ) : (
                  <div className="space-y-2">
                    {usersByRole.DRLP.map((u) => (
                      <div
                        key={u.id}
                        data-testid={`user-${u.id}`}
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

            {/* Admins */}
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
                  <p className="text-gray-500 text-center py-4">No admins registered</p>
                ) : (
                  <div className="space-y-2">
                    {usersByRole.Admin.map((u) => (
                      <div
                        key={u.id}
                        data-testid={`user-${u.id}`}
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
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
