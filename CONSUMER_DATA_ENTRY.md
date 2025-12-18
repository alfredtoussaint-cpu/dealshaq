# DealShaq Consumer (DAC) Onboarding & Data Entry Workflow

## Overview
Enable DACs to quickly set up their shopping preferences and local retailer relationships for targeted, efficient deal notifications.

## Key Definitions

### DACSAI (DAC's Shopping Area of Interest)
The **circular geographical AREA** around the DAC's delivery location, defined by:
- **Center:** DAC's delivery location (geocoded coordinates)
- **Radius:** DACSAI-Rad (0.1 to 9.9 miles)

### DACSAI-Rad (DACSAI Radius)
The **radius value** (0.1 to 9.9 miles) that determines the size of the DACSAI. Measured from the DAC's delivery location.

### DACDRLP-List (DAC's DRLP List)
The list of DRLPs the DAC wants to receive notifications from:
- **Formula:** `DRLPs domiciled inside DACSAI` + `Manually added DRLPs outside DACSAI` - `Manually removed DRLPs inside DACSAI`
- **Bidirectional Sync:** Must be kept in sync with each DRLP's DRLPDAC-List

### DRLPDAC-List (DRLP's DAC List)
The list of DACs who should receive notifications from a specific DRLP:
- Contains all DACs who have this DRLP in their DACDRLP-List
- **Bidirectional Sync Required:**
  - When DAC adds DRLP → Add DAC to that DRLP's DRLPDAC-List
  - When DAC removes DRLP → Remove DAC from that DRLP's DRLPDAC-List

## Goals
1. **Fast Onboarding**: Complete setup in < 5 minutes
2. **Item-Level Preferences**: Build DACFI-List with specific items (brand/generic)
3. **Geographic Control**: Define DACSAI via delivery location + DACSAI-Rad
4. **Retailer Control**: Manage DACDRLP-List (add/remove retailers)
5. **Targeted Notifications**: Receive only relevant offers from chosen retailers

## Workflow Overview

### Phase 1: Account Creation (1-2 minutes)
**Step 1: Basic Info**
- Email, password, name
- Select preferred charity from list
- Terms of service acceptance

**Step 2: Delivery Location (DACSAI Center)**
- Enter delivery address
- Geocode to coordinates (lat/lng)
- Store as primary delivery location
- This becomes the **center point of the DAC's DACSAI**

**Step 3: Define DACSAI-Rad**
- Set shopping radius: 0.1 - 9.9 miles (default: 5.0 miles)
- Visual map shows the DACSAI (circular area)
- Backend identifies all DRLPs domiciled inside this DACSAI
- Backend initializes DACDRLP-List with these DRLPs
- Backend adds DAC to each of those DRLPs' DRLPDAC-Lists (bidirectional sync)

### Phase 2: DACFI-List Creation (2-3 minutes)
**Build Favorite Items**
- Add specific items: "Organic 2% Milk", "Quaker, Granola"
- Brand-specific items use comma delimiter: "Brand, Item"
- Generic items (any brand OK): Just the item name
- Auto-categorized into 20 categories

**Quick-Add Methods:**
1. **Text Entry**: Type item name directly
2. **Barcode Scan**: Scan items at home (maps to category + extracts item name)
3. **Purchase History**: Auto-add after buying same item on 3 or 6 separate days

**Backend Storage (in users collection):**
```json
{
  "favorite_items": [
    {
      "item_name": "Quaker, Granola",
      "brand": "Quaker",
      "generic": "Granola",
      "has_brand": true,
      "category": "Breakfast & Cereal",
      "keywords": ["quaker", "granola"],
      "attributes": {"organic": false}
    },
    {
      "item_name": "Organic 2% Milk",
      "brand": null,
      "generic": "Organic 2% Milk",
      "has_brand": false,
      "category": "Dairy & Eggs",
      "keywords": ["milk", "2%"],
      "attributes": {"organic": true}
    }
  ]
}
```

### Phase 3: DACDRLP-List Management (Ongoing)
**Initial State:**
- Auto-populated with all DRLPs domiciled inside the DAC's DACSAI
- Each DRLP's DRLPDAC-List is updated to include this DAC (bidirectional sync)
- Shown on map with pins

**Manual Management:**
- ✅ **Add DRLP (outside DACSAI)**: 
  - Add DRLP to DAC's DACDRLP-List
  - Add DAC to that DRLP's DRLPDAC-List (bidirectional sync)
