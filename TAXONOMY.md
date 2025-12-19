# DealShaq Grocery Taxonomy - Version 1.0

## Overview
DealShaq uses a simplified 20-category taxonomy for efficient matching between RSHDs and DACFI-Lists.

## Design Principles
1. **Top-level only for DACFI-Lists**: DACs select from 20 categories, not subcategories
2. **Subcategories are internal**: Used by retailers for detailed item classification
3. **Attributes vs. Categories**: Organic, gluten-free, non-GMO are item attributes, not categories
4. **Produce split**: "Produce" becomes "Fruits" + "Vegetables" (2-to-1 substitution)

## 20 Top-Level Categories

### 1. Fruits
Fresh, frozen, dried, and canned fruits
- Examples: Apples, bananas, berries, melons, citrus

### 2. Vegetables
Fresh, frozen, canned vegetables and salads
- Examples: Lettuce, tomatoes, carrots, broccoli, peppers

### 3. Meat & Poultry
All fresh, frozen, and processed meats and poultry
- Examples: Beef, chicken, pork, turkey, lamb

### 4. Seafood
Fresh, frozen, and canned seafood
- Examples: Fish, shrimp, crab, lobster, salmon

### 5. Dairy & Eggs
Milk, cheese, yogurt, butter, eggs, and dairy alternatives
- Examples: Milk, cheddar, Greek yogurt, eggs, almond milk

### 6. Bakery & Bread
Baked goods, bread, pastries, and desserts
- Examples: Bread, bagels, muffins, cakes, cookies

### 7. Pantry Staples
Dry goods, canned items, condiments, and cooking basics
- Examples: Flour, sugar, canned beans, ketchup, mustard

### 8. Snacks & Candy
Chips, crackers, candy, nuts, and snack foods
- Examples: Potato chips, pretzels, chocolate, trail mix

### 9. Frozen Foods
Frozen meals, pizzas, ice cream, and frozen desserts
- Examples: Frozen pizza, ice cream, frozen dinners, popsicles

### 10. Beverages
Juices, sodas, water, coffee, tea, and non-alcoholic drinks
- Examples: Orange juice, Coca-Cola, bottled water, coffee

### 11. Deli & Prepared Foods
Deli meats, cheeses, prepared meals, and ready-to-eat foods
- Examples: Sliced turkey, rotisserie chicken, potato salad

**Note:** "Alcoholic Beverages" has been replaced with additional categories in V1.0

### 12. Breakfast & Cereal
Cereals, oatmeal, breakfast bars, and morning foods
- Examples: Corn flakes, granola, oatmeal, breakfast bars

### 14. Pasta, Rice & Grains
Pasta, rice, quinoa, and other grains
- Examples: Spaghetti, brown rice, quinoa, couscous

### 15. Oils, Sauces & Spices
Cooking oils, sauces, spices, and seasonings
- Examples: Olive oil, soy sauce, pepper, oregano

### 16. Baby & Kids
Baby food, formula, diapers, and kid-specific items
- Examples: Baby formula, baby food, diapers, kid snacks

### 17. Health & Nutrition
Vitamins, supplements, protein powders, and health foods
- Examples: Multivitamins, protein powder, energy bars

### 18. Household Essentials
Cleaning supplies, paper goods, and household items
- Examples: Paper towels, dish soap, laundry detergent

### 19. Personal Care
Hygiene, beauty, and personal care products
- Examples: Toothpaste, shampoo, soap, deodorant

### 20. Pet Supplies
Pet food, treats, and basic pet care items
- Examples: Dog food, cat treats, pet toys

## Item-Level Attributes (Not Categories)

These are **filters/tags**, not categories:
- Organic
- Gluten-free
- Non-GMO
- Vegan
- Vegetarian
- Kosher
- Sugar-free
- Low-sodium
- Lactose-free

**Implementation**: These attributes can be added to RSHD items and used for advanced filtering in future versions, but they are NOT part of the category taxonomy.

## Subcategories (Internal Use Only)

Subcategories are used internally by retailers when posting RSHDs for better organization, but are **NOT exposed to DACs for DACFI-List selection**.

### Example Internal Subcategories:
- **Fruits**: Apples, Bananas, Berries, Citrus, Melons
- **Vegetables**: Leafy Greens, Root Vegetables, Peppers, Tomatoes
- **Dairy & Eggs**: Milk, Cheese, Yogurt, Eggs, Butter
- **Meat & Poultry**: Beef, Chicken, Pork, Turkey

**Note**: Subcategories are optional and for retailer convenience only. They do NOT affect DACFI-List matching.

## DACFI-List Behavior

