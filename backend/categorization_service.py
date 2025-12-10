"""
DealShaq Product Categorization Service

Automatically maps product names to the 20 DealShaq categories
using AI (GPT-5/Gemini) or keyword matching.
"""

import os
from typing import Optional, Dict, List
# Uncomment when implementing AI:
# from emergentintegrations import OpenAI

# DealShaq's 20 Categories
DEALSHAQ_CATEGORIES = [
    "Fruits",
    "Vegetables", 
    "Meat & Poultry",
    "Seafood",
    "Dairy & Eggs",
    "Bakery & Bread",
    "Pantry Staples",
    "Snacks & Candy",
    "Frozen Foods",
    "Beverages (Non-Alcoholic)",
    "Alcoholic Beverages",
    "Breakfast & Cereal",
    "Deli & Prepared Foods",
    "International Foods",
    "Organic & Natural",
    "Pet Supplies",
    "Baby & Kids",
    "Health & Nutrition",
    "Household Essentials",
    "Personal Care"
]

# Keyword mapping for common items (fallback before AI)
CATEGORY_KEYWORDS = {
    "Dairy & Eggs": [
        "milk", "cheese", "yogurt", "butter", "cream", "eggs", "dairy",
        "cheddar", "mozzarella", "parmesan", "sour cream", "cottage cheese"
    ],
    "Fruits": [
        "apple", "banana", "orange", "grape", "berry", "strawberry",
        "melon", "watermelon", "pear", "peach", "plum", "cherry"
    ],
    "Vegetables": [
        "lettuce", "tomato", "carrot", "broccoli", "pepper", "onion",
        "cucumber", "spinach", "celery", "potato", "cabbage"
    ],
    "Meat & Poultry": [
        "beef", "chicken", "pork", "turkey", "lamb", "steak",
        "ground beef", "chicken breast", "bacon", "sausage"
    ],
    "Seafood": [
        "fish", "salmon", "tuna", "shrimp", "crab", "lobster",
        "tilapia", "cod", "seafood"
    ],
    "Bakery & Bread": [
        "bread", "bagel", "muffin", "cake", "cookie", "pastry",
        "donut", "croissant", "baguette", "roll"
    ],
    "Breakfast & Cereal": [
        "cereal", "granola", "oatmeal", "oats", "cornflakes",
        "cheerios", "breakfast", "pancake mix", "waffle"
    ],
    "Snacks & Candy": [
        "chips", "crackers", "candy", "chocolate", "pretzels",
        "popcorn", "nuts", "trail mix", "cookies"
    ],
    "Frozen Foods": [
        "frozen", "ice cream", "frozen pizza", "frozen dinner",
        "popsicle", "frozen vegetables", "frozen fruit"
    ],
    "Beverages (Non-Alcoholic)": [
        "juice", "soda", "water", "coffee", "tea", "energy drink",
        "sports drink", "lemonade", "iced tea"
    ],
    "Alcoholic Beverages": [
        "beer", "wine", "liquor", "vodka", "whiskey", "champagne",
        "ale", "lager", "spirits"
    ],
    "Pantry Staples": [
        "pasta", "rice", "flour", "sugar", "oil", "vinegar",
        "sauce", "canned", "beans", "soup", "ketchup", "mustard"
    ],
    "Deli & Prepared Foods": [
        "deli", "rotisserie", "sandwich", "salad", "prepared",
        "ready-to-eat", "cooked chicken"
    ],
    "International Foods": [
        "mexican", "asian", "italian", "indian", "sushi",
        "tortilla", "salsa", "soy sauce", "curry"
    ],
    "Organic & Natural": [
        "organic", "natural", "non-gmo", "gluten-free",
        "vegan", "vegetarian", "whole foods"
    ],
    "Health & Nutrition": [
        "vitamin", "supplement", "protein", "protein bar",
        "nutrition", "health", "diet", "fitness"
    ],
    "Household Essentials": [
        "detergent", "soap", "paper towel", "toilet paper",
        "cleaner", "trash bag", "aluminum foil", "cleaning"
    ],
    "Personal Care": [
        "shampoo", "toothpaste", "deodorant", "lotion",
        "soap", "body wash", "skincare", "cosmetics"
    ],
    "Baby & Kids": [
        "baby", "diaper", "formula", "baby food", "wipes",
        "kids", "children", "toddler"
    ],
    "Pet Supplies": [
        "dog", "cat", "pet", "dog food", "cat food",
        "pet food", "treats", "litter"
    ]
}


