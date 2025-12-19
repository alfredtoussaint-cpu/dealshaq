#!/usr/bin/env python3
"""
DealShaq Test Data Generator
Generates sample users, retailers, deals, and charities for contractor testing.
"""

import asyncio
import os
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration - loads from backend/.env
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'dealshaq_db')

# Sample locations around San Francisco Bay Area
SAMPLE_LOCATIONS = [
    {"name": "San Francisco", "lat": 37.7749, "lng": -122.4194},
    {"name": "Oakland", "lat": 37.8044, "lng": -122.2712},
    {"name": "Berkeley", "lat": 37.8716, "lng": -122.2727},
    {"name": "San Jose", "lat": 37.3382, "lng": -121.8863},
    {"name": "Palo Alto", "lat": 37.4419, "lng": -122.1430},
]

VALID_CATEGORIES = [
    "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
    "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
    "Snacks & Candy", "Frozen Foods", "Beverages",
    "Deli & Prepared Foods", "Breakfast & Cereal",
    "Pasta, Rice & Grains", "Oils, Sauces & Spices",
    "Baby & Kids", "Health & Nutrition", "Household Essentials",
    "Personal Care", "Pet Supplies", "Miscellaneous"
]

SAMPLE_CHARITIES = [
    {"name": "SF Food Bank", "description": "Feeding families in San Francisco"},
    {"name": "Oakland Community Food", "description": "Fighting hunger in Oakland"},
    {"name": "Bay Area Food Rescue", "description": "Reducing food waste across the Bay"},
    {"name": "Peninsula Pantry", "description": "Supporting families on the Peninsula"},
    {"name": "South Bay Meals", "description": "Providing meals to South Bay communities"},
]

SAMPLE_RETAILERS = [
    {"name": "Fresh Mart Downtown", "city": "San Francisco", "address": "123 Market St"},
    {"name": "Green Grocer SF", "city": "San Francisco", "address": "456 Valencia St"},
    {"name": "Oakland Natural Foods", "city": "Oakland", "address": "789 Broadway"},
    {"name": "Berkeley Organics", "city": "Berkeley", "address": "321 Telegraph Ave"},
    {"name": "Valley Fresh Market", "city": "San Jose", "address": "555 El Camino Real"},
]

SAMPLE_ITEMS = [
    {"name": "Organic Honeycrisp Apples", "category": "Fruits", "price": 5.99, "discount_level": 2},
    {"name": "Fresh Atlantic Salmon", "category": "Seafood", "price": 12.99, "discount_level": 3},
    {"name": "Quaker, Oatmeal", "category": "Breakfast & Cereal", "price": 4.49, "discount_level": 1},
    {"name": "Organic 2% Milk", "category": "Dairy & Eggs", "price": 6.99, "discount_level": 2},
    {"name": "Artisan Sourdough Bread", "category": "Bakery & Bread", "price": 4.99, "discount_level": 3},
    {"name": "Baby Spinach Salad Mix", "category": "Vegetables", "price": 3.99, "discount_level": 1},
    {"name": "Premium Ground Beef", "category": "Meat & Poultry", "price": 8.99, "discount_level": 2},
    {"name": "Organic Greek Yogurt", "category": "Dairy & Eggs", "price": 5.99, "discount_level": 1},
    {"name": "Nature Valley, Granola Bars", "category": "Snacks & Candy", "price": 3.99, "discount_level": 2},
    {"name": "Frozen Pizza Supreme", "category": "Frozen Foods", "price": 7.99, "discount_level": 3},
]


def calculate_discount_mapping(discount_level: int, regular_price: float):
    """Calculate discount percentages based on level"""
    discount_map = {
        1: (60.0, 50.0),  # DRLP: 60%, Consumer: 50%
        2: (75.0, 60.0),  # DRLP: 75%, Consumer: 60%
        3: (90.0, 75.0),  # DRLP: 90%, Consumer: 75%
    }
    drlp_discount, consumer_discount = discount_map.get(discount_level, (60.0, 50.0))
    deal_price = round(regular_price * (1 - consumer_discount / 100), 2)
    return {
        "drlp_discount_percent": drlp_discount,
        "consumer_discount_percent": consumer_discount,
        "deal_price": deal_price
    }


