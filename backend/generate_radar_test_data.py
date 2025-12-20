#!/usr/bin/env python3
"""
DealShaq Radar View Test Data Generator
Creates specific test data for Radar View screenshots:
- 1 DAC (consumer) 
- 6 DRLPs on DAC's DACDRLP-List
- 4 DRLPs have RSHDs (2, 3, 4, 5 deals respectively)
- 2 DRLPs have no RSHDs yet
"""

import asyncio
import os
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'dealshaq_db')

# 6 Retailers for the test
TEST_RETAILERS = [
    {"name": "Fresh Valley Market", "address": "100 Main St, San Francisco, CA"},
    {"name": "Green Leaf Grocers", "address": "200 Oak Ave, San Francisco, CA"},
    {"name": "Sunny Side Foods", "address": "300 Pine St, San Francisco, CA"},
    {"name": "Harbor Fresh Market", "address": "400 Bay Blvd, San Francisco, CA"},
    {"name": "Golden Gate Grocery", "address": "500 Golden Gate Ave, San Francisco, CA"},  # No deals
    {"name": "Pacific Produce Co", "address": "600 Ocean Ave, San Francisco, CA"},  # No deals
]

# RSHDs per retailer: [2, 3, 4, 5, 0, 0]
RSHD_COUNTS = [2, 3, 4, 5, 0, 0]

# Sample items for creating RSHDs
SAMPLE_ITEMS = [
    {"name": "Organic Honeycrisp Apples", "category": "Fruits", "price": 5.99},
    {"name": "Fresh Atlantic Salmon", "category": "Seafood", "price": 12.99},
    {"name": "Organic 2% Milk", "category": "Dairy & Eggs", "price": 6.99},
    {"name": "Artisan Sourdough Bread", "category": "Bakery & Bread", "price": 4.99},
    {"name": "Baby Spinach Salad Mix", "category": "Vegetables", "price": 3.99},
    {"name": "Premium Ground Beef", "category": "Meat & Poultry", "price": 8.99},
    {"name": "Greek Yogurt Variety Pack", "category": "Dairy & Eggs", "price": 7.49},
    {"name": "Fresh Blueberries", "category": "Fruits", "price": 4.99},
    {"name": "Organic Free-Range Eggs", "category": "Dairy & Eggs", "price": 5.49},
    {"name": "Whole Grain Pasta", "category": "Pasta, Rice & Grains", "price": 2.99},
    {"name": "Extra Virgin Olive Oil", "category": "Oils, Sauces & Spices", "price": 9.99},
    {"name": "Sparkling Water 12-Pack", "category": "Beverages", "price": 6.99},
    {"name": "Organic Chicken Breast", "category": "Meat & Poultry", "price": 11.99},
    {"name": "Fresh Avocados (4 pack)", "category": "Fruits", "price": 5.99},
]

SF_LOCATION = {"lat": 37.7749, "lng": -122.4194}


def calculate_discount(price, level):
    """Calculate discount based on level (1-3)"""
    discount_map = {1: 50, 2: 60, 3: 75}
    discount_pct = discount_map.get(level, 50)
    deal_price = round(price * (1 - discount_pct / 100), 2)
    return discount_pct, deal_price


