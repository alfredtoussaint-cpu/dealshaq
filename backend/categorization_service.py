from typing import Dict, List, Optional, Tuple
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Keyword-based categorization dictionary
CATEGORY_KEYWORDS = {
    "Fruits": ["apple", "banana", "orange", "grape", "berry", "berries", "melon", "watermelon", 
               "pear", "peach", "plum", "cherry", "cherries", "mango", "pineapple", "kiwi", "strawberry",
               "blueberry", "raspberry", "blackberry", "lemon", "lime", "grapefruit", "avocado"],
    
    "Vegetables": ["lettuce", "tomato", "cucumber", "carrot", "broccoli", "spinach", "kale",
                   "pepper", "peppers", "onion", "garlic", "potato", "celery", "cabbage", "zucchini",
                   "squash", "eggplant", "cauliflower", "asparagus", "mushroom", "corn", "peas"],
    
    "Meat & Poultry": ["beef", "chicken", "pork", "turkey", "lamb", "steak", "ground beef",
                       "bacon", "sausage", "ham", "ribs", "wings", "breast", "thigh", "drumstick"],
    
    "Seafood": ["fish", "salmon", "tuna", "shrimp", "crab", "lobster", "cod", "tilapia",
                "halibut", "trout", "sardine", "anchovy", "clam", "oyster", "mussel", "scallop"],
    
    "Dairy & Eggs": ["milk", "cheese", "yogurt", "butter", "egg", "eggs", "cream", "sour cream",
                     "cottage cheese", "cheddar", "mozzarella", "parmesan", "greek yogurt", 
                     "whipped cream", "half and half", "dairy"],
    
    "Bakery & Bread": ["bread", "bagel", "muffin", "croissant", "donut", "cake", "cookie",
                       "pie", "pastry", "baguette", "roll", "bun", "biscuit", "brownie", "cupcake"],
    
    "Pantry Staples": ["flour", "sugar", "salt", "rice", "beans", "canned", "soup", "ketchup",
                       "mustard", "mayo", "mayonnaise", "vinegar", "honey", "jam", "jelly", "peanut butter"],
    
    "Snacks & Candy": ["chips", "pretzels", "popcorn", "candy", "chocolate", "nuts", "crackers",
                       "cookies", "trail mix", "granola bar", "protein bar", "gummies"],
    
    "Frozen Foods": ["frozen", "ice cream", "pizza", "frozen dinner", "popsicle", "frozen meal",
                     "frozen vegetable", "frozen fruit"],
    
    "Beverages": ["juice", "orange juice", "apple juice", "grape juice", "soda", "water", "coffee", "tea", "energy drink", "sports drink",
                  "lemonade", "iced tea", "sparkling water", "cola", "beverage", "drink"],
    
    "Deli & Prepared Foods": ["deli", "rotisserie", "prepared", "ready to eat", "salad bar",
                              "sandwich", "wrap", "sushi", "sliced turkey", "sliced ham"],
    
    "Breakfast & Cereal": ["cereal", "oatmeal", "granola", "breakfast", "pancake", "waffle",
                           "syrup", "breakfast bar", "corn flakes"],
    
    "Pasta, Rice & Grains": ["pasta", "spaghetti", "macaroni", "noodle", "rice", "quinoa",
                             "couscous", "barley", "bulgur", "farro"],
    
    "Oils, Sauces & Spices": ["oil", "olive oil", "vegetable oil", "sauce", "soy sauce",
                              "hot sauce", "spice", "pepper", "oregano", "basil", "cinnamon",
                              "paprika", "curry"],
    
    "Baby & Kids": ["baby", "formula", "baby food", "diaper", "wipes", "kids"],
    
    "Health & Nutrition": ["vitamin", "supplement", "protein powder", "protein", "energy bar",
                           "health", "nutrition", "probiotic"],
    
    "Household Essentials": ["paper towel", "toilet paper", "tissue", "dish soap", "detergent",
                             "cleaning", "laundry", "trash bag", "cleaner"],
    
    "Personal Care": ["toothpaste", "shampoo", "soap", "deodorant", "lotion", "razor",
                      "shaving cream", "cosmetic", "makeup"],
    
    "Pet Supplies": ["dog food", "cat food", "pet", "dog treat", "cat treat", "pet toy"],
    
    "Miscellaneous": []  # Catch-all for items that don't fit elsewhere
}

# Valid categories list
VALID_CATEGORIES = [
    "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
    "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
    "Snacks & Candy", "Frozen Foods", "Beverages",
    "Deli & Prepared Foods", "Breakfast & Cereal",
    "Pasta, Rice & Grains", "Oils, Sauces & Spices",
    "Baby & Kids", "Health & Nutrition", "Household Essentials",
    "Personal Care", "Pet Supplies", "Miscellaneous"
]


def parse_brand_and_generic(item_input: str) -> Dict[str, any]:
    """
    Smart parsing of brand and generic names from user input.
    
    Supports formats:
    - "Quaker, Simply Granola" → brand: Quaker, generic: Granola
    - "Quaker Simply, Granola" → brand: Quaker Simply, generic: Granola
    - "Quaker, Granola" → brand: Quaker, generic: Granola
    - "Granola" → brand: None, generic: Granola
    
    Logic: Text before comma = brand, text after comma = generic (intelligently extracted)
    """
    item_input = item_input.strip()
    
    # Check if comma exists
    if ',' in item_input:
        parts = item_input.split(',', 1)  # Split on first comma only
        brand = parts[0].strip()
        
        # Smart generic extraction: extract the most meaningful generic term
        generic_part = parts[1].strip()
        
        # Extract the core generic name (last significant word or phrase)
        # Examples: "Simply Granola" → "Granola", "2% Milk" → "2% Milk"
        generic = extract_core_generic(generic_part)
        
        return {
            "brand": brand,
            "generic": generic,
            "full_name": item_input,
            "has_brand": True
        }
    else:
        # No comma = generic name only (no brand specified)
        return {
            "brand": None,
            "generic": item_input,
            "full_name": item_input,
            "has_brand": False
        }


