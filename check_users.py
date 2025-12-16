#!/usr/bin/env python3
"""
Check existing users in the system
"""

import asyncio
import aiohttp
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://surplus-shop-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def create_test_user():
    async with aiohttp.ClientSession() as session:
        # Try to create a new test user
        test_email = "test.brand.generic@example.com"
        test_password = "TestPassword123"
        
        print(f"📝 Creating test user: {test_email}")
        
        register_response = await session.post(
            f"{API_BASE}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "name": "Brand Generic Tester",
                "role": "DAC",
                "dacsai_radius": 5.0
            },
            headers={"Content-Type": "application/json"}
        )
        
        register_text = await register_response.text()
        print(f"Register Status: {register_response.status}")
        print(f"Register Response: {register_text}")
        
        if register_response.status == 200:
            print("✅ Test user created successfully!")
            
            # Try login
            login_response = await session.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": test_email,
                    "password": test_password,
                    "role": "DAC"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status == 200:
                login_data = await login_response.json()
                print("✅ Login successful!")
                print(f"User ID: {login_data['user']['id']}")
                return test_email, test_password
            else:
                print("❌ Login failed after registration")
                return None, None
        else:
            print("❌ Registration failed!")
            return None, None

if __name__ == "__main__":
    email, password = asyncio.run(create_test_user())
    if email:
        print(f"\n✅ Use these credentials:")
        print(f"Email: {email}")
        print(f"Password: {password}")
    else:
        print("\n❌ Failed to create test user")