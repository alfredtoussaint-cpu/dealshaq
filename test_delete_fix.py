#!/usr/bin/env python3
"""
Test the delete functionality to understand the issue
"""

import asyncio
import aiohttp
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shop-radar-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

TEST_EMAIL = "test.brand.generic@example.com"
TEST_PASSWORD = "TestPassword123"

async def test_delete_functionality():
    async with aiohttp.ClientSession() as session:
        # Login first
        login_response = await session.post(
            f"{API_BASE}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "role": "DAC"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status != 200:
            print("❌ Login failed")
            return
        
        login_data = await login_response.json()
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Get current favorites
        get_response = await session.get(f"{API_BASE}/favorites/items", headers=headers)
        if get_response.status == 200:
            data = await get_response.json()
            items_by_category = data.get("items_by_category", {})
            
            print("📋 Current favorites:")
            for category, items in items_by_category.items():
                for item in items:
                    print(f"  - {item['item_name']} (Category: {category})")
            
            # Try to delete the first item we find
            if items_by_category:
                first_category = list(items_by_category.keys())[0]
                first_item = items_by_category[first_category][0]
                item_name = first_item["item_name"]
                
                print(f"\n🗑️ Trying to delete: {item_name}")
                
                # Test the original DELETE endpoint
                delete_response1 = await session.delete(
                    f"{API_BASE}/favorites/items",
                    json={"item_name": item_name},
                    headers=headers
                )
                
                print(f"Original DELETE endpoint status: {delete_response1.status}")
                if delete_response1.status != 200:
                    delete_text1 = await delete_response1.text()
                    print(f"Original DELETE response: {delete_text1}")
                
                # Test the alternative DELETE endpoint with query parameter
                delete_response2 = await session.delete(
                    f"{API_BASE}/favorites/items/remove?item_name={item_name}",
                    headers=headers
                )
                
                print(f"Alternative DELETE endpoint status: {delete_response2.status}")
                delete_text2 = await delete_response2.text()
                print(f"Alternative DELETE response: {delete_text2}")
                
        else:
            print("❌ Failed to get favorites")

if __name__ == "__main__":
    asyncio.run(test_delete_functionality())