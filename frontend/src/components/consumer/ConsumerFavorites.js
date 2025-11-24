import { useState, useEffect } from 'react';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { favorites as favoritesApi } from '../../utils/api';
import { Heart, Trash2, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';

// DealShaq 20-Category Taxonomy (Top-level only for DACFI-List)
const CATEGORIES = [
  "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
  "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
  "Snacks & Candy", "Frozen Foods", "Beverages",
  "Alcoholic Beverages", "Deli & Prepared Foods",
  "Breakfast & Cereal", "Pasta, Rice & Grains",
  "Oils, Sauces & Spices", "Baby & Kids",
  "Health & Nutrition", "Household Essentials",
  "Personal Care", "Pet Supplies"
];

export default function ConsumerFavorites({ user, onLogout }) {
  const [favorites, setFavorites] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const response = await favoritesApi.list();
      setFavorites(response.data);
    } catch (error) {
      toast.error('Failed to load favorites');
    } finally {
      setLoading(false);
    }
  };

  const addFavorite = async () => {
    if (!selectedCategory) {
      toast.error('Please select a category');
      return;
    }

    try {
      await favoritesApi.create({
        category: selectedCategory,
      });
      toast.success('Category added to your DACFI-List!');
      loadFavorites();
      setSelectedCategory('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add favorite');
    }
  };

  const removeFavorite = async (id) => {
    try {
      await favoritesApi.delete(id);
      toast.success('Favorite removed');
      loadFavorites();
    } catch (error) {
      toast.error('Failed to remove favorite');
    }
  };

  const selectedCategoryObj = CATEGORIES.find((c) => c.value === selectedCategory);

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            My DACFI-List
          </h1>
          <p className="text-gray-600 mt-1">Build your favorites inventory list. When retailers post matching RSHDs, you'll be notified.</p>
        </div>

        {/* Add Favorite Form */}
        <Card>
          <CardHeader>
            <CardTitle>Add Favorite Category</CardTitle>
            <CardDescription>Choose categories to receive deal notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger data-testid="select-category">
                  <SelectValue placeholder="Select Category" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.value}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={selectedSubcategory}
                onValueChange={setSelectedSubcategory}
                disabled={!selectedCategory}
              >
                <SelectTrigger data-testid="select-subcategory">
                  <SelectValue placeholder="Subcategory (Optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All {selectedCategory}</SelectItem>
                  {selectedCategoryObj?.subcategories.map((sub) => (
                    <SelectItem key={sub} value={sub}>
                      {sub}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                data-testid="add-favorite-btn"
                onClick={addFavorite}
                disabled={!selectedCategory}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Favorite
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Favorites List */}
        <Card>
          <CardHeader>
            <CardTitle>Your Favorite Categories</CardTitle>
            <CardDescription>You'll receive notifications for deals in these categories</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading favorites...</p>
            ) : favorites.length === 0 ? (
              <div className="text-center py-12">
                <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No favorites yet</p>
                <p className="text-gray-400 text-sm mt-2">Add categories above to get started</p>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {favorites.map((fav) => (
                  <div
                    key={fav.id}
                    data-testid={`favorite-${fav.id}`}
                    className="border rounded-lg p-4 bg-gradient-to-br from-emerald-50 to-teal-50 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="bg-emerald-100 p-2 rounded-lg">
                        <Heart className="w-5 h-5 text-emerald-600 fill-emerald-600" />
                      </div>
                      <Button
                        data-testid={`remove-favorite-${fav.id}`}
                        size="sm"
                        variant="ghost"
                        onClick={() => removeFavorite(fav.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                    <h3 className="font-bold text-gray-900 mb-1">{fav.category}</h3>
                    {fav.subcategory && <Badge variant="outline">{fav.subcategory}</Badge>}
                  </div>
                ))}
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
                <h4 className="font-bold text-gray-900 mb-1">Supply-Initiated Model</h4>
                <p className="text-sm text-gray-600">
                  DealShaq is supply-driven: Retailers initiate sales by posting RSHDs (urgent items). 
                  Our backend matches them against your DACFI-List and notifies you only if there's a match. 
                  No searching, no noise - just targeted offers you care about.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ConsumerLayout>
  );
}
