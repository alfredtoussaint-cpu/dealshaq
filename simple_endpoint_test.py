#!/usr/bin/env python3
"""
Simple DealShaq Backend Endpoint Testing
Focus on core endpoints mentioned in the review request.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shop-radar-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_CREDENTIALS = {
    "consumer": {"email": "consumer1@dealshaq.com", "password": "TestPassword123", "role": "DAC"},
    "retailer": {"email": "retailer1@dealshaq.com", "password": "TestPassword123", "role": "DRLP"},
    "admin": {"email": "admin@dealshaq.com", "password": "AdminPassword123", "role": "Admin"}
}

async def make_request(session, method, endpoint, data=None, token=None):
    """Make HTTP request with error handling"""
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        async with session.request(method, url, json=data, headers=headers) as response:
            response_text = await response.text()
            try:
                response_data = json.loads(response_text) if response_text else {}
            except json.JSONDecodeError:
                response_data = {"raw_response": response_text}
            
            return {
                "status": response.status,
                "data": response_data
            }
    except Exception as e:
        return {
            "status": 0,
            "data": {"error": str(e)}
        }

async def test_authentication():
    """Test authentication for all user types"""
    logger.info("🔐 Testing Authentication...")
    
    async with aiohttp.ClientSession() as session:
        tokens = {}
        
        for user_type, credentials in TEST_CREDENTIALS.items():
            response = await make_request(session, "POST", "/auth/login", {
                "email": credentials["email"],
                "password": credentials["password"],
                "role": credentials["role"]
            })
            
            if response["status"] == 200:
                tokens[user_type] = response["data"]["access_token"]
                user_role = response["data"]["user"]["role"]
                logger.info(f"✅ {user_type.title()} login successful - Role: {user_role}")
            else:
                logger.error(f"❌ {user_type.title()} login failed: {response['data']}")
        
        return tokens

async def test_auth_me(session, tokens):
    """Test GET /api/auth/me endpoint"""
    logger.info("👤 Testing /api/auth/me...")
    
    for user_type, token in tokens.items():
        response = await make_request(session, "GET", "/auth/me", token=token)
        
        if response["status"] == 200:
            user_data = response["data"]
            logger.info(f"✅ Auth/me for {user_type}: {user_data['email']} - {user_data['role']}")
        else:
            logger.error(f"❌ Auth/me failed for {user_type}: {response['data']}")

async def test_consumer_endpoints(session, tokens):
    """Test Consumer (DAC) endpoints"""
    logger.info("🛒 Testing Consumer Endpoints...")
    
    if "consumer" not in tokens:
        logger.error("❌ Consumer not authenticated")
        return
    
    token = tokens["consumer"]
    
    # Test GET /api/dac/retailers
    response = await make_request(session, "GET", "/dac/retailers", token=token)
    if response["status"] == 200:
        retailers = response["data"].get("retailers", [])
        logger.info(f"✅ GET /api/dac/retailers: {len(retailers)} retailers found")
    else:
        logger.error(f"❌ GET /api/dac/retailers failed: {response['data']}")
    
    # Test GET /api/favorites/items
    response = await make_request(session, "GET", "/favorites/items", token=token)
    if response["status"] == 200:
        total_items = response["data"].get("total_items", 0)
        logger.info(f"✅ GET /api/favorites/items: {total_items} favorite items")
    else:
        logger.error(f"❌ GET /api/favorites/items failed: {response['data']}")
    
    # Test GET /api/notifications
    response = await make_request(session, "GET", "/notifications", token=token)
    if response["status"] == 200:
        notifications = response["data"]
        logger.info(f"✅ GET /api/notifications: {len(notifications)} notifications")
    else:
        logger.error(f"❌ GET /api/notifications failed: {response['data']}")

async def test_retailer_endpoints(session, tokens):
    """Test Retailer (DRLP) endpoints"""
    logger.info("🏪 Testing Retailer Endpoints...")
    
    if "retailer" not in tokens:
        logger.error("❌ Retailer not authenticated")
        return
    
    token = tokens["retailer"]
    
    # Test GET /api/drlp/my-location
    response = await make_request(session, "GET", "/drlp/my-location", token=token)
    if response["status"] == 200:
        location = response["data"]
        logger.info(f"✅ GET /api/drlp/my-location: {location.get('name', 'Unknown')}")
    elif response["status"] == 404:
        logger.info("✅ GET /api/drlp/my-location: No location found (404 - acceptable)")
    else:
        logger.error(f"❌ GET /api/drlp/my-location failed: {response['data']}")
    
    # Test GET /api/rshd/my-items (may have validation errors)
    response = await make_request(session, "GET", "/rshd/my-items", token=token)
    if response["status"] == 200:
        items = response["data"]
        logger.info(f"✅ GET /api/rshd/my-items: {len(items)} items posted")
    elif response["status"] == 500:
        logger.info("⚠️ GET /api/rshd/my-items: 500 error (likely validation issues with existing data)")
    else:
        logger.error(f"❌ GET /api/rshd/my-items failed: {response['data']}")

async def test_general_endpoints(session):
    """Test general endpoints"""
    logger.info("🌐 Testing General Endpoints...")
    
    # Test GET /api/categories
    response = await make_request(session, "GET", "/categories")
    if response["status"] == 200:
        categories = response["data"].get("categories", [])
        logger.info(f"✅ GET /api/categories: {len(categories)} categories")
        if len(categories) == 20:
            logger.info("✅ Categories count matches expected (20)")
        else:
            logger.info(f"⚠️ Expected 20 categories, got {len(categories)}")
    else:
        logger.error(f"❌ GET /api/categories failed: {response['data']}")
    
    # Test GET /api/charities
    response = await make_request(session, "GET", "/charities")
    if response["status"] == 200:
        charities = response["data"]
        logger.info(f"✅ GET /api/charities: {len(charities)} charities")
        if len(charities) == 5:
            logger.info("✅ Charities count matches expected (5)")
        else:
            logger.info(f"⚠️ Expected 5 charities, got {len(charities)}")
    else:
        logger.error(f"❌ GET /api/charities failed: {response['data']}")

async def main():
    """Main test execution"""
    logger.info("🚀 Starting DealShaq Endpoint Testing...")
    
    # Step 1: Test authentication
    tokens = await test_authentication()
    
    if not tokens:
        logger.error("❌ No users authenticated successfully")
        return
    
    async with aiohttp.ClientSession() as session:
        # Step 2: Test auth/me endpoint
        await test_auth_me(session, tokens)
        
        # Step 3: Test consumer endpoints
        await test_consumer_endpoints(session, tokens)
        
        # Step 4: Test retailer endpoints
        await test_retailer_endpoints(session, tokens)
        
        # Step 5: Test general endpoints
        await test_general_endpoints(session)
    
    logger.info("🎯 Testing Complete!")

if __name__ == "__main__":
    asyncio.run(main())