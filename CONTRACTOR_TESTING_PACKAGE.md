# DealShaq Contractor Testing Package

## Overview

This document provides everything a contractor needs to perform extensive user testing on DealShaq, a surplus-driven grocery deal platform connecting retailers (DRLPs) with consumers (DACs).

---

## Quick Start

### Access the Application
**Live URL:** `[To be provided after deployment]`

### Test Credentials

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| Consumer (DAC) | test.consumer@example.com | TestPassword123 | Test consumer flows |
| Retailer (DRLP) | test.retailer@example.com | TestPassword123 | Test retailer flows |
| Admin | admin@dealshaq.com | AdminPassword123 | Test admin flows |

*Note: Create fresh accounts for comprehensive registration testing*

---

## Application Structure

DealShaq has three separate applications:

| App | URL Path | Users |
|-----|----------|-------|
| Consumer App | `/consumer` | DACs (Deal-seeking consumers) |
| Retailer App | `/retailer` | DRLPs (Retailers with surplus inventory) |
| Admin App | `/admin` | Platform administrators |

---

## Key Concepts to Understand

### DACSAI (DAC's Shopping Area of Interest)
- Circular geographic area around consumer's delivery location
- Defined by: Delivery address (center) + DACSAI-Rad (0.1-9.9 mile radius)
- Retailers within this area automatically appear in consumer's list

### DACDRLP-List (Consumer's Retailer List)
- List of retailers a consumer receives notifications from
- Formula: `Retailers inside DACSAI` + `Manually added` - `Manually removed`
- Bidirectionally synced with DRLPDAC-List

### DRLPDAC-List (Retailer's Consumer List)
- List of consumers who receive notifications from a retailer
- Contains all DACs who have this DRLP in their DACDRLP-List

### DACFI-List (Consumer's Favorite Items)
- Item-level favorites with brand/generic parsing
- Example: "Quaker, Granola" (brand-specific) vs "Granola" (any brand OK)

### RSHD (Retailer Sizzling Hot Deal)
- Surplus items posted by retailers
- Discount levels: 50% (L1), 60% (L2), 75% (L3) off for consumers

---

## Test Scenarios by Feature Area

### 1. Consumer Registration Flow
**Priority: HIGH**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| Register with valid data | Fill all fields including delivery address | Account created, redirected to dashboard |
| Delivery address geocoding | Enter address, blur field | "✓ Verified" appears, coordinates captured |
| DACSAI radius selection | Adjust slider (0.1-9.9 mi) | Value updates, shown in registration |
| Missing required fields | Skip delivery address | Error message, cannot submit |
| Duplicate email | Use existing email | Error: "Email already registered" |

### 2. Consumer DACSAI/Location Management
**Priority: HIGH**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| View DACSAI settings | Go to Settings page | See delivery address and radius |
| Update delivery address | Enter new address, save | Address geocoded and saved |
| Update DACSAI radius | Adjust slider, save | Radius updated, retailers recalculated |
| Invalid address | Enter gibberish | Error: "Address not found" |

### 3. Consumer Retailer Management (My Retailers)
**Priority: HIGH**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| View retailer list | Go to "Retailers" tab | See all retailers in DACDRLP-List |
| Add retailer outside DACSAI | Click "Add Retailer", select store | Store added with "Added" badge |
| Remove retailer inside DACSAI | Click X on a retailer | Store removed, won't receive notifications |
| Filter by tab | Click "In DACSAI" / "Manually Added" | List filters correctly |
| Empty state | Remove all retailers | Shows "No retailers found" message |

### 4. Consumer Favorites Management (DACFI-List)
**Priority: HIGH**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| Add generic item | Type "Organic Milk" | Added, any brand matches |
| Add brand-specific item | Type "Quaker, Granola" | Added with brand parsing |
| View favorites by category | Go to "Favorites" tab | Items grouped by 20 categories |
| Delete favorite | Click delete on item | Item removed |
| Auto-add threshold | Set to 3 days in Settings | Setting saved |

### 5. Consumer Deal Radar
**Priority: MEDIUM**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| View radar | Go to "Radar" tab | See deals from DACDRLP-List retailers |
| Filter by category | Select category dropdown | Only that category's deals shown |
| Refresh deals | Click refresh button | List updates |
| Empty state | No deals available | Shows "No Deals Available" message |

### 6. Consumer Password Change
**Priority: MEDIUM**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| Change with correct current password | Enter current, new, confirm | "Password changed successfully" |
| Wrong current password | Enter wrong current | Error: "Current password is incorrect" |
| Password too short | New password < 8 chars | Error: "at least 8 characters" |
| Passwords don't match | Confirm doesn't match new | Error: "Passwords do not match" |
| Same as current | New = current | Error: "must be different" |

