import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import AdminAuth from '../components/admin/AdminAuth';
import AdminDashboard from '../components/admin/AdminDashboard';
import AdminUsers from '../components/admin/AdminUsers';
import AdminTransactions from '../components/admin/AdminTransactions';
import AdminItems from '../components/admin/AdminItems';
import AdminCharities from '../components/admin/AdminCharities';

export default function AdminApp() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      const parsedUser = JSON.parse(savedUser);
      if (parsedUser.role === 'Admin') {
        setUser(parsedUser);
      } else {
        localStorage.clear();
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (responseData) => {
    const { access_token, user: userData } = responseData;
    if (userData.role !== 'Admin') {
      throw new Error('Invalid user role for Admin App');
    }
    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    navigate('/admin/dashboard');
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    navigate('/admin');
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return <AdminAuth onLogin={handleLogin} />;
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/admin/dashboard" replace />} />
      <Route path="/dashboard" element={<AdminDashboard user={user} onLogout={handleLogout} />} />
      <Route path="/users" element={<AdminUsers user={user} onLogout={handleLogout} />} />
      <Route path="/transactions" element={<AdminTransactions user={user} onLogout={handleLogout} />} />
      <Route path="/items" element={<AdminItems user={user} onLogout={handleLogout} />} />
      <Route path="/charities" element={<AdminCharities user={user} onLogout={handleLogout} />} />
    </Routes>
  );
}
