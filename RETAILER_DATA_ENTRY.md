# DealShaq Retailer Data Entry Workflow

## Goal
Enable DRLP associates to post RSHDs in **under 1 minute** with minimal typing and maximum automation.

## Workflow Overview

### Step 1: Barcode Capture (5-10 seconds)
**Method**: Camera capture or manual entry
- Associate taps "Scan Barcode" button
- Uses smartphone/tablet camera to capture barcode image
- Backend decodes: UPC, PLU, or retailer-specific barcode
- **Auto-populated**:
  - Product name (from GS1 database or retailer catalog)
  - Base category (mapped to 1 of 20 DealShaq categories)
  - Typical weight/unit size
- **Fallback**: Manual barcode entry if camera unavailable

**APIs Used**:
- Barcode decoding: ZXing, ZBar, or Scandit SDK
- Product lookup: GS1 database, UPC Item DB, or retailer API

**V1.0 Implementation**: Mock barcode lookup with manual entry fallback

### Step 2: Price & Expiry Capture (5-10 seconds)
**Method**: Photo OCR or manual entry
- Associate taps "Scan Price Label"
- Takes photo of shelf label/sticker
- OCR extracts:
  - Retail price (regular price)
  - Expiry date (if visible)
- **Quick override**: Manual adjustment if OCR misreads
- App highlights extracted text for verification

**APIs Used**:
- OCR: Google Cloud Vision, AWS Textract, or Tesseract
- Text parsing: Regex patterns for price ($X.XX) and dates

**V1.0 Implementation**: Mock OCR with manual entry

### Step 3: Deal Configuration (10-15 seconds)
**Manual Entry** (required):
- **Discount Level**: Select Level 1, 2, or 3
  - Level 1: 60% to DealShaq → Consumer sees 50% OFF
  - Level 2: 75% to DealShaq → Consumer sees 60% OFF
  - Level 3: 90% to DealShaq → Consumer sees 75% OFF
- **Quantity Available**: Number input
- **Optional Notes**: Free text (e.g., "Damaged packaging", "Near expiry")

**Auto-calculated** (shown in preview):
- Consumer deal price (based on discount level)
- DRLP discount to DealShaq
- Consumer discount percentage

### Step 4: Validation (Instant)
**Backend Checks**:
- ✅ Category: Must be 1 of 20 valid DealShaq categories
- ✅ Discount Level: Must be 1, 2, or 3 (Level 0 rejected)
- ✅ Expiry Date: Must be after current date
- ✅ Quantity: Must be positive integer
- ✅ Price: Must be positive number
- ❌ Reject if any validation fails

**Frontend Feedback**:
- Real-time validation as user types
- Clear error messages if validation fails
- Green checkmarks for valid fields

### Step 5: Backend Matching & Notification (Automatic)
**After RSHD Posted**:

1. **Retrieve DRLPDAC-List**:
   ```
   Get all DACs who have this DRLP in their DACDRLP-List
   (DACs within DACSAI or manually added)
   ```

2. **Generate DRLPDAC-SNL** (Subset Notification List):
   ```
   For each DAC in DRLPDAC-List:
       Check if RSHD.category matches any category in DAC's DACFI-List
       If match: Add to DRLPDAC-SNL
   ```

3. **Dispatch Notifications**:
   ```
   For each DAC in DRLPDAC-SNL:
       Create notification record
       Send in-app notification
       [Future: Send push/email/SMS]
   ```

## Data Flow Diagram

```
DRLP Associate
    ↓
1. Scan Barcode → [Barcode API] → Auto-populate name, category
    ↓
2. Scan Price Label → [OCR API] → Extract price, expiry
    ↓
3. Select Discount Level + Enter Quantity
    ↓
4. Review Preview (deal price, discounts)
    ↓
5. Submit RSHD → [Backend Validation]
    ↓
Backend:
    - Validate category (20 categories)
    - Validate discount level (1-3 only)
    - Validate expiry (future date)
    - Validate quantity (positive)
    ↓
    - Get DRLPDAC-List (all local DACs)
    ↓
    - Generate DRLPDAC-SNL (matched DACs)
      For each DAC:
          Does RSHD.category match DACFI-List?
          Yes → Add to SNL
    ↓
    - Create notifications for DACs in SNL
    ↓
DAC receives notification
```

## UI/UX Design Principles

### Speed-Optimized Layout
- **Large tap targets**: Buttons sized for quick tapping on mobile/tablet
- **Minimal scrolling**: All key fields visible without scrolling
- **Auto-focus**: Next field auto-selected after input
- **Smart defaults**: Common values pre-selected

### Visual Feedback
- **Loading states**: Show "Scanning..." during barcode/OCR processing
- **Success indicators**: Green checkmarks for valid fields
- **Error prevention**: Disable submit until all required fields valid
- **Preview panel**: Real-time price calculations

### Error Handling
- **Clear messages**: "Expiry date must be in the future"
- **Suggested fixes**: "Try Level 2 instead?" if Level 0 attempted
- **Retry options**: "Scan again" if barcode/OCR fails
- **Manual overrides**: Always allow manual entry as fallback

## Technical Implementation

### Frontend (React)
**Component**: `RetailerPostItemFast.js`
- Camera access via Web APIs (getUserMedia)
- Barcode scanning via QuaggaJS or ZXing web library
- OCR via Tesseract.js (client-side) or API call
- Real-time validation with visual feedback
- Mobile-optimized UI with large buttons

