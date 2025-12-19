# DealShaq Glossary

**Last Updated:** December 19, 2025  
**Status:** ✅ All terms verified against V1.0 implementation

## Core Entities

### DAC (DealShaq Adjusted Consumer)
- A consumer user of the DealShaq platform
- Receives targeted notifications for deals matching their preferences and location

### DRLP (DealShaq Retailer Location Partner)
- A retailer location/store on the DealShaq platform
- Posts RSHDs (deals) that get matched to interested local consumers

### RSHD (Retailer Sizzling Hot Deal)
- A grocery item posted by a DRLP that needs to move fast
- Characteristics: steep discount (Level 1/2/3), limited quantity, time-sensitive
- Often: perishable, near-expiration, overstock, seasonal items

---

## Geographic Concepts

### DACSAI (DAC's Shopping Area of Interest)
- **Definition:** The circular geographical AREA around the DAC's delivery location
- **Composed of:** DAC's delivery location (center point) + DACSAI-Rad (radius)
- **Purpose:** Defines the geographic zone for "local" retailers
- All DRLPs domiciled within this area are automatically candidates for the DAC's DACDRLP-List

### DACSAI-Rad (DACSAI Radius)
- **Definition:** The radius value (0.1 to 9.9 miles) that determines the size of the DACSAI
- **Measured from:** DAC's delivery location (center point)
- **Configurable by:** DAC during registration or in settings
- **Purpose:** Allows DAC to control how large their shopping area is

---

## List Structures

### DACFI-List (DAC Favorites Inventory List)
- **Definition:** The list of item-level favorites a DAC wants to be notified about
- **Contains:** Specific items with brand/generic parsing, categories, keywords, and attributes
- **Examples:** "Quaker, Granola" (brand-specific), "Organic 2% Milk" (generic)
- **Purpose:** Preference matching - only notify DAC about items they care about

### DACDRLP-List (DAC's DRLP List)
- **Definition:** The list of DRLPs a DAC wants to receive notifications from
- **Formula:** `DRLPs inside DACSAI` + `Manually added DRLPs outside DACSAI` - `Manually removed DRLPs inside DACSAI`
- **Purpose:** Geographic/retailer preference - DAC controls which stores they hear from
- **Sync Requirement:** Must be kept in bidirectional sync with DRLPDAC-List

### DRLPDAC-List (DRLP's DAC List)
- **Definition:** The list of DACs who should receive notifications from this DRLP
- **Contains:** All DACs who have this DRLP in their DACDRLP-List
- **Purpose:** Efficient lookup when DRLP posts RSHD - find eligible DACs quickly
- **Sync Requirement:** Must be kept in bidirectional sync with DACDRLP-List:
  - When DAC removes DRLP from DACDRLP-List → Remove DAC from DRLP's DRLPDAC-List
  - When DAC adds DRLP to DACDRLP-List → Add DAC to DRLP's DRLPDAC-List

### DRLPDAC-SNL (DRLP's DAC Subset Notification List)
- **Definition:** A temporary list generated when a DRLP posts an RSHD
- **Derived from:** DRLPDAC-List filtered by DACFI-List matching
- **Formula:** DACs in DRLPDAC-List whose DACFI-List matches the posted RSHD
- **Purpose:** Final list of DACs who receive notifications for this specific RSHD

---

## Matching Flow

```
DRLP posts RSHD
    ↓
Query DRLPDAC-List (geographic filter - who considers this DRLP local?)
    ↓
For each DAC in DRLPDAC-List:
    Check if RSHD matches DAC's DACFI-List (preference filter)
    ↓
Generate DRLPDAC-SNL (subset who match both geography AND preference)
    ↓
Send notifications to DACs in DRLPDAC-SNL
```

---

## Discount Levels

| Level | DRLP → DealShaq | Consumer Sees |
|-------|-----------------|---------------|
| 1     | 60% discount    | 50% off       |
| 2     | 75% discount    | 60% off       |
| 3     | 90% discount    | 75% off       |

---

## Key Principles

1. **Surplus-Driven Model:** Retailers initiate sales by posting RSHDs, not consumers searching
2. **Targeted Notifications:** DACs only receive notifications for items they want from stores they choose
3. **Bidirectional Sync:** DACDRLP-List and DRLPDAC-List must always be kept in sync
4. **Geographic Anchoring:** DACSAI ensures local relevance
5. **Preference Matching:** DACFI-List ensures item relevance
