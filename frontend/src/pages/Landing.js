import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ShoppingCart, Store, BarChart3 } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-emerald-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto space-y-8">
          <h1 className="text-6xl sm:text-7xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            DealShaq
          </h1>
          <p className="text-2xl text-gray-600" style={{ fontFamily: 'Inter, sans-serif' }}>
            Discover Sizzling Hot Deals on Grocery Foods
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Connect local consumers with retailers offering steep discounts on quality groceries.
            Every purchase contributes to charity.
          </p>

          {/* App Selection Cards */}
          <div className="grid md:grid-cols-3 gap-6 mt-16">
            {/* Consumer Card */}
            <div
              data-testid="consumer-card"
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-transparent hover:border-emerald-500 cursor-pointer"
              onClick={() => navigate('/consumer')}
            >
              <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShoppingCart className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                Consumer
              </h3>
              <p className="text-gray-600 mb-6">
                Browse deals, save on groceries, and support local charities
              </p>
              <Button
                data-testid="consumer-launch-btn"
                className="w-full bg-emerald-600 hover:bg-emerald-700"
                onClick={() => navigate('/consumer')}
              >
                Launch App
              </Button>
            </div>

            {/* Retailer Card */}
            <div
              data-testid="retailer-card"
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-transparent hover:border-blue-500 cursor-pointer"
              onClick={() => navigate('/retailer')}
            >
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Store className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                Retailer
              </h3>
              <p className="text-gray-600 mb-6">
                Post deals, manage inventory, and engage with customers
              </p>
              <Button
                data-testid="retailer-launch-btn"
                className="w-full bg-blue-600 hover:bg-blue-700"
                onClick={() => navigate('/retailer')}
              >
                Launch App
              </Button>
            </div>

            {/* Admin Card */}
            <div
              data-testid="admin-card"
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-transparent hover:border-purple-500 cursor-pointer"
              onClick={() => navigate('/admin')}
            >
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                Admin
              </h3>
              <p className="text-gray-600 mb-6">
                Monitor system, manage users, and view analytics
              </p>
              <Button
                data-testid="admin-launch-btn"
                className="w-full bg-purple-600 hover:bg-purple-700"
                onClick={() => navigate('/admin')}
              >
                Launch Dashboard
              </Button>
            </div>
          </div>

          {/* Features Section */}
          <div className="mt-20 grid md:grid-cols-3 gap-8 text-left">
            <div className="space-y-2">
              <div className="text-3xl font-bold text-emerald-600">💰</div>
              <h4 className="text-xl font-bold text-gray-900">Save Big</h4>
              <p className="text-gray-600">Get steep discounts on quality groceries from local retailers</p>
            </div>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-emerald-600">❤️</div>
              <h4 className="text-xl font-bold text-gray-900">Give Back</h4>
              <p className="text-gray-600">Every purchase contributes to your chosen charity</p>
            </div>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-emerald-600">🔔</div>
              <h4 className="text-xl font-bold text-gray-900">Stay Notified</h4>
              <p className="text-gray-600">Get alerts when deals match your favorites</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