**Key Features**:
- Progressive disclosure: Show sections as needed
- Keyboard optimization: Number pad for quantity/price
- Camera preview with overlay guides
- Batch posting: Quick "Post Another" button

### Backend (FastAPI)
**Endpoints**:
```python
POST /api/barcode/scan
    - Input: Image file or barcode string
    - Output: Product name, category, weight
    - Mock in v1.0: Return sample data

POST /api/ocr/parse-label
    - Input: Image file
    - Output: Price, expiry date
    - Mock in v1.0: Return sample data

POST /api/rshd/items (existing)
    - Enhanced validation
    - DRLPDAC-SNL generation
    - Notification dispatch
```

**Validation Service**:
```python
def validate_rshd_posting(item_data):
    # Category validation
    if item_data.category not in VALID_CATEGORIES:
        raise ValidationError("Invalid category")
    
    # Discount level validation
    if item_data.discount_level not in [1, 2, 3]:
        raise ValidationError("Level 0 inactive in v1.0")
    
    # Expiry validation
    if item_data.expiry_date <= datetime.now():
        raise ValidationError("Expiry must be future date")
    
    # Quantity validation
    if item_data.quantity <= 0:
        raise ValidationError("Quantity must be positive")
    
    return True
```

**Matching Service**:
```python
async def generate_drlpdac_snl(rshd, drlp_id):
    """Generate Subset Notification List for RSHD"""
    
    # Step 1: Get all DACs who consider this DRLP local
    # (In v1.0: simplified to all DACs for MVP)
    all_dacs = await db.users.find({"role": "DAC"}).to_list(10000)
    
    # Step 2: Filter to DACs with matching category in DACFI-List
    matching_dacs = []
    for dac in all_dacs:
        has_category = await db.favorites.find_one({
            "dac_id": dac["id"],
            "category": rshd["category"]
        })
        if has_category:
            matching_dacs.append(dac["id"])
    
    # Step 3: Return DRLPDAC-SNL
    return matching_dacs
```

## Performance Optimization

### Caching
- Cache barcode lookups (1 hour TTL)
- Cache category mappings (no expiry)
- Cache DRLPDAC-Lists per location (update on change)

### Batch Processing
- Allow posting multiple RSHDs in sequence
- Keep form state between posts
- Pre-load next barcode scan while submitting

### Network Optimization
- Compress images before upload (max 500KB)
- Use WebP format for photos
- Offline mode: Queue posts, sync when online

## Mobile Considerations

### Camera Access
- Request camera permissions on first use
- Show permission denial instructions
- Fallback to file upload if camera denied

### Orientation
- Support both portrait and landscape
- Lock orientation during barcode scanning
- Adaptive layout based on screen size

### Touch Targets
- Minimum 44x44px for all buttons (iOS guideline)
- Adequate spacing between interactive elements
- Large, easy-to-tap number inputs

## Testing Scenarios

### Happy Path (30-45 seconds)
1. Scan barcode: 5s → Auto-populate name, category
2. Scan price label: 5s → Auto-populate price, expiry
3. Select Level 2: 2s
4. Enter quantity 10: 3s
5. Review preview: 5s
6. Submit: 2s
**Total: ~22 seconds**

### Manual Entry Path (45-60 seconds)
1. Manual barcode entry: 10s
2. Manual price entry: 5s
3. Manual expiry entry: 5s
4. Select Level 2: 2s
5. Enter quantity 10: 3s
6. Review preview: 5s
7. Submit: 2s
**Total: ~32 seconds**

### Error Recovery Path
1. Scan barcode: 5s → Failed
2. Retry scan: 5s → Success
3. Scan price: 5s → Misread ($1.99 vs $19.99)
4. Manual override: 3s
5. Continue normal flow: 15s
**Total: ~33 seconds**

## Training Materials

### Quick Start Guide for Associates
1. **Tap "Post New Deal"**
2. **Scan barcode** (or type it in)
3. **Scan price label** (or type price + expiry)
4. **Choose discount level** (1, 2, or 3)
5. **Enter how many** items available
6. **Review & Submit**

### Common Issues & Solutions
- **Barcode won't scan**: Try better lighting, hold steady
- **Price OCR failed**: Just type it in manually
- **"Invalid category" error**: Contact support for mapping
- **"Level 0 inactive"**: Use Level 1, 2, or 3 instead

## Success Metrics

### Speed
- **Target**: 95% of posts completed in < 60 seconds
- **Measure**: Time from "Post New Deal" to "Submit" click

### Accuracy
- **Target**: < 5% validation errors per post
- **Measure**: Failed submissions / total attempts

### Adoption
- **Target**: 80% of DRLPs post at least 5 RSHDs per week
- **Measure**: Active posting DRLPs / total DRLPs

### Automation
- **Target**: 70% of posts use barcode scan (not manual)
- **Measure**: Barcode scans / total posts

## Future Enhancements (v2.0+)

### Advanced Barcode Features
- Multi-barcode batch scanning
- Variable-weight barcode parsing (extract weight + price)
- QR code support for internal tracking

### Smart Suggestions
- Recommended discount level based on expiry proximity
- Suggested quantity based on historical data
- Auto-categorization using ML

### Voice Input
- Voice-to-text for notes
- Voice commands for navigation
- Hands-free mode for busy associates

### Integration Enhancements
- Real GS1 database integration
- Retailer POS system integration
- Inventory management sync

---

**Version**: 1.0  
**Target Time**: < 60 seconds per RSHD  
**Status**: V1.0 uses mock barcode/OCR with manual entry fallback
