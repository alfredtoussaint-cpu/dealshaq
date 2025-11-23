import { Button } from '@/components/ui/button';
import { Home, Package, ShoppingBag, LogOut, Plus } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Store } from 'lucide-react';

export default function RetailerLayout({ children, user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/retailer/dashboard', icon: Home, label: 'Dashboard', testId: 'retailer-nav-home' },
    { path: '/retailer/post-item', icon: Plus, label: 'Post Deal', testId: 'retailer-nav-post' },
    { path: '/retailer/inventory', icon: Package, label: 'Inventory', testId: 'retailer-nav-inventory' },
    { path: '/retailer/orders', icon: ShoppingBag, label: 'Orders', testId: 'retailer-nav-orders' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Store className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
                DealShaq Retailer
              </h1>
              <p className="text-xs text-gray-500">{user?.name}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            data-testid="retailer-logout-btn"
            className="text-gray-600 hover:text-gray-900"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>

      <nav className="bg-white border-b">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1 overflow-x-auto">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  data-testid={item.testId}
                  onClick={() => navigate(item.path)}
                  className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                    isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
