"""
Barcode and OCR Service for DealShaq
- Barcode lookup via Open Food Facts API (free, no key required)
- OCR via OpenAI GPT-4 Vision (using Emergent LLM Key)
"""

import os
import httpx
import base64
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Open Food Facts API endpoint
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v2/product"


async def lookup_barcode(barcode: str) -> Dict[str, Any]:
    """
    Look up product information from Open Food Facts API by barcode.
    
    Args:
        barcode: Product barcode (e.g., '3017620422003')
    
    Returns:
        Dict with product info or error message
    """
    url = f"{OPEN_FOOD_FACTS_API}/{barcode}.json"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params={'lc': 'en'})
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 1 and data.get('product'):
                product = data['product']
                
                # Map to DealShaq item format
                return {
                    "success": True,
                    "product": {
                        "name": product.get('product_name', product.get('product_name_en', '')),
                        "brand": product.get('brands', ''),
                        "category": map_category(product.get('categories_tags', [])),
                        "barcode": barcode,
                        "weight": extract_weight(product),
                        "description": product.get('generic_name', ''),
                        "image_url": product.get('image_front_url', ''),
                        "ingredients": product.get('ingredients_text_en', product.get('ingredients_text', '')),
                        "nutriscore": product.get('nutriscore_grade', ''),
                        "is_organic": 'en:organic' in product.get('labels_tags', []),
                        "raw_data": {
                            "categories": product.get('categories', ''),
                            "labels": product.get('labels', ''),
                            "quantity": product.get('quantity', ''),
                        }
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Product not found in database",
                    "barcode": barcode
                }
                
    except httpx.TimeoutException:
        logger.error(f"Timeout looking up barcode {barcode}")
        return {"success": False, "error": "Request timed out"}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error looking up barcode {barcode}: {e}")
        return {"success": False, "error": f"API request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Error looking up barcode {barcode}: {e}")
        return {"success": False, "error": str(e)}


def map_category(category_tags: list) -> str:
    """Map Open Food Facts categories to DealShaq categories"""
    
    # DealShaq valid categories
    VALID_CATEGORIES = [
        "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
        "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
        "Snacks & Candy", "Frozen Foods", "Beverages",
        "Deli & Prepared Foods", "Breakfast & Cereal",
        "Pasta, Rice & Grains", "Oils, Sauces & Spices",
        "Baby & Kids", "Health & Nutrition", "Household Essentials",
        "Personal Care", "Pet Supplies", "Miscellaneous"
    ]
    
    # Category mapping from Open Food Facts to DealShaq
    category_map = {
        'fruits': 'Fruits',
        'vegetables': 'Vegetables',
        'meat': 'Meat & Poultry',
        'poultry': 'Meat & Poultry',
        'beef': 'Meat & Poultry',
        'pork': 'Meat & Poultry',
        'chicken': 'Meat & Poultry',
        'fish': 'Seafood',
        'seafood': 'Seafood',
        'dairy': 'Dairy & Eggs',
        'milk': 'Dairy & Eggs',
        'cheese': 'Dairy & Eggs',
        'yogurt': 'Dairy & Eggs',
        'eggs': 'Dairy & Eggs',
        'bread': 'Bakery & Bread',
        'bakery': 'Bakery & Bread',
        'pastries': 'Bakery & Bread',
        'snacks': 'Snacks & Candy',
        'candy': 'Snacks & Candy',
        'chocolate': 'Snacks & Candy',
        'chips': 'Snacks & Candy',
        'frozen': 'Frozen Foods',
        'ice-cream': 'Frozen Foods',
        'beverages': 'Beverages',
        'drinks': 'Beverages',
        'juice': 'Beverages',
        'soda': 'Beverages',
        'water': 'Beverages',
        'coffee': 'Beverages',
        'tea': 'Beverages',
        'deli': 'Deli & Prepared Foods',
        'prepared': 'Deli & Prepared Foods',
        'ready-to-eat': 'Deli & Prepared Foods',
        'cereal': 'Breakfast & Cereal',
        'breakfast': 'Breakfast & Cereal',
        'oatmeal': 'Breakfast & Cereal',
        'pasta': 'Pasta, Rice & Grains',
        'rice': 'Pasta, Rice & Grains',
        'grains': 'Pasta, Rice & Grains',
        'noodles': 'Pasta, Rice & Grains',
        'oil': 'Oils, Sauces & Spices',
        'sauce': 'Oils, Sauces & Spices',
        'spice': 'Oils, Sauces & Spices',
        'condiment': 'Oils, Sauces & Spices',
        'baby': 'Baby & Kids',
        'infant': 'Baby & Kids',
        'health': 'Health & Nutrition',
        'vitamin': 'Health & Nutrition',
        'supplement': 'Health & Nutrition',
        'cleaning': 'Household Essentials',
        'household': 'Household Essentials',
        'personal-care': 'Personal Care',
        'hygiene': 'Personal Care',
        'pet': 'Pet Supplies',
        'dog': 'Pet Supplies',
        'cat': 'Pet Supplies',
    }
    
    # Search for matching category
    for tag in category_tags:
        tag_lower = tag.lower().replace('en:', '')
        for key, value in category_map.items():
            if key in tag_lower:
                return value
    
    return "Miscellaneous"


def extract_weight(product: Dict) -> Optional[float]:
    """Extract weight in pounds from product data"""
    quantity = product.get('quantity', '')
    
    if not quantity:
        return None
    
    import re
    
    # Try to extract weight
    # Match patterns like "500g", "1kg", "16oz", "1lb"
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*kg', lambda x: float(x) * 2.20462),  # kg to lb
        (r'(\d+(?:\.\d+)?)\s*g\b', lambda x: float(x) * 0.00220462),  # g to lb
        (r'(\d+(?:\.\d+)?)\s*oz', lambda x: float(x) * 0.0625),  # oz to lb
        (r'(\d+(?:\.\d+)?)\s*lb', lambda x: float(x)),  # already lb
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, quantity.lower())
        if match:
            try:
                return round(converter(match.group(1)), 2)
            except:
                pass
    
    return None


