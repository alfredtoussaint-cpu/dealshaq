import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import RetailerAuth from '../components/retailer/RetailerAuth';
import RetailerDashboard from '../components/retailer/RetailerDashboard';
import RetailerPostItem from '../components/retailer/RetailerPostItem';
import RetailerInventory from '../components/retailer/RetailerInventory';
import RetailerOrders from '../components/retailer/RetailerOrders';

export default function RetailerApp() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      const parsedUser = JSON.parse(savedUser);
      if (parsedUser.role === 'DRLP') {
        setUser(parsedUser);
      } else {
        localStorage.clear();
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, userData) => {
    if (userData.role !== 'DRLP') {
      throw new Error('Invalid user role for Retailer App');
    }
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    navigate('/retailer/dashboard');
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    navigate('/retailer');
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return <RetailerAuth onLogin={handleLogin} />;
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/retailer/dashboard" replace />} />
      <Route path="/dashboard" element={<RetailerDashboard user={user} onLogout={handleLogout} />} />
      <Route path="/post-item" element={<RetailerPostItem user={user} onLogout={handleLogout} />} />
      <Route path="/inventory" element={<RetailerInventory user={user} onLogout={handleLogout} />} />
      <Route path="/orders" element={<RetailerOrders user={user} onLogout={handleLogout} />} />
    </Routes>
  );
}
