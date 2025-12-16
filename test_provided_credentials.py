#!/usr/bin/env python3
"""
Test with the provided credentials from the review request
"""

import asyncio
import aiohttp
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://surplus-shop-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Provided credentials from review request
PROVIDED_EMAIL = "alfred.toussaint@gmail.com"
PROVIDED_PASSWORD = "TestPassword123"

async def test_provided_credentials():
    async with aiohttp.ClientSession() as session:
        print(f"🔐 Testing provided credentials: {PROVIDED_EMAIL}")
        
        # Try login
        login_response = await session.post(
            f"{API_BASE}/auth/login",
            json={
                "email": PROVIDED_EMAIL,
                "password": PROVIDED_PASSWORD,
                "role": "DAC"
            },
            headers={"Content-Type": "application/json"}
        )
        
        login_text = await login_response.text()
        print(f"Login Status: {login_response.status}")
        print(f"Login Response: {login_text}")
        
        if login_response.status == 200:
            print("✅ Provided credentials work!")
            login_data = await login_response.json()
            user = login_data["user"]
            print(f"User ID: {user['id']}")
            print(f"User Name: {user['name']}")
            
            # Test adding a brand/generic item
            token = login_data["access_token"]
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            add_response = await session.post(
                f"{API_BASE}/favorites/items",
                json={"item_name": "Quaker, Simply Granola"},
                headers=headers
            )
            
            if add_response.status == 200:
                add_data = await add_response.json()
                item = add_data["item"]
                print(f"\n✅ Successfully added brand/generic item:")
                print(f"  Brand: {item.get('brand')}")
                print(f"  Generic: {item.get('generic')}")
                print(f"  Has Brand: {item.get('has_brand')}")
                print(f"  Category: {item.get('category')}")
                return True
            else:
                add_text = await add_response.text()
                print(f"\n❌ Failed to add item: {add_response.status} - {add_text}")
                return False
        else:
            print("❌ Provided credentials don't work")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_provided_credentials())
    print(f"\nResult: {'Success' if success else 'Failed'}")