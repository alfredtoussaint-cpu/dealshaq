#!/usr/bin/env python3
"""
Test script for brand/generic name parsing
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from categorization_service import parse_brand_and_generic, categorize_item

async def test_brand_generic_parsing():
    """Test various brand/generic input formats"""
    
    test_cases = [
        {
            "input": "Quaker, Simply Granola",
            "expected_brand": "Quaker",
            "expected_generic": "Granola",
            "description": "Brand with modifier in generic"
        },
        {
            "input": "Quaker Simply, Granola",
            "expected_brand": "Quaker Simply",
            "expected_generic": "Granola",
            "description": "Multi-word brand"
        },
        {
            "input": "Quaker, Granola",
            "expected_brand": "Quaker",
            "expected_generic": "Granola",
            "description": "Simple brand + generic"
        },
        {
            "input": "Granola",
            "expected_brand": None,
            "expected_generic": "Granola",
            "description": "Generic only (any brand)"
        },
        {
            "input": "Valley Farm, 2% Milk",
            "expected_brand": "Valley Farm",
            "expected_generic": "2% Milk",
            "description": "Brand with percentage in generic"
        },
        {
            "input": "Organic 2% Milk",
            "expected_brand": None,
            "expected_generic": "Organic 2% Milk",
            "description": "Organic without brand"
        },
        {
            "input": "Dannon, Greek Yogurt",
            "expected_brand": "Dannon",
            "expected_generic": "Greek Yogurt",
            "description": "Brand with multi-word generic"
        },
    ]
    
    print("=" * 80)
    print("BRAND/GENERIC NAME PARSING TEST")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = parse_brand_and_generic(test["input"])
        
        brand_match = result["brand"] == test["expected_brand"]
        generic_match = result["generic"] == test["expected_generic"]
        
        status = "✅ PASS" if (brand_match and generic_match) else "❌ FAIL"
        
        if brand_match and generic_match:
            passed += 1
        else:
            failed += 1
        
        print(f"\nTest {i}: {test['description']}")
        print(f"  Input: '{test['input']}'")
        print(f"  Expected: Brand='{test['expected_brand']}', Generic='{test['expected_generic']}'")
        print(f"  Got:      Brand='{result['brand']}', Generic='{result['generic']}'")
        print(f"  has_brand: {result['has_brand']}")
        print(f"  Status: {status}")
        print("-" * 80)
    
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'=' * 80}\n")
    
    # Test full categorization with brand/generic
    print("\n" + "=" * 80)
    print("FULL CATEGORIZATION TEST (with brand/generic)")
    print("=" * 80)
    
    full_test_items = [
        "Quaker, Simply Granola",
        "Valley Farm, 2% Milk",
        "Granola"
    ]
    
    for item in full_test_items:
        category, keywords, attributes, brand_info = await categorize_item(item)
        
        print(f"\nItem: {item}")
        print(f"  Category: {category}")
        print(f"  Brand: {brand_info.get('brand')}")
        print(f"  Generic: {brand_info.get('generic')}")
        print(f"  has_brand: {brand_info.get('has_brand')}")
        print(f"  Keywords: {keywords}")
        print(f"  Brand Keywords: {brand_info.get('brand_keywords')}")
        print(f"  Generic Keywords: {brand_info.get('generic_keywords')}")
        print(f"  Attributes: {attributes}")
        print("-" * 80)
    
    print("\n✅ Brand/Generic parsing test completed!\n")

if __name__ == "__main__":
    asyncio.run(test_brand_generic_parsing())