def extract_core_generic(generic_part: str) -> str:
    """
    Extract the core generic name from a phrase.
    
    Examples:
    - "Simply Granola" → "Granola"
    - "Organic 2% Milk" → "2% Milk" (keeps percentage)
    - "Greek Yogurt" → "Greek Yogurt" (both words are meaningful)
    - "Fresh Bananas" → "Bananas"
    """
    generic_lower = generic_part.lower()
    
    # Common modifier words that should be removed to get core generic
    modifiers = {
        'simply', 'fresh', 'pure', 'natural', 'classic', 'original',
        'premium', 'extra', 'special', 'deluxe', 'regular', 'light'
    }
    
    words = generic_part.split()
    
    # If only one word, return as-is
    if len(words) == 1:
        return generic_part
    
    # Filter out modifier words (but keep organic, gluten-free, etc. as they're attributes)
    core_words = []
    for word in words:
        word_lower = word.lower()
        # Keep words that are NOT simple modifiers
        if word_lower not in modifiers:
            core_words.append(word)
    
    # Return filtered words or original if all were modifiers
    if core_words:
        return ' '.join(core_words)
    else:
        return generic_part


def extract_keywords(item_name: str) -> List[str]:
    """Extract keywords from item name for matching."""
    # Convert to lowercase and split
    item_lower = item_name.lower()
    
    # Remove special characters but keep alphanumeric and spaces
    cleaned = re.sub(r'[^a-z0-9\s%]', ' ', item_lower)
    
    # Split into words and filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    keywords = [word for word in cleaned.split() if word and word not in stop_words]
    
    return keywords


def detect_attributes(item_name: str) -> Dict[str, bool]:
    """Detect attributes like organic, gluten-free from item name."""
    item_lower = item_name.lower()
    attributes = {}
    
    # Check for organic
    if 'organic' in item_lower:
        attributes['organic'] = True
    
    # Check for gluten-free
    if 'gluten-free' in item_lower or 'gluten free' in item_lower:
        attributes['gluten_free'] = True
    
    # Check for non-GMO
    if 'non-gmo' in item_lower or 'non gmo' in item_lower:
        attributes['non_gmo'] = True
    
    # Check for vegan
    if 'vegan' in item_lower:
        attributes['vegan'] = True
    
    return attributes


def categorize_by_keywords(item_name: str) -> Optional[str]:
    """Categorize item using keyword matching."""
    item_lower = item_name.lower()
    
    # Score each category based on keyword matches
    category_scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in item_lower:
                # Longer keywords get higher scores (more specific)
                score += len(keyword.split())
        
        if score > 0:
            category_scores[category] = score
    
    # Return category with highest score
    if category_scores:
        return max(category_scores, key=category_scores.get)
    
    return None


async def categorize_with_ai(item_name: str) -> str:
    """Categorize item using AI (OpenAI GPT-5) as fallback."""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.error("EMERGENT_LLM_KEY not found in environment")
            return "Miscellaneous"
        
        # Create LLM chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id=f"categorization_{item_name}",
            system_message=f"""You are a grocery categorization expert. 
            Categorize the given item into EXACTLY ONE of these 20 categories:
            {', '.join(VALID_CATEGORIES)}
            
            Respond with ONLY the category name, nothing else."""
        ).with_model("openai", "gpt-5.1")
        
        user_message = UserMessage(
            text=f"Categorize this grocery item: '{item_name}'"
        )
        
        response = await chat.send_message(user_message)
        category = response.strip()
        
        # Validate response is a valid category
        if category in VALID_CATEGORIES:
            logger.info(f"AI categorized '{item_name}' as '{category}'")
            return category
        else:
            logger.warning(f"AI returned invalid category '{category}' for '{item_name}'")
            return "Miscellaneous"
    
    except Exception as e:
        logger.error(f"AI categorization failed for '{item_name}': {str(e)}")
        return "Miscellaneous"


async def categorize_item(item_name: str) -> Tuple[str, List[str], Dict[str, bool], Dict[str, any]]:
    """Main categorization function: keyword first, AI fallback.
    
    Returns:
        Tuple of (category, keywords, attributes, brand_info)
    """
    # Parse brand and generic
    brand_info = parse_brand_and_generic(item_name)
    
    # Extract keywords from the full name
    keywords = extract_keywords(item_name)
    
    # Also extract separate keyword lists for brand and generic
    brand_keywords = extract_keywords(brand_info["brand"]) if brand_info["brand"] else []
    generic_keywords = extract_keywords(brand_info["generic"])
    
    # Detect attributes
    attributes = detect_attributes(item_name)
    
    # Try keyword-based categorization first (use generic for better accuracy)
    category = categorize_by_keywords(brand_info["generic"])
    
    if category:
        logger.info(f"Keyword categorized '{item_name}' as '{category}'")
        return category, keywords, attributes, {
            **brand_info,
            "brand_keywords": brand_keywords,
            "generic_keywords": generic_keywords
        }
    
    # Fallback to AI categorization
    logger.info(f"Using AI fallback for '{item_name}'")
    category = await categorize_with_ai(item_name)
    
    return category, keywords, attributes, {
        **brand_info,
        "brand_keywords": brand_keywords,
        "generic_keywords": generic_keywords
    }