### DAC Perspective
When a DAC builds their DACFI-List:
1. Select from **20 top-level categories only**
2. No subcategory selection available
3. Example: Select "Fruits" (NOT "Apples")
4. Will receive notifications for ANY RSHD in "Fruits" category

### Matching Logic
```
RSHD posted in category "Fruits"
    ↓
Backend checks all DACs with "Fruits" in their DACFI-List
    ↓
Generate DRLPDAC-SNL (matched DACs)
    ↓
Send notifications to matched DACs
```

## Retailer App Behavior

### RSHD Posting
When a DRLP posts an RSHD:
1. **Required**: Select 1 of 20 top-level categories
2. **Optional**: Add subcategory for internal organization (not used in matching)
3. **Optional**: Add item attributes (organic, gluten-free, etc.)

### Example RSHD Entry
```
Category: Fruits (required)
Subcategory: Apples (optional, internal only)
Item Name: Organic Honeycrisp Apples
Attributes: organic=true (item attribute)
```

## Backend Implementation

### Category Validation
- RSHD must have 1 of 20 valid categories
- Subcategory is optional and not validated
- Attributes are stored but not used in matching (v1.0)

### Matching Algorithm
```python
# Existence-check model (category level only)
def match_rshd_to_dacs(rshd):
    category = rshd["category"]  # e.g., "Fruits"
    
    # Find all DACs with this category in their DACFI-List
    matching_dacs = db.favorites.find({
        "category": category
    })
    
    # Subcategory is ignored for matching
    # Attributes are ignored for matching (v1.0)
    
    return [dac["dac_id"] for dac in matching_dacs]
```

## Admin Dashboard

### Reporting
- View RSHD distribution across 20 categories
- Track which categories are most popular
- Analyze DACFI-List preferences by category
- Monitor category-level matching efficiency

### Analytics Queries
- "How many DACs have 'Fruits' in their DACFI-List?"
- "How many RSHDs were posted in 'Dairy & Eggs' this week?"
- "What's the conversion rate for 'Meat & Poultry' RSHDs?"

## Migration from Old Taxonomy

### Old System (Before)
- "Produce" as single category with "Fruits" and "Vegetables" as subcategories
- Variable subcategories across categories
- DACFI-List included subcategories

### New System (Now)
- "Fruits" and "Vegetables" as separate top-level categories
- 20 fixed top-level categories
- DACFI-List only uses top-level categories

### Migration Steps
1. Split "Produce" favorites into "Fruits" and "Vegetables"
2. Remove subcategory selections from existing DACFI-Lists
3. Update all RSHDs to use new 20-category system
4. Validate all data against new taxonomy

## Validation Rules

### Backend Validation
```python
VALID_CATEGORIES = [
    "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
    "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
    "Snacks & Candy", "Frozen Foods", "Beverages",
    "Deli & Prepared Foods", "Breakfast & Cereal",
    "Pasta, Rice & Grains", "Oils, Sauces & Spices",
    "Baby & Kids", "Health & Nutrition", "Household Essentials",
    "Personal Care", "Pet Supplies", "Miscellaneous"
]

def validate_category(category: str) -> bool:
    return category in VALID_CATEGORIES
```

### DACFI-List Validation
- Must select at least 1 category
- Can select up to all 20 categories
- Cannot select subcategories
- Cannot select attributes as categories

### RSHD Validation
- Must have exactly 1 category
- Category must be in VALID_CATEGORIES list
- Subcategory is optional and free-form
- Attributes are optional and stored as tags

## Benefits of This Taxonomy

### For DACs (Consumers)
✅ Simple: Only 20 categories to choose from
✅ Clear: No confusion about subcategories
✅ Efficient: Quick onboarding process
✅ Comprehensive: Covers all grocery needs

### For DRLPs (Retailers)
✅ Easy: Straightforward category selection
✅ Flexible: Optional subcategories for organization
✅ Consistent: Standardized across all stores
✅ Accurate: Clear mapping for every item

### For Platform
✅ Scalable: Fast matching with 20 categories
✅ Maintainable: Fixed taxonomy is easy to manage
✅ Performant: O(1) category lookups
✅ Extensible: Attributes allow future expansion

## Future Enhancements (v2.0+)

### Potential Additions
- Advanced filtering by attributes (organic, gluten-free)
- Personalized recommendations based on purchase history
- Seasonal category highlighting
- Dynamic subcategory suggestions
- Multi-category RSHD support (e.g., "Deli & Prepared Foods" + "Breakfast & Cereal")

### Backwards Compatibility
Any taxonomy changes must maintain compatibility with existing DACFI-Lists and RSHDs.

---

**Version**: 1.0  
**Last Updated**: December 2025  
**Status**: Active - 20 categories in production (Miscellaneous replaces Alcoholic Beverages)
