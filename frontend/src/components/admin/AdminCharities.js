import { useState, useEffect } from 'react';
import AdminLayout from './AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { admin } from '../../utils/api';
import { toast } from 'sonner';
import { Heart, DollarSign, Users, TrendingUp } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899'];

export default function AdminCharities({ user, onLogout }) {
  const [charities, setCharities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCharities();
  }, []);

  const loadCharities = async () => {
    try {
      const response = await admin.charities();
      setCharities(response.data);
    } catch (error) {
      toast.error('Failed to load charities');
    } finally {
      setLoading(false);
    }
  };

  const totalDonations = charities.reduce((sum, c) => sum + c.total_donations, 0);
  const totalDAC = charities.reduce((sum, c) => sum + c.donations_dac, 0);
  const totalDRLP = charities.reduce((sum, c) => sum + c.donations_drlp, 0);
  const totalRoundup = charities.reduce((sum, c) => sum + c.donations_roundup, 0);

  const pieData = charities
    .filter(c => c.total_donations > 0)
    .map(c => ({
      name: c.name,
      value: c.total_donations
    }));

  const breakdownData = [
    { name: 'Consumer (DAC)', value: totalDAC, color: '#10b981' },
    { name: 'Retailer (DRLP)', value: totalDRLP, color: '#3b82f6' },
    { name: 'Round-up', value: totalRoundup, color: '#f59e0b' },
  ].filter(d => d.value > 0);

  return (
    <AdminLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-8 text-white shadow-lg">
          <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            Charity Management
          </h2>
          <p className="text-emerald-50 text-lg">Track donations and charity impact</p>
        </div>

        {/* Summary Stats */}
        <div className="grid md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-emerald-100 p-3 rounded-lg">
                  <Heart className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Charities</p>
                  <p className="text-2xl font-bold text-gray-900">{charities.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-green-100 p-3 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Donations</p>
                  <p className="text-2xl font-bold text-green-600">${totalDonations.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">DAC Contributions</p>
                  <p className="text-2xl font-bold text-blue-600">${totalDAC.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="bg-orange-100 p-3 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Round-up Total</p>
                  <p className="text-2xl font-bold text-orange-600">${totalRoundup.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        {(pieData.length > 0 || breakdownData.length > 0) && (
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Donations by Charity */}
            {pieData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Donations by Charity</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => 
                          percent > 0.1 ? `${name.slice(0, 15)}...` : ''
                        }
                        labelLine={false}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Donation Source Breakdown */}
            {breakdownData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Donation Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={breakdownData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                      >
                        {breakdownData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Charities List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Heart className="w-5 h-5 text-emerald-600" />
              <span>All Charities</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading charities...</p>
            ) : charities.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No charities registered</p>
            ) : (
              <div className="space-y-4">
                {charities.map((charity, index) => (
                  <div
                    key={charity.id}
                    className="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg border border-emerald-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="font-medium text-gray-900">{charity.name}</h4>
                          {index === 0 && charity.total_donations > 0 && (
                            <Badge className="bg-yellow-500">Top Charity</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{charity.description}</p>
                        
                        {/* Donation Breakdown */}
                        <div className="grid grid-cols-4 gap-2 text-sm">
                          <div className="bg-white p-2 rounded border">
                            <p className="text-xs text-gray-500">DAC</p>
                            <p className="font-medium text-emerald-600">${charity.donations_dac.toFixed(2)}</p>
                          </div>
                          <div className="bg-white p-2 rounded border">
                            <p className="text-xs text-gray-500">DRLP</p>
                            <p className="font-medium text-blue-600">${charity.donations_drlp.toFixed(2)}</p>
                          </div>
                          <div className="bg-white p-2 rounded border">
                            <p className="text-xs text-gray-500">Round-up</p>
                            <p className="font-medium text-orange-600">${charity.donations_roundup.toFixed(2)}</p>
                          </div>
                          <div className="bg-emerald-100 p-2 rounded border border-emerald-300">
                            <p className="text-xs text-emerald-700">Total</p>
                            <p className="font-bold text-emerald-700">${charity.total_donations.toFixed(2)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