async def generate_radar_test_data():
    """Generate test data for Radar View screenshots"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🚀 Generating Radar View Test Data...")
    print(f"Database: {DB_NAME}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Create the Test Consumer (DAC)
    print("\n👤 Creating test consumer...")
    dac_id = str(uuid4())
    dac_user = {
        "id": dac_id,
        "email": "radar.test@dealshaq.com",
        "password_hash": pwd_context.hash("RadarTest123"),
        "name": "Sarah Johnson",
        "role": "DAC",
        "delivery_location": {
            "address": "San Francisco, CA",
            "lat": SF_LOCATION["lat"],
            "lng": SF_LOCATION["lng"]
        },
        "dacsai_rad": 5.0,
        "favorite_items": [],
        "notification_prefs": {"email": True, "push": True, "sms": False},
        "created_at": now
    }
    
    # Remove existing test user if present
    await db.users.delete_many({"email": "radar.test@dealshaq.com"})
    await db.users.insert_one(dac_user)
    print(f"  ✅ radar.test@dealshaq.com / RadarTest123")
    
    # 2. Create 6 Retailers
    print("\n🏪 Creating 6 retailers...")
    drlp_data = []
    
    for i, retailer in enumerate(TEST_RETAILERS):
        drlp_id = str(uuid4())
        email = f"radartest.retailer{i+1}@dealshaq.com"
        
        # Remove existing if present
        await db.users.delete_many({"email": email})
        
        # Create DRLP user
        await db.users.insert_one({
            "id": drlp_id,
            "email": email,
            "password_hash": pwd_context.hash("TestPassword123"),
            "name": retailer["name"],
            "role": "DRLP",
            "created_at": now
        })
        
        # Remove existing location if present
        await db.drlp_locations.delete_many({"drlp_name": retailer["name"]})
        
        # Create DRLP location
        location_id = str(uuid4())
        await db.drlp_locations.insert_one({
            "id": location_id,
            "drlp_id": drlp_id,
            "user_id": drlp_id,  # Also add user_id for compatibility
            "drlp_name": retailer["name"],
            "name": retailer["name"],
            "address": retailer["address"],
            "location": SF_LOCATION,
            "drlpdac_list": [dac_id],  # Add the DAC to retailer's list
            "created_at": now
        })
        
        drlp_data.append({
            "id": drlp_id,
            "name": retailer["name"],
            "rshd_count": RSHD_COUNTS[i]
        })
        
        status = f"({RSHD_COUNTS[i]} deals)" if RSHD_COUNTS[i] > 0 else "(no deals yet)"
        print(f"  ✅ {retailer['name']} {status}")
    
    # 3. Create DACDRLP-List for the consumer (add all 6 retailers)
    print("\n🔗 Creating DACDRLP-List with 6 retailers...")
    
    # Remove existing list
    await db.dacdrlp_list.delete_many({"dac_id": dac_id})
    
    retailers_list = []
    for drlp in drlp_data:
        retailers_list.append({
            "drlp_id": drlp["id"],
            "drlp_name": drlp["name"],
            "distance": round(1.5 + len(retailers_list) * 0.3, 1),  # Varying distances
            "inside_dacsai": True,
            "manually_added": False,
            "manually_removed": False,
            "added_at": now
        })
    
    await db.dacdrlp_list.insert_one({
        "id": str(uuid4()),
        "dac_id": dac_id,
        "retailers": retailers_list,
        "dacsai_rad": 5.0,
        "dacsai_center": SF_LOCATION,
        "updated_at": now
    })
    print(f"  ✅ Added 6 retailers to consumer's list")
    
    # 4. Create RSHDs (deals) for 4 retailers
    print("\n🔥 Creating RSHD items (deals)...")
    
    # Remove existing test RSHDs
    for drlp in drlp_data:
        await db.rshd_items.delete_many({"drlp_id": drlp["id"]})
    
    item_index = 0
    total_rshds = 0
    
    for drlp in drlp_data:
        if drlp["rshd_count"] == 0:
            continue
            
        print(f"\n  📦 {drlp['name']} - {drlp['rshd_count']} deals:")
        
        for j in range(drlp["rshd_count"]):
            item = SAMPLE_ITEMS[item_index % len(SAMPLE_ITEMS)]
            item_index += 1
            
            discount_level = (j % 3) + 1  # Cycle through 1, 2, 3
            discount_pct, deal_price = calculate_discount(item["price"], discount_level)
            
            expiry_days = 3 + (j % 5)  # 3-7 days
            expiry_date = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat()
            
            rshd = {
                "id": str(uuid4()),
                "drlp_id": drlp["id"],
                "drlp_name": drlp["name"],
                "name": item["name"],
                "description": f"Fresh {item['name']} - {discount_pct}% off!",
                "category": item["category"],
                "regular_price": item["price"],
                "discount_level": discount_level,
                "drlp_discount_percent": discount_pct + 10,
                "consumer_discount_percent": discount_pct,
                "deal_price": deal_price,
                "quantity": 10 + (j * 5),
                "expiry_date": expiry_date,
                "barcode": f"0012345{item_index:05d}",
                "image_url": None,
                "status": "active",
                "created_at": now
            }
            
            await db.rshd_items.insert_one(rshd)
            total_rshds += 1
            print(f"    ✅ {item['name']} - ${deal_price} ({discount_pct}% off)")
    
    # Summary
    print("\n" + "="*60)
    print("✅ RADAR VIEW TEST DATA COMPLETE!")
    print("="*60)
    print("\n📋 Test Credentials:")
    print("    Consumer Email: radar.test@dealshaq.com")
    print("    Password: RadarTest123")
    print("\n📦 Data Summary:")
    print("    Total Retailers on List: 6")
    print("    Retailers with Deals: 4")
    print("    Retailers without Deals: 2")
    print(f"    Total RSHDs Created: {total_rshds}")
    print("\n🏪 Retailers Detail:")
    for drlp in drlp_data:
        status = f"{drlp['rshd_count']} deals" if drlp['rshd_count'] > 0 else "no deals"
        print(f"    • {drlp['name']}: {status}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(generate_radar_test_data())
