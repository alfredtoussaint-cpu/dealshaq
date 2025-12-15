#!/usr/bin/env python3
"""
Test script for categorization service
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from categorization_service import categorize_item

async def test_categorization():
    """Test various items for categorization"""
    
    test_items = [
        "Organic 2% Milk",
        "Granola",
        "Honeycrisp Apples",
        "Greek Yogurt",
        "Whole Wheat Bread",
        "Gluten-Free Pasta",
        "Organic Bananas",
        "2% Milk",
        "Cat Food"
    ]
    
    print("=" * 70)
    print("CATEGORIZATION SERVICE TEST")
    print("=" * 70)
    
    for item in test_items:
        category, keywords, attributes = await categorize_item(item)
        
        print(f"\nItem: {item}")
        print(f"  Category: {category}")
        print(f"  Keywords: {keywords}")
        print(f"  Attributes: {attributes}")
        print("-" * 70)
    
    print("\n✅ Categorization test completed successfully!\n")

if __name__ == "__main__":
    asyncio.run(test_categorization())