def categorize_by_keywords(product_name: str) -> Optional[str]:
    """
    Simple keyword matching to categorize product.
    Returns category name or None if no match.
    """
    product_lower = product_name.lower()
    
    # Score each category
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in product_lower)
        if score > 0:
            scores[category] = score
    
    if scores:
        # Return category with highest score
        best_category = max(scores, key=scores.get)
        return best_category
    
    return None


async def categorize_with_ai(product_name: str) -> Optional[str]:
    """
    Use AI (GPT-5 or Gemini) to categorize product.
    Returns category name or None if API fails.
    """
    try:
        # Uncomment and implement when adding AI integration:
        """
        from emergentintegrations import OpenAI
        
        client = OpenAI(api_key=os.environ.get('EMERGENT_LLM_KEY'))
        
        prompt = f'''Classify this grocery product into ONE of these 20 categories:
{', '.join(DEALSHAQ_CATEGORIES)}

Product: "{product_name}"

Rules:
- Return ONLY the exact category name from the list above
- No explanation, just the category name
- If unsure, choose the most likely category

Category:'''

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a grocery product categorization expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        category = response.choices[0].message.content.strip()
        
        # Validate category is in our list
        if category in DEALSHAQ_CATEGORIES:
            return category
        """
        
        # For now, return None (implement AI later)
        return None
        
    except Exception as e:
        print(f"AI categorization error: {e}")
        return None


def generate_keywords(product_name: str) -> List[str]:
    """
    Generate search keywords from product name for better matching.
    """
    keywords = []
    
    # Basic tokenization
    words = product_name.lower().split()
    keywords.extend(words)
    
    # Remove common words
    stop_words = {"the", "a", "an", "and", "or", "of", "with"}
    keywords = [w for w in keywords if w not in stop_words]
    
    # Add full product name
    keywords.append(product_name.lower())
    
    return list(set(keywords))


async def auto_categorize_product(product_name: str, barcode: Optional[str] = None) -> Dict:
    """
    Main categorization function that tries multiple methods.
    
    Returns:
    {
        "category": str or None,
        "confidence": "high" | "medium" | "low" | "none",
        "method": "barcode" | "ai" | "keyword" | "manual_required",
        "keywords": List[str],
        "suggestions": List[str]  # Alternative categories if uncertain
    }
    """
    
    # Tier 1: Barcode lookup (future implementation)
    if barcode:
        # TODO: Implement barcode API lookup
        pass
    
    # Tier 2: Keyword matching
    keyword_category = categorize_by_keywords(product_name)
    if keyword_category:
        return {
            "category": keyword_category,
            "confidence": "medium",
            "method": "keyword_match",
            "keywords": generate_keywords(product_name),
            "suggestions": []
        }
    
    # Tier 3: AI classification
    ai_category = await categorize_with_ai(product_name)
    if ai_category:
        return {
            "category": ai_category,
            "confidence": "medium",
            "method": "ai_classification",
            "keywords": generate_keywords(product_name),
            "suggestions": []
        }
    
    # Tier 4: Manual selection required
    # Suggest most common categories
    common_categories = [
        "Dairy & Eggs",
        "Fruits",
        "Vegetables",
        "Meat & Poultry",
        "Breakfast & Cereal"
    ]
    
    return {
        "category": None,
        "confidence": "none",
        "method": "manual_required",
        "keywords": generate_keywords(product_name),
        "suggestions": common_categories
    }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test cases
        test_items = [
            "2% Milk",
            "Granola",
            "Organic Apples",
            "Ground Beef",
            "Whole Wheat Bread"
        ]
        
        for item in test_items:
            result = await auto_categorize_product(item)
            print(f"\nItem: {item}")
            print(f"Category: {result['category']}")
            print(f"Method: {result['method']}")
            print(f"Keywords: {result['keywords']}")
    
    asyncio.run(test())
