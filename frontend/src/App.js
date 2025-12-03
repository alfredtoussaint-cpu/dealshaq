import { useState, useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ConsumerApp from './apps/ConsumerApp';
import RetailerApp from './apps/RetailerApp';
import AdminApp from './apps/AdminApp';
import Landing from './pages/Landing';
import PasswordReset from './components/PasswordReset';
import { Toaster } from '@/components/ui/sonner';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/reset-password" element={<PasswordReset />} />
          <Route path="/consumer/*" element={<ConsumerApp />} />
          <Route path="/retailer/*" element={<RetailerApp />} />
          <Route path="/admin/*" element={<AdminApp />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