### 7. Retailer Registration Flow
**Priority: HIGH**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| Register as DRLP | Fill form, select DRLP role | Account created |
| Create store location | Add name, address, coordinates | Location saved, DRLPDAC-List initialized |
| Location geocoding | Enter address | Coordinates captured |
| Duplicate location | Try to create second location | Error: "Location already exists" |

### 8. Retailer RSHD Posting
**Priority: HIGH**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| Post new RSHD | Fill item details, submit | RSHD created, notifications sent |
| Select discount level | Choose L1/L2/L3 | Correct discount applied |
| Set expiry date | Pick future date | Expiry shown on deal |
| View my RSHDs | Go to inventory/deals page | See posted items |

### 9. Notification Flow (End-to-End)
**Priority: CRITICAL**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| DRLP posts deal matching DAC favorite | DRLP posts "Organic Milk", DAC has it in favorites | DAC receives notification |
| Geographic filter | DRLP outside DAC's DACSAI posts deal | DAC does NOT receive notification |
| Brand matching | DAC has "Quaker, Granola", DRLP posts "Quaker Oats Granola" | DAC receives notification |
| Generic matching | DAC has "Granola" (no brand), DRLP posts "Nature Valley Granola" | DAC receives notification |
| Stop-after-first-hit | DAC has multiple matching favorites | Only ONE notification sent |

### 10. Admin Functions
**Priority: LOW**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| View users | Login as admin, go to users | See all users |
| View charities | Go to charities page | See charity list |
| System stats | View dashboard | See statistics |

---

## Discount Model Reference

| Level | DRLP Sells At | Consumer Pays | DealShaq Margin |
|-------|---------------|---------------|-----------------|
| 1 | 40% of retail | 50% of retail | 10% |
| 2 | 25% of retail | 40% of retail | 15% |
| 3 | 10% of retail | 25% of retail | 15% |

---

## Known Limitations / Mocked Features

| Feature | Status | Notes |
|---------|--------|-------|
| Barcode scanning | Mocked | Returns mock category data |
| OCR text extraction | Mocked | Not real OCR |
| DoorDash integration | Mocked | No real delivery |
| Stripe checkout | Configured | Test mode only |
| Password reset email | Live | Via Resend API |

---

## Bug Reporting Template

When reporting issues, please include:

```
## Bug Report

**Feature Area:** [e.g., Consumer Registration, RSHD Posting]
**Severity:** [Critical / High / Medium / Low]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:**

**Actual Result:**

**Screenshots/Video:** [attach if applicable]

**Browser/Device:** [e.g., Chrome 120, macOS]

**Console Errors:** [if any]
```

---

## Documentation Index

| Document | Description | Location |
|----------|-------------|----------|
| User Testing Guide | Detailed test scenarios | `/app/USER_TESTING_GUIDE.md` |
| Value Proposition | Business model overview | `/app/VALUE_PROPOSITION.md` |
| Consumer Data Entry | DAC workflows | `/app/CONSUMER_DATA_ENTRY.md` |
| Retailer Data Entry | DRLP workflows | `/app/RETAILER_DATA_ENTRY.md` |
| Sequence Diagram | Transaction flows | `/app/SEQUENCE_DIAGRAM.md` |
| Data Flow Diagram | System architecture | `/app/DATA_FLOW_DIAGRAM.md` |
| Taxonomy | 20 product categories | `/app/TAXONOMY.md` |
| Discount Model | Pricing structure | `/app/DISCOUNT_MODEL.md` |
| Audit Reports | System audits | `/app/COMPREHENSIVE_AUDIT_REPORT.md` |
| Glossary | Term definitions | `/app/dealshaq-prompts/glossary/glossary.md` |

---

## API Endpoints Reference

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/password/change` - Change password

### Consumer (DAC)
- `GET /api/dac/retailers` - Get DACDRLP-List
- `POST /api/dac/retailers/add` - Add retailer
- `DELETE /api/dac/retailers/{id}` - Remove retailer
- `PUT /api/dac/dacsai` - Update DACSAI radius
- `PUT /api/dac/location` - Update delivery location

### Favorites (DACFI-List)
- `GET /api/favorites/items` - Get favorites by category
- `POST /api/favorites/items` - Add favorite item
- `POST /api/favorites/items/delete` - Remove favorite

### Retailer (DRLP)
- `POST /api/drlp/locations` - Create store location
- `GET /api/drlp/locations` - List all locations
- `GET /api/drlp/my-location` - Get own location

### RSHD (Deals)
- `POST /api/rshd/items` - Post new deal
- `GET /api/rshd/items` - List deals
- `GET /api/rshd/my-items` - Get own deals

### Notifications
- `GET /api/notifications` - Get notifications

---

## Contact

For questions about this testing package, contact: [Your contact info]

---

*Document Version: 1.0*
*Last Updated: December 19, 2025*