async def extract_text_from_image(image_base64: str, prompt: str = None) -> Dict[str, Any]:
    """
    Extract text/information from image using OpenAI GPT-4 Vision.
    
    Args:
        image_base64: Base64 encoded image (JPEG, PNG, or WEBP) - raw base64 without data URI prefix
        prompt: Custom prompt for extraction (default: extract price)
    
    Returns:
        Dict with extracted info or error message
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return {"success": False, "error": "EMERGENT_LLM_KEY not configured"}
    
    # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
    if image_base64.startswith('data:'):
        try:
            # Extract just the base64 part after the comma
            image_base64 = image_base64.split(',')[1]
        except IndexError:
            return {"success": False, "error": "Invalid data URI format"}
    
    # Validate base64 string
    try:
        import base64
        # Test decode to validate
        decoded = base64.b64decode(image_base64)
        if len(decoded) < 100:
            return {"success": False, "error": "Image too small or invalid"}
    except Exception as e:
        return {"success": False, "error": f"Invalid base64 encoding: {str(e)}"}
    
    default_prompt = """Analyze this image of a product price tag or receipt.
Extract the following information:
1. Price (the main price shown)
2. Product name (if visible)
3. Any discount or sale information

Return your response in this exact JSON format:
{
    "price": "X.XX",
    "product_name": "name or null",
    "original_price": "X.XX or null if no discount",
    "discount_percentage": "XX or null"
}

Only return the JSON, no other text."""

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"ocr-{os.urandom(8).hex()}",
            system_message="You are a helpful assistant that extracts information from images. Always respond with valid JSON."
        ).with_model("openai", "gpt-4o")
        
        # Create image content with raw base64 (no data URI prefix)
        image_content = ImageContent(image_base64=image_base64)
        
        # Send message with image
        user_message = UserMessage(
            text=prompt or default_prompt,
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Try to parse JSON from response
        import json
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```'):
                clean_response = clean_response.split('\n', 1)[1]
            if clean_response.endswith('```'):
                clean_response = clean_response.rsplit('\n', 1)[0]
            clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            
            extracted_data = json.loads(clean_response)
            return {
                "success": True,
                "extracted": extracted_data,
                "raw_response": response
            }
        except json.JSONDecodeError:
            # Return raw text if not JSON
            return {
                "success": True,
                "extracted": {"raw_text": response},
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return {"success": False, "error": str(e)}


async def analyze_product_image(image_base64: str) -> Dict[str, Any]:
    """
    Analyze a product image to extract product information.
    
    Args:
        image_base64: Base64 encoded image - raw base64 without data URI prefix
    
    Returns:
        Dict with product info or error message
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return {"success": False, "error": "EMERGENT_LLM_KEY not configured"}
    
    # Remove data URI prefix if present
    if image_base64.startswith('data:'):
        try:
            image_base64 = image_base64.split(',')[1]
        except IndexError:
            return {"success": False, "error": "Invalid data URI format"}
    
    # Validate base64 string
    try:
        import base64
        decoded = base64.b64decode(image_base64)
        if len(decoded) < 100:
            return {"success": False, "error": "Image too small or invalid"}
    except Exception as e:
        return {"success": False, "error": f"Invalid base64 encoding: {str(e)}"}
    
    prompt = """Analyze this product image and extract as much information as possible.

Return your response in this exact JSON format:
{
    "product_name": "full product name",
    "brand": "brand name or null",
    "category": "one of: Fruits, Vegetables, Meat & Poultry, Seafood, Dairy & Eggs, Bakery & Bread, Pantry Staples, Snacks & Candy, Frozen Foods, Beverages, Deli & Prepared Foods, Breakfast & Cereal, Pasta Rice & Grains, Oils Sauces & Spices, Baby & Kids, Health & Nutrition, Household Essentials, Personal Care, Pet Supplies, Miscellaneous",
    "weight": "weight with unit or null",
    "is_organic": true or false,
    "description": "brief description"
}

Only return the JSON, no other text."""

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"product-{os.urandom(8).hex()}",
            system_message="You are a helpful assistant that identifies products from images. Always respond with valid JSON."
        ).with_model("openai", "gpt-4o")
        
        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text=prompt,
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        import json
        try:
            clean_response = response.strip()
            if clean_response.startswith('```'):
                clean_response = clean_response.split('\n', 1)[1]
            if clean_response.endswith('```'):
                clean_response = clean_response.rsplit('\n', 1)[0]
            clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            
            extracted_data = json.loads(clean_response)
            return {
                "success": True,
                "product": extracted_data,
                "raw_response": response
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "product": {"raw_text": response},
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error analyzing product image: {e}")
        return {"success": False, "error": str(e)}