- ❌ **Remove DRLP (inside DACSAI)**:
  - Remove DRLP from DAC's DACDRLP-List
  - Remove DAC from that DRLP's DRLPDAC-List (bidirectional sync)
- 🔒 **Overrides Preserved**: 
  - Removed DRLPs never auto-added back (even if inside DACSAI)
  - Manually added DRLPs always kept (even if outside DACSAI)

**Visual Tools:**
- **Map View**: Geographic display showing DACSAI circle and DRLPs
- **List View**: Sortable table with distance, name, add/remove controls
- **Radar View**: Live feed of RSHDs from DRLPs in DACDRLP-List

## Detailed Workflows

### 1. DACSAI (Shopping Area of Interest) Setup

**UI Component:**
```
┌─────────────────────────────────────┐
│  Set Your Shopping Area             │
├─────────────────────────────────────┤
│  Delivery Address:                  │
│  ┌───────────────────────────────┐  │
│  │ 123 Main St, City, State...  │  │
│  └───────────────────────────────┘  │
│                                     │
│  Shopping Radius: [5.0] miles       │
│  ├─────○─────────────────────────┤  │
│  0.1 miles              9.9 miles   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │      [Map Preview]          │   │
│  │   • Your Location (center)  │   │
│  │   ○ Radius Circle           │   │
│  │   📍 DRLPs in area          │   │
│  └─────────────────────────────┘   │
│                                     │
│  DRLPs Found: 12                    │
│  [Continue]                         │
└─────────────────────────────────────┘
```

**Validation:**
- Radius: 0.1 ≤ radius ≤ 9.9 miles
- Address: Must be valid and geocodable
- Backend calculates which DRLPs fall within radius

**Backend Logic:**
```python
def initialize_dacdrlp_list(dac_id, location, radius):
    # Get all DRLPs
    all_drlps = await db.drlp_locations.find().to_list(10000)
    
    # Calculate distance for each DRLP
    dac_coords = location["coordinates"]
    local_drlps = []
    
    for drlp in all_drlps:
        drlp_coords = drlp["coordinates"]
        distance = calculate_distance(dac_coords, drlp_coords)
        
        if distance <= radius:
            local_drlps.append({
                "drlp_id": drlp["user_id"],
                "drlp_name": drlp["name"],
                "distance": distance,
                "auto_added": True  # From DACSAI
            })
    
    # Store DACDRLP-List
    await db.dacdrlp_list.insert_one({
        "dac_id": dac_id,
        "retailers": local_drlps,
        "dacsai_radius": radius,
        "dacsai_center": dac_coords
    })
```

### 2. DACFI-List Creation

**UI Component:**
```
┌─────────────────────────────────────┐
│  Build Your Favorites List          │
├─────────────────────────────────────┤
│  Select categories you care about:  │
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ 🍎  │ │ 🥬  │ │ 🥩  │ │ 🐟  │  │
│  │Fruit│ │Veg  │ │Meat │ │Sea  │  │
│  └──✓──┘ └─────┘ └──✓──┘ └─────┘  │
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ 🥛  │ │ 🍞  │ │ 📦  │ │ 🍿  │  │
│  │Dairy│ │Bread│ │Pantry│ │Snack│  │
│  └──✓──┘ └─────┘ └─────┘ └─────┘  │
│                                     │
│  [Scan Barcode to Add]              │
│  [Continue]                         │
│                                     │
│  Selected: 4 categories             │
└─────────────────────────────────────┘
```

**Barcode Scan Flow:**
1. DAC taps "Scan Barcode"
2. Camera opens
3. Scans product barcode
4. Backend maps to category
5. Category auto-added to DACFI-List if not present

**Validation:**
- Category must be in VALID_CATEGORIES (20 only)
- No duplicates allowed
- At least 1 category recommended

### 3. DACDRLP-List Management

**Map View:**
```
┌─────────────────────────────────────┐
│  Your Local Retailers               │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │    [Interactive Map]        │   │
│  │  🏠 Your Location           │   │
│  │  ○  5 mile radius           │   │
│  │  📍 Store A (1.2 mi)        │   │
│  │  📍 Store B (3.4 mi)        │   │
│  │  📍 Store C (4.8 mi)        │   │
│  │  ⭐ Store D (6.2 mi) [Added]│   │
│  └─────────────────────────────┘   │
│                                     │
│  [Add Retailer] [View Radar]       │
└─────────────────────────────────────┘
```

