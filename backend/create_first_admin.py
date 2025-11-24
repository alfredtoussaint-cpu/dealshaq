#!/usr/bin/env python3
"""
Create the first Admin account for DealShaq

This script should only be run once to bootstrap the first Admin account.
After that, Admins can create additional Admin accounts through the API.

Usage:
    python create_first_admin.py

Security:
    - Only run this on a secure server
    - Change the default password immediately after first login
    - This script should be deleted or secured after initial use
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_first_admin():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Check if any Admin exists
    existing_admin = await db.users.find_one({"role": "Admin"})
    if existing_admin:
        print("❌ Admin account already exists!")
        print(f"   Email: {existing_admin['email']}")
        print(f"   Created: {existing_admin.get('created_at', 'Unknown')}")
        print("\nTo create additional Admins, use the existing Admin account and the API.")
        client.close()
        return
    
    # Prompt for Admin details
    print("=" * 60)
    print("CREATE FIRST ADMIN ACCOUNT FOR DEALSHAQ")
    print("=" * 60)
    
    email = input("\nAdmin Email: ").strip()
    if not email:
        print("❌ Email is required")
        client.close()
        return
    
    name = input("Admin Name: ").strip()
    if not name:
        print("❌ Name is required")
        client.close()
        return
    
    password = input("Admin Password (min 8 chars): ").strip()
    if not password or len(password) < 8:
        print("❌ Password must be at least 8 characters")
        client.close()
        return
    
    confirm_password = input("Confirm Password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        client.close()
        return
    
    # Create Admin account
    admin_account = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": name,
        "role": "Admin",
        "password_hash": pwd_context.hash(password),
        "charity_id": None,
        "delivery_location": None,
        "dacsai_radius": None,
        "notification_prefs": {"email": True, "push": True, "sms": False},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(admin_account)
    
    print("\n" + "=" * 60)
    print("✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nEmail: {email}")
    print(f"Name: {name}")
    print(f"Role: Admin")
    print(f"Account ID: {admin_account['id']}")
    print(f"\n⚠️  IMPORTANT SECURITY NOTES:")
    print("   1. Change this password immediately after first login")
    print("   2. Keep Admin credentials secure")
    print("   3. This script should be secured or deleted")
    print("   4. Use /api/admin/create-admin to create additional Admins")
    print("\n✅ You can now login at: /admin")
    
    client.close()

if __name__ == "__main__":
    print("\n🔐 DealShaq Admin Account Creation\n")
    asyncio.run(create_first_admin())
