# DealShaq Transaction Sequence Diagram

This document describes the key transaction flows in the DealShaq system.

## 1. DAC Registration Flow

```mermaid
sequenceDiagram
    participant DAC as Consumer (DAC)
    participant FE as Frontend
    participant BE as Backend
    participant GEO as Geocoding API
    participant DB as MongoDB

    DAC->>FE: Fill registration form
    Note over DAC,FE: Name, Email, Password,<br/>Delivery Address, DACSAI-Rad
    
    FE->>GEO: Geocode delivery address
    GEO-->>FE: Return coordinates (lat, lng)
    
    FE->>BE: POST /api/auth/register
    Note over FE,BE: {name, email, password, role: "DAC",<br/>delivery_location: {address, coordinates},<br/>dacsai_rad: 5.0}
    
    BE->>DB: Create user document
    BE->>DB: Query all DRLP locations
    
    loop For each DRLP within DACSAI radius
        BE->>DB: Add DRLP to DACDRLP-List
        BE->>DB: Add DAC to DRLP's DRLPDAC-List
        Note over BE,DB: Bidirectional sync
    end
    
    BE-->>FE: Return JWT token + user data
    FE-->>DAC: Redirect to dashboard
```

## 2. DRLP Posts RSHD (Deal) Flow

```mermaid
sequenceDiagram
    participant DRLP as Retailer (DRLP)
    participant FE as Frontend
    participant BE as Backend
    participant DB as MongoDB
    participant DAC as Consumers (DACs)

    DRLP->>FE: Create new RSHD item
    Note over DRLP,FE: Item name, category, price,<br/>discount level, quantity, expiry
    
    FE->>BE: POST /api/rshd/items
    BE->>DB: Save RSHD item
    
    BE->>BE: create_matching_notifications()
    
    Note over BE: STEP 1: Geographic Filter
    BE->>DB: Query DRLPDAC-List for this DRLP
    DB-->>BE: Return list of DAC IDs
    Note over BE: Only DACs who have this<br/>DRLP in their DACDRLP-List
    
    Note over BE: STEP 2: Preference Filter
    loop For each DAC in DRLPDAC-List
        BE->>DB: Get DAC's favorite_items
        BE->>BE: Match RSHD against DACFI-List
        Note over BE: Category match +<br/>Keyword match +<br/>Brand/Generic logic
        
        alt Match found
            BE->>DB: Create notification
            Note over BE: Stop checking this DAC<br/>(stop-after-first-hit)
        end
    end
    
    BE-->>FE: Return created RSHD
    
    Note over DAC: DACs receive notifications<br/>for matching items from<br/>local retailers
```

## 3. DAC Manages DACDRLP-List Flow

### 3a. Add Retailer (Outside DACSAI)

```mermaid
sequenceDiagram
    participant DAC as Consumer (DAC)
    participant FE as Frontend
    participant BE as Backend
    participant DB as MongoDB

    DAC->>FE: Click "Add Retailer"
    FE->>BE: POST /api/dac/retailers/add?drlp_id=XXX
    
    BE->>DB: Get DRLP location info
    BE->>BE: Calculate distance from DAC
    
    BE->>DB: Add to DACDRLP-List
    Note over BE,DB: manually_added: true
    
    BE->>DB: Add DAC to DRLP's DRLPDAC-List
    Note over BE,DB: Bidirectional sync
    
    BE-->>FE: Return success
    FE-->>DAC: "Retailer added to your list"
```

### 3b. Remove Retailer (Inside DACSAI)

```mermaid
sequenceDiagram
    participant DAC as Consumer (DAC)
    participant FE as Frontend
    participant BE as Backend
    participant DB as MongoDB

    DAC->>FE: Click "Remove" on retailer
    FE->>BE: DELETE /api/dac/retailers/{drlp_id}
    
    BE->>DB: Mark as manually_removed in DACDRLP-List
    Note over BE,DB: Prevents auto-re-add<br/>even if inside DACSAI
    
    BE->>DB: Remove DAC from DRLP's DRLPDAC-List
    Note over BE,DB: Bidirectional sync
    
    BE-->>FE: Return success
    FE-->>DAC: "You will no longer receive<br/>notifications from this store"
```

## 4. DAC Updates DACSAI-Rad Flow

```mermaid
sequenceDiagram
    participant DAC as Consumer (DAC)
    participant FE as Frontend
    participant BE as Backend
    participant DB as MongoDB

    DAC->>FE: Adjust DACSAI-Rad slider
    DAC->>FE: Click "Save"
    FE->>BE: PUT /api/dac/dacsai?dacsai_rad=7.5
    
    BE->>DB: Update user's dacsai_rad
    BE->>DB: Get current DACDRLP-List
    BE->>BE: Note manual overrides
    Note over BE: manually_added: keep<br/>manually_removed: keep out
    
    BE->>DB: Query all DRLP locations
    
    loop For each DRLP
        BE->>BE: Calculate distance
        alt Inside new DACSAI AND not manually_removed
            BE->>DB: Add to DACDRLP-List
        else Outside new DACSAI AND not manually_added
            BE->>DB: Remove from DACDRLP-List
        end
    end
    
    BE->>DB: Update all affected DRLPDAC-Lists
    Note over BE,DB: Bidirectional sync
    
    BE-->>FE: Return {retailers_count: N}
    FE-->>DAC: "DACSAI updated! N retailers in your area"
```

## 5. Purchase and Auto-Add Favorites Flow

```mermaid
sequenceDiagram
    participant DAC as Consumer (DAC)
    participant FE as Frontend
    participant BE as Backend
    participant DB as MongoDB
    participant SCHED as Scheduler

    DAC->>FE: Complete purchase
    FE->>BE: POST /api/orders
    BE->>DB: Save order with items
    Note over BE,DB: Each item includes:<br/>name, category, purchase date
    
    Note over SCHED: Daily at 11 PM
    SCHED->>BE: Run auto-add job
    
    BE->>DB: Get all DACs with auto_threshold > 0
    
    loop For each DAC
        BE->>DB: Get purchase history (21 days)
        BE->>DB: Get current favorite_items
        
        loop For each non-favorite item
            BE->>BE: Count purchase days
            alt Days >= threshold (3 or 6)
                BE->>DB: Add to favorite_items
                Note over BE,DB: auto_added_date: today
            end
        end
    end
```

## Key Concepts

### DACSAI (DAC's Shopping Area of Interest)
- Circular geographic area defined by:
  - **Center**: DAC's delivery location (coordinates)
  - **Radius**: DACSAI-Rad (0.1 to 9.9 miles)

### Bidirectional Sync
- **DACDRLP-List**: Which retailers a DAC wants notifications from
- **DRLPDAC-List**: Which DACs want notifications from a retailer
- These lists MUST be kept in sync:
  - Add to one → Add to the other
  - Remove from one → Remove from the other

### Matching Logic
1. **Geographic Filter**: Only DACs in DRLPDAC-List are considered
2. **Preference Filter**: RSHD must match DAC's DACFI-List
3. **Brand Logic**:
   - Brand-specific favorite → Must match brand AND generic
   - Generic favorite → Any brand is OK
4. **Stop-after-first-hit**: One notification per DAC per RSHD batch
