#!/usr/bin/env python3
"""
Create a test DAC user directly in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone
import os

# MongoDB connection
mongo_url = "mongodb://localhost:27017"
client = AsyncIOMotorClient(mongo_url)
db = client["dealshaq_db"]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_dac():
    """Create a test DAC user"""
    
    # Check if user already exists
    existing = await db.users.find_one({
        "email": "test.dac@example.com",
        "role": "DAC"
    })
    
    if existing:
        print("Test DAC user already exists")
        return existing["id"]
    
    # Create new user
    user_data = {
        "id": str(uuid.uuid4()),
        "email": "test.dac@example.com",
        "password_hash": pwd_context.hash("TestPassword123"),
        "name": "Test DAC User",
        "role": "DAC",
        "charity_id": None,
        "delivery_location": {
            "address": "123 Test St, Test City, TC 12345",
            "coordinates": {"lat": 40.7128, "lng": -74.0060}
        },
        "dacsai_radius": 5.0,
        "notification_prefs": {"email": True, "push": True, "sms": False},
        "favorite_items": [],
        "auto_favorite_threshold": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_data)
    print(f"Created test DAC user: {user_data['email']} with ID: {user_data['id']}")
    
    return user_data["id"]

async def main():
    user_id = await create_test_dac()
    client.close()
    return user_id

if __name__ == "__main__":
    asyncio.run(main())