import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { favoriteItems, categories as categoriesApi } from '../../utils/api';
import { Heart, Trash2, Plus, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';

export default function ConsumerFavorites({ user, onLogout }) {
  const [favoriteItemsByCategory, setFavoriteItemsByCategory] = useState({});
  const [totalItems, setTotalItems] = useState(0);
  const [newItemName, setNewItemName] = useState('');
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    loadCategories();
    loadFavoriteItems();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await categoriesApi.list();
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const loadFavoriteItems = async () => {
    try {
      const response = await favoriteItems.list();
      setFavoriteItemsByCategory(response.data.items_by_category || {});
      setTotalItems(response.data.total_items || 0);
    } catch (error) {
      toast.error('Failed to load favorite items');
    } finally {
      setLoading(false);
    }
  };

  const addFavoriteItem = async () => {
    if (!newItemName.trim()) {
      toast.error('Please enter an item name');
      return;
    }

    setAdding(true);
    try {
      const response = await favoriteItems.create({
        item_name: newItemName.trim(),
      });
      
      toast.success(`"${newItemName}" added to your favorites!`, {
        description: `Automatically categorized as: ${response.data.item.category}`,
      });
      
      setNewItemName('');
      loadFavoriteItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add item');
    } finally {
      setAdding(false);
    }
  };

  const removeFavoriteItem = async (itemName, category) => {
    try {
      await favoriteItems.delete(itemName);
      toast.success(`"${itemName}" removed from favorites`);
      loadFavoriteItems();
    } catch (error) {
      toast.error('Failed to remove item');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            My Favorite Items (DACFI-List)
          </h1>
          <p className="text-gray-600 mt-1">
            Add specific items you love. When retailers post matching deals, you'll be notified.
          </p>
        </div>

        {/* Add Favorite Item Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Plus className="w-5 h-5 text-emerald-600" />
              <span>Add Favorite Item</span>
            </CardTitle>
            <CardDescription>
              Enter your favorite item - we'll automatically organize it for you
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Input
                  type="text"
                  placeholder='e.g., "Granola" or "Quaker, Granola"'
                  value={newItemName}
                  onChange={(e) => setNewItemName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addFavoriteItem()}
                  disabled={adding}
                  className="text-base"
                />
                <p className="text-sm text-gray-500 mt-2">
                  <strong>Brand-specific items:</strong> Use comma after brand name (e.g., "Valley Farm, 2% Milk")<br />
                  <strong>Any brand:</strong> Enter generic name only (e.g., "Granola" matches all brands)
                </p>
              </div>

              <Button
                onClick={addFavoriteItem}
                disabled={!newItemName.trim() || adding}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                {adding ? 'Adding...' : 'Add to Favorites'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Favorites List by Category */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Your Favorite Items</CardTitle>
                <CardDescription>
                  {totalItems} {totalItems === 1 ? 'item' : 'items'} organized by category
                </CardDescription>
              </div>
              <Badge variant="secondary" className="text-base px-3 py-1">
                {totalItems} items
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading favorites...</p>
            ) : totalItems === 0 ? (
              <div className="text-center py-12">
                <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No favorite items yet</p>
                <p className="text-gray-400 text-sm mt-2">Add items above to get personalized deal notifications</p>
              </div>
            ) : (
              <div className="space-y-6">
                {categories.map((category) => {
                  const items = favoriteItemsByCategory[category];
                  if (!items || items.length === 0) return null;

                  return (
                    <div key={category} className="border-l-4 border-emerald-500 pl-4">
                      <h3 className="text-lg font-bold text-gray-900 mb-3">
                        {category}
                      </h3>
                      <div className="space-y-2">
                        {items.map((item, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between bg-gray-50 hover:bg-gray-100 rounded-lg p-3 transition-colors"
                          >
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <div>
                                  <span className="font-medium text-gray-900">
                                    {item.item_name}
                                  </span>
                                  {item.has_brand && (
                                    <span className="text-xs text-gray-500 ml-2">
                                      (Brand: {item.brand})
                                    </span>
                                  )}
                                </div>
                                {item.auto_added_date ? (
                                  <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                                    <Sparkles className="w-3 h-3 mr-1" />
                                    Auto: {formatDate(item.auto_added_date)}
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                                    Manual
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center space-x-2 mt-1">
                                {item.attributes?.organic && (
                                  <span className="text-xs text-emerald-600">🌿 Organic</span>
                                )}
                                {item.has_brand && (
                                  <span className="text-xs text-purple-600">🏷️ Brand-specific</span>
                                )}
                              </div>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeFavoriteItem(item.item_name, category)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <Heart className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-bold text-gray-900 mb-2">How It Works</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>✓ <strong>Add items manually</strong> by typing specific product names</li>
                  <li>✓ <strong>Auto-categorization</strong> organizes items into categories automatically</li>
                  <li>✓ <strong>Smart matching</strong> notifies you when retailers post matching deals</li>
                  <li>✓ <strong>Organic detection</strong> recognizes when you prefer organic products</li>
                  <li>✓ <strong>Auto-add feature</strong> learns from your purchases (configurable in Settings)</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ConsumerLayout>
  );
}