**List View:**
```
┌─────────────────────────────────────┐
│  Retailer Name      | Distance      │
├─────────────────────────────────────┤
│  📍 Store A         | 1.2 mi  [❌]  │
│  📍 Store B         | 3.4 mi  [❌]  │
│  ⭐ Store D (Added) | 6.2 mi  [❌]  │
└─────────────────────────────────────┘
```

**Add/Remove Logic:**
- **Add**: Search nearby stores, manually add to list
- **Remove**: Click [❌], store removed from DACDRLP-List
- **Backend Tracking**:
  - `auto_added: true` - From DACSAI
  - `manually_added: true` - User added outside DACSAI
  - `manually_removed: true` - User removed (never re-add)

**Backend Storage:**
```json
{
  "dac_id": "uuid",
  "retailers": [
    {
      "drlp_id": "uuid1",
      "drlp_name": "Store A",
      "distance": 1.2,
      "auto_added": true,
      "manually_removed": false
    },
    {
      "drlp_id": "uuid2",
      "drlp_name": "Store D",
      "distance": 6.2,
      "manually_added": true,
      "auto_added": false
    }
  ],
  "dacsai_radius": 5.0,
  "dacsai_center": {"lat": 40.7128, "lng": -74.0060}
}
```

### 4. Radar View (Live RSHD Feed)

**UI Component:**
```
┌─────────────────────────────────────┐
│  Deal Radar - Live Feed             │
├─────────────────────────────────────┤
│  🔴 Store A (1.2 mi) - 3 new deals  │
│  ┌─────────────────────────────┐   │
│  │ 🍎 Organic Apples - 50% OFF │   │
│  │ 🥛 Greek Yogurt - 60% OFF   │   │
│  │ 🥩 Ground Beef - 75% OFF    │   │
│  └─────────────────────────────┘   │
│                                     │
│  🟢 Store B (3.4 mi) - 1 new deal   │
│  ┌─────────────────────────────┐   │
│  │ 🍞 Sourdough Bread - 50% OFF│   │
│  └─────────────────────────────┘   │
│                                     │
│  ⚪ Store C (4.8 mi) - No deals     │
└─────────────────────────────────────┘
```

**Real-time Updates:**
- WebSocket connection to backend
- New RSHDs appear instantly
- Only shows RSHDs from DRLPs in DACDRLP-List
- Highlights RSHDs matching DACFI-List

## Notification Flow

### Backend Matching Logic

**When DRLP posts RSHD:**
```python
async def dispatch_notifications(rshd, drlp_id):
    # Step 1: Get DRLPDAC-List directly (pre-computed, bidirectionally synced)
    # This list contains all DACs who have this DRLP in their DACDRLP-List
    drlpdac_list_doc = await db.drlpdac_list.find_one({"drlp_id": drlp_id})
    
    if not drlpdac_list_doc:
        return  # No DACs interested in this DRLP
    
    dac_ids = drlpdac_list_doc.get("dac_ids", [])
    
    # Step 2: Generate DRLPDAC-SNL (Subset Notification List)
    # Filter to DACs whose DACFI-List (favorite_items) matches the RSHD
    drlpdac_snl = []
    
    for dac_id in dac_ids:
        user = await db.users.find_one({"id": dac_id}, {"favorite_items": 1})
        if not user:
            continue
        
        # Check if any favorite item matches this RSHD
        # (using item-level matching with brand/generic logic)
        for fav_item in user.get("favorite_items", []):
            if matches_rshd(fav_item, rshd):  # Category + keywords + attributes
                drlpdac_snl.append(dac_id)
                break  # Stop after first match (stop-after-first-hit)
    
    # Step 3: Send notifications to DACs in SNL
    for dac_id in drlpdac_snl:
        await create_notification(dac_id, rshd)
```

**Key Points:**
1. DRLPDAC-List is queried directly - no need to scan all DACDRLP-Lists
2. Bidirectional sync ensures DRLPDAC-List is always up-to-date
3. Only DACs in the DRLPDAC-List are considered (geographic filter already applied)
4. DACFI-List (favorite_items) provides the preference filter

### Notification Delivery

**In-App (v1.0):**
- Red badge on bell icon
- Notification list in app
- Click to view RSHD details

**Push Notification (v2.0):**
- iOS/Android push
- "New deal: Organic Apples 50% OFF at Store A"

**Email/SMS (v2.0):**
- Digest: Daily or weekly summary
- Instant: For high-priority deals

## Data Models

