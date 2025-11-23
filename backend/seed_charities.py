import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_charities():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    charities = [
        {
            "id": str(uuid.uuid4()),
            "name": "Feeding America",
            "description": "Fighting hunger across America",
            "logo_url": ""
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Local Food Bank",
            "description": "Supporting local communities with food assistance",
            "logo_url": ""
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Meals on Wheels",
            "description": "Delivering meals to seniors in need",
            "logo_url": ""
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Second Harvest",
            "description": "Rescuing food to feed hungry families",
            "logo_url": ""
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Community Kitchen",
            "description": "Providing hot meals to those in need",
            "logo_url": ""
        }
    ]
    
    # Clear existing
    await db.charities.delete_many({})
    
    # Insert new
    await db.charities.insert_many(charities)
    print(f"Seeded {len(charities)} charities")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_charities())
