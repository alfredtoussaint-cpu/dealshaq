import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { auth } from '../utils/api';
import ConsumerAuth from '../components/consumer/ConsumerAuth';
import ConsumerDashboard from '../components/consumer/ConsumerDashboard';
import ConsumerBrowse from '../components/consumer/ConsumerBrowse';
import ConsumerFavorites from '../components/consumer/ConsumerFavorites';
import ConsumerNotifications from '../components/consumer/ConsumerNotifications';
import ConsumerCheckout from '../components/consumer/ConsumerCheckout';
import ConsumerOrders from '../components/consumer/ConsumerOrders';

export default function ConsumerApp() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      const parsedUser = JSON.parse(savedUser);
      if (parsedUser.role === 'DAC') {
        setUser(parsedUser);
      } else {
        localStorage.clear();
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, userData) => {
    if (userData.role !== 'DAC') {
      throw new Error('Invalid user role for Consumer App');
    }
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    navigate('/consumer/dashboard');
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    navigate('/consumer');
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return <ConsumerAuth onLogin={handleLogin} />;
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/consumer/dashboard" replace />} />
      <Route path="/dashboard" element={<ConsumerDashboard user={user} onLogout={handleLogout} />} />
      <Route path="/browse" element={<ConsumerBrowse user={user} onLogout={handleLogout} />} />
      <Route path="/favorites" element={<ConsumerFavorites user={user} onLogout={handleLogout} />} />
      <Route path="/notifications" element={<ConsumerNotifications user={user} onLogout={handleLogout} />} />
      <Route path="/checkout" element={<ConsumerCheckout user={user} onLogout={handleLogout} />} />
      <Route path="/orders" element={<ConsumerOrders user={user} onLogout={handleLogout} />} />
    </Routes>
  );
}