### User (DAC)
```json
{
  "id": "uuid",
  "email": "dac@example.com",
  "name": "John Doe",
  "role": "DAC",
  "delivery_location": {
    "address": "123 Main St, City, State 12345",
    "coordinates": {"lat": 40.7128, "lng": -74.0060}
  },
  "charity_id": "uuid",
  "notification_prefs": {
    "push": true,
    "email": true,
    "sms": false
  },
  "created_at": "2025-01-01T00:00:00Z"
}
```

### DACSAI (Embedded in User Document)
```json
{
  "dacsai_rad": 5.0,  // DACSAI-Rad: radius in miles (0.1 - 9.9)
  "delivery_location": {
    "address": "123 Main St, City, State 12345",
    "coordinates": {"lat": 40.7128, "lng": -74.0060}  // DACSAI center
  }
}
```
Note: DACSAI is the circular area defined by delivery_location (center) + dacsai_rad (radius)

### DACFI-List (Embedded in User Document as favorite_items)
```json
{
  "favorite_items": [
    {
      "item_name": "Quaker, Granola",
      "brand": "Quaker",
      "generic": "Granola",
      "has_brand": true,
      "category": "Breakfast & Cereal",
      "keywords": ["quaker", "granola"],
      "attributes": {"organic": false},
      "auto_added_date": null  // null = explicit, date = implicit
    }
  ]
}
```

### DACDRLP-List (Separate Collection)
```json
{
  "id": "uuid",
  "dac_id": "uuid",
  "retailers": [
    {
      "drlp_id": "uuid",
      "drlp_name": "Store A",
      "drlp_location": {"lat": 40.7200, "lng": -74.0100},
      "distance": 1.2,
      "inside_dacsai": true,      // Domiciled inside DACSAI
      "manually_added": false,    // User added from outside DACSAI
      "manually_removed": false,  // User removed despite inside DACSAI
      "added_at": "2025-01-01T00:00:00Z"
    }
  ],
  "dacsai_rad": 5.0,
  "dacsai_center": {"lat": 40.7128, "lng": -74.0060},
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### DRLPDAC-List (Separate Collection - NEW)
```json
{
  "id": "uuid",
  "drlp_id": "uuid",
  "dac_ids": ["dac_uuid_1", "dac_uuid_2", "dac_uuid_3"],
  "updated_at": "2025-01-01T00:00:00Z"
}
```
Note: This list is the inverse of DACDRLP-List. Contains all DACs who have this DRLP in their DACDRLP-List. Must be kept in **bidirectional sync** with DACDRLP-Lists.

## Validation Rules

### DACSAI-Rad
- ✅ Radius: 0.1 ≤ dacsai_rad ≤ 9.9 miles
- ✅ Default: 5.0 miles

### Delivery Location (DACSAI Center)
- ✅ Address: Must be valid and geocodable
- ✅ Coordinates: Required (lat, lng)

### DACFI-List (favorite_items)
- ✅ Item name: Required, non-empty
- ✅ Category: Must be in VALID_CATEGORIES (20 only)
- ✅ No duplicates: Each item_name once only
- ✅ Brand parsing: Comma delimiter for brand-specific ("Brand, Item")

### DACDRLP-List
- ✅ Manual overrides respected (never auto-revert)
- ✅ Removed DRLPs (manually_removed=true) never re-added automatically
- ✅ Manually added DRLPs always preserved
- ✅ **Bidirectional sync**: Changes must update corresponding DRLPDAC-List

### DRLPDAC-List
- ✅ Must mirror DACDRLP-List entries
- ✅ Add DAC when DAC adds this DRLP to their DACDRLP-List
- ✅ Remove DAC when DAC removes this DRLP from their DACDRLP-List

## API Endpoints

### Onboarding
```
POST /api/auth/register
    - Input: User details, delivery location, dacsai_rad
    - Output: User created
    - Side effects: 
      - DACDRLP-List initialized with DRLPs inside DACSAI
      - Each DRLP's DRLPDAC-List updated to include this DAC

PUT /api/users/dacsai
    - Input: New dacsai_rad and/or delivery_location
    - Output: Updated DACSAI settings
    - Side effects:
      - Recalculate which DRLPs are inside DACSAI
      - Update DACDRLP-List (respecting manual overrides)
      - Update affected DRLPDAC-Lists (bidirectional sync)
```

### DACFI-List (Item-Level Favorites)
```
POST /api/favorites/items
    - Input: item_name (e.g., "Organic 2% Milk" or "Quaker, Granola")
    - Output: Item added with auto-categorization
    - Validation: No duplicates, valid category assignment

