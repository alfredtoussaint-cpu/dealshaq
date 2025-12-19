import { Button } from '@/components/ui/button';
import { Home, ShoppingBag, Heart, Bell, ShoppingCart, LogOut, Receipt, Settings, Store } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import Logo from '../Logo';

export default function ConsumerLayout({ children, user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/consumer/dashboard', icon: Home, label: 'Home', testId: 'nav-home' },
    { path: '/consumer/browse', icon: ShoppingBag, label: 'Browse', testId: 'nav-browse' },
    { path: '/consumer/favorites', icon: Heart, label: 'Favorites', testId: 'nav-favorites' },
    { path: '/consumer/retailers', icon: Store, label: 'Retailers', testId: 'nav-retailers' },
    { path: '/consumer/notifications', icon: Bell, label: 'Alerts', testId: 'nav-notifications' },
    { path: '/consumer/orders', icon: Receipt, label: 'Orders', testId: 'nav-orders' },
    { path: '/consumer/settings', icon: Settings, label: 'Settings', testId: 'nav-settings' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-100 p-2 rounded-lg">
              <ShoppingCart className="w-6 h-6 text-emerald-600" />
            </div>
            <div 
              className="cursor-pointer"
              onClick={() => navigate('/consumer/dashboard')}
            >
              <Logo size="default" />
              <p className="text-xs text-gray-500">{user?.name}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            data-testid="logout-btn"
            className="text-gray-600 hover:text-gray-900"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>

      {/* Navigation */}
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
                      ? 'border-emerald-600 text-emerald-600'
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

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
