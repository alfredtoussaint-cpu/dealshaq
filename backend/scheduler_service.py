from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
import logging
from typing import Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)


async def process_auto_add_favorites(db):
    """Daily job to auto-add items to DACFI-List based on purchase history.
    
    Runs at 11 PM daily.
    Checks last 21 days of purchases for each DAC.
    Adds items purchased on threshold days (3 or 6 separate days).
    """
    logger.info("Starting auto-add favorites job")
    
    try:
        # Get all DACs with auto_favorite_threshold > 0
        users = await db.users.find(
            {"role": "DAC", "auto_favorite_threshold": {"$gt": 0}},
            {"_id": 0}
        ).to_list(10000)
        
        logger.info(f"Found {len(users)} DACs with auto-add enabled")
        
        # Calculate 21 days ago
        twenty_one_days_ago = datetime.now(timezone.utc) - timedelta(days=21)
        
        for user in users:
            dac_id = user["id"]
            threshold = user["auto_favorite_threshold"]
            
            logger.info(f"Processing DAC {dac_id} with threshold {threshold}")
            
            # Get orders from last 21 days
            orders = await db.orders.find(
                {
                    "dac_id": dac_id,
                    "created_at": {"$gte": twenty_one_days_ago.isoformat()}
                },
                {"_id": 0}
            ).to_list(10000)
            
            if not orders:
                logger.info(f"No orders found for DAC {dac_id} in last 21 days")
                continue
            
            # Get current favorite items
            current_favorites = user.get("favorite_items", [])
            favorite_item_names = {fav["item_name"].lower() for fav in current_favorites}
            
            # Track unique days each item was purchased
            # Structure: {item_name: {category: str, dates: set()}}
            item_purchase_days = defaultdict(lambda: {"category": None, "dates": set()})
            
            for order in orders:
                order_date = datetime.fromisoformat(order["created_at"]).date()
                
                for item in order["items"]:
                    item_name = item["name"]
                    item_name_lower = item_name.lower()
                    
                    # Skip if already in favorites
                    if item_name_lower in favorite_item_names:
                        continue
                    
                    # Get item details from rshd_items to find category
                    rshd_item = await db.rshd_items.find_one(
                        {"id": item["rshd_id"]},
                        {"_id": 0, "category": 1}
                    )
                    
                    if rshd_item:
                        item_purchase_days[item_name]["category"] = rshd_item["category"]
                        item_purchase_days[item_name]["dates"].add(order_date)
            
            # Find items that meet the threshold
            items_to_add = []
            
            for item_name, data in item_purchase_days.items():
                unique_days = len(data["dates"])
                
                if unique_days >= threshold:
                    # Extract keywords for matching
                    from categorization_service import extract_keywords, detect_attributes
                    
                    keywords = extract_keywords(item_name)
                    attributes = detect_attributes(item_name)
                    
                    items_to_add.append({
                        "item_name": item_name,
                        "category": data["category"],
                        "keywords": keywords,
                        "attributes": attributes,
                        "auto_added_date": datetime.now(timezone.utc).isoformat()
                    })
                    
                    logger.info(
                        f"Auto-adding '{item_name}' for DAC {dac_id} "
                        f"(purchased on {unique_days} separate days)"
                    )
            
            # Update user's favorite_items
            if items_to_add:
                result = await db.users.update_one(
                    {"id": dac_id},
                    {"$push": {"favorite_items": {"$each": items_to_add}}}
                )
                
                logger.info(
                    f"Added {len(items_to_add)} items to DAC {dac_id}'s DACFI-List"
                )
        
        logger.info("Auto-add favorites job completed successfully")
    
    except Exception as e:
        logger.error(f"Error in auto-add favorites job: {str(e)}", exc_info=True)


def start_scheduler(db):
    """Initialize and start the APScheduler."""
    scheduler = AsyncIOScheduler()
    
    # Schedule daily job at 11 PM (23:00)
    scheduler.add_job(
        process_auto_add_favorites,
        trigger=CronTrigger(hour=23, minute=0),
        args=[db],
        id="auto_add_favorites",
        name="Auto-add favorite items based on purchase history",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started - Auto-add job scheduled for 11 PM daily")
    
    return scheduler