GET /api/favorites/items
    - Output: DAC's favorite_items organized by category

POST /api/favorites/items/delete
    - Input: item_name
    - Output: Item removed from favorite_items

POST /api/favorites/scan-barcode
    - Input: Barcode image or string
    - Output: Item name extracted, categorized, added to favorite_items
```

### DACDRLP-List
```
GET /api/dac/retailers
    - Output: DACDRLP-List for current DAC (all retailers they receive notifications from)

POST /api/dac/retailers/add
    - Input: DRLP ID (for a DRLP outside DACSAI)
    - Output: DRLP added to DACDRLP-List (manually_added: true)
    - Side effect: Add DAC to that DRLP's DRLPDAC-List (bidirectional sync)

DELETE /api/dac/retailers/{drlp_id}
    - Input: DRLP ID (for a DRLP inside DACSAI that DAC wants to stop receiving notifications from)
    - Output: DRLP marked as manually_removed in DACDRLP-List
    - Side effect: Remove DAC from that DRLP's DRLPDAC-List (bidirectional sync)
```

### Notifications
```
GET /api/notifications
    - Output: Notifications for current DAC
    - Note: Notifications only generated for DACs in DRLPDAC-SNL (geographic + preference match)

GET /api/radar
    - Output: Live feed of all RSHDs from DRLPs in DAC's DACDRLP-List
    - Note: Shows all deals from chosen retailers, not just matching favorites
```

## UI/UX Best Practices

### Onboarding
- **Progressive**: One step at a time
- **Visual**: Maps and icons
- **Helpful**: Tooltips and examples
- **Skippable**: Can complete later

### DACFI-List
- **Simple**: 20 categories, no subcategories
- **Visual**: Category icons/images
- **Fast**: Tap to add, tap to remove
- **Scannable**: Barcode option for convenience

### DACDRLP-List
- **Map-first**: Geographic visualization
- **Clear indicators**: Auto vs. manual, removed vs. active
- **Control**: Easy add/remove
- **Informative**: Distance, RSHD count per retailer

### Notifications
- **Relevant**: Only matching categories
- **Local**: Only from DACDRLP-List retailers
- **Actionable**: Tap to view deal details
- **Manageable**: Mark read, delete

## Performance Optimization

### Caching
- Cache DACDRLP-List in memory (update on change)
- Cache DACFI-List for fast matching
- Cache geocoding results (address → coordinates)

### Database Indexes
- `dacdrlp_list.dac_id` for fast lookup
- `favorites.dac_id` for matching
- `favorites.category` for existence checks

### Matching Optimization
- Pre-filter by DRLPDAC-List (geographic)
- Then filter by DACFI-List (preference)
- Batch notification creation

## Testing Scenarios

### Happy Path Onboarding (< 5 minutes)
1. Register account: 1 min
2. Set delivery location: 30s
3. Define DACSAI (5 mi): 30s
4. Select 5 categories: 2 min
5. Review DACDRLP-List: 1 min
**Total: ~5 minutes**

### DACFI-List Management
1. Add category: < 5s
2. Scan barcode: < 10s
3. Remove category: < 3s

### DACDRLP-List Management
1. View map: < 3s
2. Add retailer: < 10s
3. Remove retailer: < 5s
4. Update DACSAI: < 15s

## Success Metrics

### Onboarding
- **Target**: 90% completion rate
- **Time**: < 5 minutes average
- **Drop-off**: < 10% at any step

### DACFI-List
- **Target**: Average 5-8 categories per DAC
- **Adoption**: 95% of DACs create DACFI-List
- **Maintenance**: 80% update monthly

### DACDRLP-List
- **Target**: Average 8-12 retailers per DAC
- **Customization**: 40% make manual changes
- **Engagement**: 60% use radar view weekly

### Notifications
- **Relevance**: > 80% match DAC interests
- **Action**: > 30% click-through rate
- **Conversion**: > 10% purchase from notification

## Future Enhancements (v2.0+)

### Advanced Preferences
- Attribute filters (organic, gluten-free)
- Price thresholds per category
- Time-of-day preferences

### Smart Features
- ML-based category recommendations
- Predictive RSHD alerts
- Personalized radar sorting

### Integration
- Calendar sync for pickup scheduling
- Shopping list import (map to categories)
- Recipe-to-DACFI mapping

---

**Version**: 1.0  
**Target Time**: < 5 minutes onboarding  
**Status**: V1.0 uses simplified DACSAI (all DACs see all DRLPs), full DACDRLP-List in v2.0
