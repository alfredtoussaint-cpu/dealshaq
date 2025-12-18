#!/usr/bin/env python3
"""
Quick authentication test to check if user exists or needs registration
"""

import asyncio
import aiohttp
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://itemfinder-30.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

TEST_EMAIL = "alfred.toussaint@gmail.com"
TEST_PASSWORD = "TestPassword123"
TEST_ROLE = "DAC"

async def test_auth():
    async with aiohttp.ClientSession() as session:
        # Try login first
        print(f"🔐 Trying to login with {TEST_EMAIL}...")
        
        login_response = await session.post(
            f"{API_BASE}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "role": TEST_ROLE
            },
            headers={"Content-Type": "application/json"}
        )
        
        login_text = await login_response.text()
        print(f"Login Status: {login_response.status}")
        print(f"Login Response: {login_text}")
        
        if login_response.status == 200:
            print("✅ User exists and login successful!")
            return True
        
        # If login failed, try registration
        print(f"\n📝 Trying to register {TEST_EMAIL}...")
        
        register_response = await session.post(
            f"{API_BASE}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Alfred Toussaint",
                "role": TEST_ROLE,
                "dacsai_radius": 5.0
            },
            headers={"Content-Type": "application/json"}
        )
        
        register_text = await register_response.text()
        print(f"Register Status: {register_response.status}")
        print(f"Register Response: {register_text}")
        
        if register_response.status == 200:
            print("✅ User registered successfully!")
            return True
        elif register_response.status == 400 and "already registered" in register_text:
            print("⚠️ User already exists but login failed - password issue?")
            return False
        else:
            print("❌ Registration failed!")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_auth())
    print(f"\nResult: {'Success' if success else 'Failed'}")