async def generate_test_data():
    """Generate all test data"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🚀 Starting test data generation...")
    print(f"Database: {DB_NAME}")
    
    # Clear existing data (optional - comment out to keep existing)
    # await db.users.delete_many({})
    # await db.charities.delete_many({})
    # await db.rshd_items.delete_many({})
    # await db.drlp_locations.delete_many({})
    # await db.dacdrlp_list.delete_many({})
    # await db.notifications.delete_many({})
    
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Create Charities
    print("\n📦 Creating charities...")
    charity_ids = []
    for charity in SAMPLE_CHARITIES:
        charity_id = str(uuid4())
        await db.charities.insert_one({
            "id": charity_id,
            "name": charity["name"],
            "description": charity["description"],
            "created_at": now
        })
        charity_ids.append(charity_id)
        print(f"  ✅ {charity['name']}")
    
    # 2. Create Admin User
    print("\n👤 Creating admin user...")
    admin_id = str(uuid4())
    await db.users.insert_one({
        "id": admin_id,
        "email": "admin@dealshaq.com",
        "password_hash": pwd_context.hash("AdminPassword123"),
        "name": "System Administrator",
        "role": "Admin",
        "created_at": now
    })
    print(f"  ✅ admin@dealshaq.com / AdminPassword123")
    
    # 3. Create Retailer Users and Locations
    print("\n🏪 Creating retailers and locations...")
    drlp_ids = []
    for i, retailer in enumerate(SAMPLE_RETAILERS):
        drlp_id = str(uuid4())
        location = SAMPLE_LOCATIONS[i % len(SAMPLE_LOCATIONS)]
        
        # Create DRLP user
        await db.users.insert_one({
            "id": drlp_id,
            "email": f"retailer{i+1}@dealshaq.com",
            "password_hash": pwd_context.hash("TestPassword123"),
            "name": retailer["name"],
            "role": "DRLP",
            "created_at": now
        })
        
        # Create DRLP location
        location_id = str(uuid4())
        await db.drlp_locations.insert_one({
            "id": location_id,
            "drlp_id": drlp_id,
            "drlp_name": retailer["name"],
            "name": retailer["name"],
            "address": f"{retailer['address']}, {retailer['city']}, CA",
            "location": {"lat": location["lat"], "lng": location["lng"]},
            "drlpdac_list": [],  # Will be populated when DACs register
            "created_at": now
        })
        
        drlp_ids.append({"id": drlp_id, "location_id": location_id, "name": retailer["name"]})
        print(f"  ✅ {retailer['name']} - retailer{i+1}@dealshaq.com")
    
    # 4. Create Consumer Users
    print("\n🛒 Creating consumers...")
    dac_ids = []
    for i in range(5):
        dac_id = str(uuid4())
        location = SAMPLE_LOCATIONS[i % len(SAMPLE_LOCATIONS)]
        charity_id = charity_ids[i % len(charity_ids)]
        
        user = {
            "id": dac_id,
            "email": f"consumer{i+1}@dealshaq.com",
            "password_hash": pwd_context.hash("TestPassword123"),
            "name": f"Test Consumer {i+1}",
            "role": "DAC",
            "charity_id": charity_id,
            "delivery_location": {
                "address": f"{location['name']}, CA",
                "lat": location["lat"],
                "lng": location["lng"]
            },
            "dacsai_rad": 5.0 + (i * 0.5),  # Varying radii: 5.0, 5.5, 6.0, 6.5, 7.0
            "favorite_items": [],
            "auto_favorite_threshold": 3 if i % 2 == 0 else 0,
            "notification_prefs": {"email": True, "push": True, "sms": False},
            "created_at": now
        }
        
        await db.users.insert_one(user)
        dac_ids.append({"id": dac_id, "location": location})
        print(f"  ✅ consumer{i+1}@dealshaq.com ({location['name']})")
    
    # 5. Create DACDRLP-Lists for consumers
    print("\n🔗 Creating DACDRLP-Lists...")
    for dac in dac_ids:
        dacdrlp_list = {
            "id": str(uuid4()),
            "dac_id": dac["id"],
            "retailers": [],
            "dacsai_rad": 5.0,
            "dacsai_center": {"lat": dac["location"]["lat"], "lng": dac["location"]["lng"]},
            "updated_at": now
        }
        
        # Add nearby retailers to list (simplified - add all for testing)
        for drlp in drlp_ids[:3]:  # Add first 3 retailers to each DAC
            dacdrlp_list["retailers"].append({
                "drlp_id": drlp["id"],
                "drlp_name": drlp["name"],
                "distance": 2.5,  # Simplified
                "inside_dacsai": True,
                "manually_added": False,
                "manually_removed": False,
                "added_at": now
            })
            
            # Update DRLPDAC-List (bidirectional sync)
            await db.drlp_locations.update_one(
                {"drlp_id": drlp["id"]},
                {"$addToSet": {"drlpdac_list": dac["id"]}}
            )
        
        await db.dacdrlp_list.insert_one(dacdrlp_list)
    print(f"  ✅ Created lists for {len(dac_ids)} consumers")
    
    # 6. Add favorite items to consumers
    print("\n⭐ Adding favorite items to consumers...")
    sample_favorites = [
        {"item_name": "Organic Milk", "brand": None, "generic": "Milk", "has_brand": False, "category": "Dairy & Eggs"},
        {"item_name": "Quaker, Oatmeal", "brand": "Quaker", "generic": "Oatmeal", "has_brand": True, "category": "Breakfast & Cereal"},
        {"item_name": "Fresh Salmon", "brand": None, "generic": "Salmon", "has_brand": False, "category": "Seafood"},
        {"item_name": "Honeycrisp Apples", "brand": None, "generic": "Apples", "has_brand": False, "category": "Fruits"},
        {"item_name": "Sourdough Bread", "brand": None, "generic": "Bread", "has_brand": False, "category": "Bakery & Bread"},
    ]
    
    for i, dac in enumerate(dac_ids):
        # Add 2-3 favorites per consumer
        favorites_to_add = sample_favorites[i:i+3] if i < 3 else sample_favorites[:2]
        for fav in favorites_to_add:
            await db.users.update_one(
                {"id": dac["id"]},
                {"$push": {"favorite_items": {
                    **fav,
                    "keywords": [fav["generic"].lower()],
                    "attributes": {"organic": "organic" in fav["item_name"].lower()},
                    "added_at": now
                }}}
            )
    print(f"  ✅ Added favorites to {len(dac_ids)} consumers")
    
    # 7. Create RSHD Items
    print("\n🔥 Creating RSHD items (deals)...")
    for i, item in enumerate(SAMPLE_ITEMS):
        drlp = drlp_ids[i % len(drlp_ids)]
        discount_info = calculate_discount_mapping(item["discount_level"], item["price"])
        
        expiry_days = 3 + (i % 7)  # Expiry between 3-9 days
        expiry_date = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat()
        
        rshd = {
            "id": str(uuid4()),
            "drlp_id": drlp["id"],
            "drlp_name": drlp["name"],
            "name": item["name"],
            "category": item["category"],
            "regular_price": item["price"],
            "discount_level": item["discount_level"],
            "drlp_discount_percent": discount_info["drlp_discount_percent"],
            "consumer_discount_percent": discount_info["consumer_discount_percent"],
            "deal_price": discount_info["deal_price"],
            "quantity": 10 + (i * 5),
            "expiry_date": expiry_date,
            "status": "active",
            "created_at": now
        }
        
        await db.rshd_items.insert_one(rshd)
        print(f"  ✅ {item['name']} @ {discount_info['consumer_discount_percent']}% off (${discount_info['deal_price']})")
    
    # 8. Create some sample notifications
    print("\n🔔 Creating sample notifications...")
    items_cursor = db.rshd_items.find({}, {"_id": 0}).limit(5)
    items = await items_cursor.to_list(5)
    
    for i, item in enumerate(items):
        dac = dac_ids[i % len(dac_ids)]
        notification = {
            "id": str(uuid4()),
            "dac_id": dac["id"],
            "rshd_id": item["id"],
            "type": "rshd_match",
            "title": f"🔥 New Deal: {item['name']}",
            "message": f"{item['consumer_discount_percent']}% OFF at {item['drlp_name']}!",
            "data": {
                "item_name": item["name"],
                "discount": item["consumer_discount_percent"],
                "deal_price": item["deal_price"]
            },
            "is_read": False,
            "created_at": now
        }
        await db.notifications.insert_one(notification)
    print(f"  ✅ Created {len(items)} notifications")
    
    # Summary
    print("\n" + "="*50)
    print("✅ TEST DATA GENERATION COMPLETE!")
    print("="*50)
    print("\n📋 Test Credentials:")
    print("\n  Admin:")
    print("    Email: admin@dealshaq.com")
    print("    Password: AdminPassword123")
    print("\n  Retailers (5):")
    for i in range(5):
        print(f"    Email: retailer{i+1}@dealshaq.com")
    print("    Password: TestPassword123 (all)")
    print("\n  Consumers (5):")
    for i in range(5):
        print(f"    Email: consumer{i+1}@dealshaq.com")
    print("    Password: TestPassword123 (all)")
    print("\n📦 Data Created:")
    print(f"    Charities: {len(SAMPLE_CHARITIES)}")
    print(f"    Retailers: {len(SAMPLE_RETAILERS)}")
    print(f"    Consumers: 5")
    print(f"    RSHD Items: {len(SAMPLE_ITEMS)}")
    print(f"    DRLP Locations: {len(SAMPLE_RETAILERS)}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(generate_test_data())
