# DealShaq Discount Model - Version 1.0

## Overview
DealShaq uses a tiered discount model where retailers (DRLPs) provide discounts to DealShaq, and DealShaq applies mapped consumer-facing discounts.

## Discount Levels

### Level 1: Standard Deal
- **DRLP → DealShaq**: 60% discount
- **Consumer sees**: 50% OFF
- **Example**: $10 item → Consumer pays $5

### Level 2: Hot Deal
- **DRLP → DealShaq**: 75% discount
- **Consumer sees**: 60% OFF
- **Example**: $10 item → Consumer pays $4

### Level 3: Sizzling Hot Deal
- **DRLP → DealShaq**: 90% discount
- **Consumer sees**: 75% OFF
- **Example**: $10 item → Consumer pays $2.50

### Level 0: INACTIVE (Future)
- **DRLP → DealShaq**: 15% discount
- **Consumer sees**: 0% OFF (No visible discount)
- **Status**: Rejected in Version 1.0, reserved for future versions

## Validation Logic

### Backend Enforcement (`/app/backend/server.py`)
- Only accepts discount levels 1, 2, or 3
- Rejects Level 0 with error: "Invalid discount level. Only levels 1, 2, and 3 are supported in Version 1.0. Level 0 is inactive."
- Automatically calculates both DRLP discount % and consumer discount %
- Computes final consumer price based on consumer discount mapping

### Calculation Function
```python
def calculate_discount_mapping(discount_level: int, regular_price: float):
    discount_map = {
        1: (60.0, 50.0),  # (drlp_discount, consumer_discount)
        2: (75.0, 60.0),
        3: (90.0, 75.0),
    }
    
    drlp_discount, consumer_discount = discount_map[discount_level]
    deal_price = regular_price * (1 - consumer_discount / 100)
    
    return {
        "drlp_discount_percent": drlp_discount,
        "consumer_discount_percent": consumer_discount,
        "deal_price": deal_price
    }
```

## Implementation Across Apps

### Consumer App
- **Displays**: Consumer-facing discount percentage (50%, 60%, 75%)
- **Shows**: Final deal price after discount
- **Location**: Browse page, Dashboard, Product cards
- **Field**: `deal.consumer_discount_percent`

### Retailer App
- **Posting Items**: Select discount level from dropdown
  - Level 1: "You: 60% → Consumer: 50%"
  - Level 2: "You: 75% → Consumer: 60%"
  - Level 3: "You: 90% → Consumer: 75%"
- **Preview**: Shows both DRLP discount and consumer-facing discount
- **Inventory**: Displays discount level badge (L1, L2, L3) and both discount percentages
- **Transparency**: Clearly shows retailer's discount to DealShaq vs consumer's view

### Admin Dashboard
- **Discount Model Distribution**: Shows count of items at each level
- **Transparency View**: 
  - Level 1: X items (60% → 50%)
  - Level 2: Y items (75% → 60%)
  - Level 3: Z items (90% → 75%)
- **Note**: Reminds that Level 0 is inactive in Version 1.0

## Database Schema Changes

### RSHD Item Model
```javascript
{
  "id": "uuid",
  "name": "Product Name",
  "regular_price": 10.00,
  "discount_level": 2,  // 1, 2, or 3 only
  "drlp_discount_percent": 75.0,  // Discount DRLP gives to DealShaq
  "consumer_discount_percent": 60.0,  // Discount consumer sees
  "deal_price": 4.00,  // Final price consumer pays
  // ... other fields
}
```

## Business Logic

### Nuances
1. **Two-tier discount**: DRLP discounts to DealShaq, DealShaq applies consumer mapping
2. **DealShaq margin**: Built into the discount mapping (e.g., 60% from DRLP → 50% to consumer = 10% margin for DealShaq)
3. **Transparency**: Admin dashboard shows both discount levels for operational oversight
4. **Future-proofing**: Level 0 reserved for future features (e.g., inventory management without visible discounts)

### Validation Rules
- ✅ Levels 1-3: Accepted and processed
- ❌ Level 0: Rejected with error message
- ⚠️ Other values: Rejected as invalid

## Testing

### Test Scenarios
1. **Retailer posts Level 1 deal**: Regular $10 → Consumer sees 50% OFF → Pays $5
2. **Retailer posts Level 2 deal**: Regular $10 → Consumer sees 60% OFF → Pays $4
3. **Retailer posts Level 3 deal**: Regular $10 → Consumer sees 75% OFF → Pays $2.50
4. **Retailer tries Level 0**: Backend rejects with 400 error
5. **Admin views distribution**: Sees count of items at each active level

### API Endpoints
- `POST /api/rshd/items` - Validates discount_level (1-3 only)
- `GET /api/admin/items` - Returns all items with discount details

## Version History
- **v1.0**: Initial release with Levels 1-3 active, Level 0 inactive

## Future Enhancements
- **v2.0**: May activate Level 0 for special use cases
- Potential for additional discount levels (Level 4, 5, etc.)
- Dynamic discount mapping based on market conditions
