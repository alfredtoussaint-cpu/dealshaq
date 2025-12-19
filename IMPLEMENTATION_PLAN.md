# DealShaq Implementation Plan

This document outlines the implementation roadmap for building out the complete DealShaq system based on the seed summary. The system consists of five major modules working together to create a comprehensive grocery discount marketplace.

---

## System Overview

DealShaq is a surplus-driven grocery discount marketplace with:
- **Retailer App (DRLP)**: Where retailers post time-sensitive deals
- **Consumer App (DAC)**: Where consumers discover and purchase discounted items
- **Admin Dashboard**: Central management and oversight platform
- **Backend Services**: API and business logic layer
- **Frontend Shared Components**: Common UI elements and utilities

---

## Current State vs. Target State

### ✅ Currently Implemented (Updated December 2025)
- Basic authentication (JWT-based, multi-role support)
- Consumer App with registration and login
- Retailer App with registration and login
- Admin Dashboard with secure admin creation
- Password show/hide toggles on all auth forms
- Forgot password modals on all auth forms
- MongoDB integration for users, charities, items
- 20-category taxonomy for groceries
- 3-level discount model (DRLP: 60/75/90% → Consumer: 50/60/75%)
- Basic API structure with FastAPI
- **DACSAI Geographic Filtering System** ✅ NEW
  - Delivery location required at registration
  - DACSAI-Rad (0.1-9.9 miles) configuration
  - Automatic DACDRLP-List generation
  - Bidirectional sync with DRLPDAC-List
- **"My Retailers" Page** ✅ NEW - DACs can manage their DACDRLP-List
- **"Radar View" Page** ✅ NEW - Real-time local RSHD feed
- **Enhanced Favorites** ✅ - Item-level favorites with brand/generic distinction
- **Smart Favorites (Auto-Add)** ✅ - Implicit favorites based on purchase history
- **Password Change** ✅ - From Settings page
- **DRLP Location Management** ✅ - Retailers can set their store location

### 🔨 To Be Implemented
Based on the seed summary, the following features still need to be built:

---

## Phase 1: Retailer App Enhancement (DRLP)

### 1.1 RSHD Posting & Management
**Priority**: High  
**Estimated Effort**: Large

**Features**:
- Complete RSHD item creation form with all fields
- Barcode scanning integration (currently mocked - needs real API)
- OCR for expiry date reading (currently mocked - needs real API)
- Quantity validation and tracking
- Discount level enforcement (33%, 66%, 99%)
- Contribution calculation (percentage of savings donated to charity)
- RSHD listing and management dashboard
- Edit and delete RSHD items
- Bulk upload capability

**Technical Requirements**:
- Database schema for RSHDs with all required fields
- File upload for product images
- Third-party barcode scanning API integration
- Third-party OCR API integration
- Real-time inventory tracking

**API Endpoints Needed**:
```
POST   /api/rshd/items          - Create new RSHD
PUT    /api/rshd/items/{id}     - Update RSHD
DELETE /api/rshd/items/{id}     - Delete RSHD
GET    /api/rshd/items          - List retailer's RSHDs
POST   /api/rshd/bulk-upload    - Bulk upload RSHDs
POST   /api/rshd/scan-barcode   - Scan product barcode
POST   /api/rshd/scan-expiry    - OCR expiry date
```

### 1.2 Retailer Approval Workflow
**Priority**: High  
**Estimated Effort**: Medium

**Features**:
- Retailer registration status tracking (pending, approved, rejected, suspended)
- Admin notification when new retailer registers
- Retailer dashboard showing approval status
- Email notifications for status changes

**Technical Requirements**:
- Add `approval_status` field to users collection
- Admin approval API endpoints
- Email notification system integration

**Database Schema Updates**:
```javascript
users: {
  approval_status: "pending" | "approved" | "rejected" | "suspended",
  approval_date: Date,
  approved_by: String, // admin_id
  rejection_reason: String
}
```

---

## Phase 2: Consumer App Enhancement (DAC)

### 2.1 Consumer Onboarding & Validation ✅ COMPLETED
**Priority**: High  
**Estimated Effort**: Medium
**Status**: ✅ IMPLEMENTED (December 2025)

**Features Implemented**:
- ✅ DACSAI (Shopping Area of Interest) setup - delivery location + radius
- ✅ Radius selection (0.1 - 9.9 miles, required at registration)
- ✅ Delivery location required at registration
- ✅ Favorite items selection (DACFI-List with brand/generic support)
- ✅ Charity selection for donation contributions
- ✅ Settings page for updating DACSAI configuration

**API Endpoints Implemented**:
```
PUT    /api/dac/dacsai              - Update DACSAI-Rad and delivery location
GET    /api/dac/retailers           - Get DACDRLP-List
POST   /api/dac/retailers/add       - Add retailer to DACDRLP-List
DELETE /api/dac/retailers/{drlp_id} - Remove retailer from DACDRLP-List
```

### 2.2 Radar View - Local RSHD Discovery ✅ COMPLETED
**Priority**: High  
**Estimated Effort**: Large
**Status**: ✅ IMPLEMENTED (December 2025)

**Features Implemented**:
- ✅ Real-time display of all RSHDs from retailers in DACDRLP-List
- ✅ List view with RSHD cards showing deal details
- ✅ Distance calculation from consumer location (Haversine formula)
- ✅ Geographic filtering based on DACSAI

**API Endpoints Implemented**:
```
GET    /api/radar                   - Get RSHDs from DACDRLP-List retailers
```

**Future Enhancements (v2.0)**:
- Filter by favorite categories
- Filter by discount level
- Sort by distance, discount, expiry date
- Map view showing retailer locations

### 2.3 Notifications System
**Priority**: High  
**Estimated Effort**: Medium

**Features**:
- Real-time notifications when new RSHDs match consumer preferences
- Push notifications (web push or mobile)
- Email notifications (optional setting)
- Notification preferences management
- Notification history

**Technical Requirements**:
- Web Push API integration or Firebase Cloud Messaging
- Email service integration (SendGrid, AWS SES)
- Background job for matching RSHDs to consumer preferences

**API Endpoints Needed**:
```
GET    /api/notifications          - Get user notifications
PUT    /api/notifications/read     - Mark notifications as read
POST   /api/notifications/settings - Update notification preferences
```

### 2.4 DACDRLP-List Management ✅ COMPLETED
**Priority**: Medium  
**Estimated Effort**: Small
**Status**: ✅ IMPLEMENTED (December 2025)

**Features Implemented**:
- ✅ "My Retailers" page for managing DACDRLP-List
- ✅ View list of retailers in DACSAI (auto-populated)
- ✅ Manual add retailers outside DACSAI
- ✅ Manual remove retailers inside DACSAI
- ✅ Bidirectional sync with DRLPDAC-List
- ✅ Manual overrides preserved during DACSAI updates

**Database Schema Implemented**:
```javascript
// dacdrlp_list collection
{
  id: String,
  dac_id: String,
  retailers: [{
    drlp_id: String,
    drlp_name: String,
    drlp_location: {lat, lng},
    distance: Number,
    inside_dacsai: Boolean,
    manually_added: Boolean,
    manually_removed: Boolean
  }],
  dacsai_rad: Number,
  dacsai_center: {lat, lng}
}

// drlp_locations collection (DRLPDAC-List stored here)
{
  drlp_id: String,
  drlpdac_list: [dac_id]  // DACs who have this DRLP in their DACDRLP-List
}
```

**API Endpoints Implemented**:
```
GET    /api/dac/retailers           - Get DAC's DACDRLP-List
POST   /api/dac/retailers/add       - Add retailer (bidirectional sync)
DELETE /api/dac/retailers/{drlp_id} - Remove retailer (bidirectional sync)
```

### 2.5 Enhanced Checkout & Net Proceed
**Priority**: High  
**Estimated Effort**: Large

**Features**:
- Shopping cart with RSHD items
- Delivery option (DoorDash integration - currently mocked)
- Pickup option with time slot selection
- Net Proceed calculation display
- Charity contribution amount shown
- Round-up option at checkout
- Payment processing (Stripe integration)
- Order confirmation and receipt

**Technical Requirements**:
- DoorDash API integration (replace mock)
- Stripe payment processing
- Net Proceed calculation formula
- PDF receipt generation

**Net Proceed Calculation**:
```
Original Price - Discounted Price = Savings
Contribution = Savings × Retailer's Contribution %
Net Proceed = Discounted Price + Contribution + Round-up
```

**API Endpoints Needed**:
```
POST   /api/cart/add               - Add item to cart
DELETE /api/cart/remove/{id}       - Remove from cart
GET    /api/cart                   - Get cart items
POST   /api/checkout               - Process checkout
POST   /api/checkout/delivery      - Arrange DoorDash delivery
GET    /api/checkout/pickup-times  - Get available pickup times
```

---

## Phase 3: Admin Dashboard Enhancement

### 3.1 DRLP Approval System
**Priority**: High  
**Estimated Effort**: Medium

**Features**:
- View pending retailer registrations
- Review retailer details and credentials
- Approve/reject with reason
- Suspend/remove existing retailers
- Bulk approval actions
- Approval history log

**API Endpoints Needed**:
```
GET    /api/admin/retailers/pending    - Get pending retailers
POST   /api/admin/retailers/approve    - Approve retailer
POST   /api/admin/retailers/reject     - Reject retailer
POST   /api/admin/retailers/suspend    - Suspend retailer
GET    /api/admin/retailers/history    - Get approval history
```

### 3.2 Charity Management
**Priority**: Medium  
**Estimated Effort**: Small

**Features**:
- Add/edit/remove charities
- Validate charity credentials
- View charity selection statistics
- Deactivate/reactivate charities

**API Endpoints Needed**:
```
POST   /api/admin/charities        - Create charity
PUT    /api/admin/charities/{id}   - Update charity
DELETE /api/admin/charities/{id}   - Delete charity
GET    /api/admin/charities/stats  - Get charity statistics
```

### 3.3 Contribution Aggregation & Disbursement
**Priority**: High  
**Estimated Effort**: Large

**Features**:
- Real-time contribution tracking by charity
- Aggregation dashboard with charts
- Disbursement schedule management
- Generate disbursement files (CSV, PDF)
- Execute disbursements (manual or automated)
- Issue donation receipts to consumers
- Audit trail for all disbursements

**Technical Requirements**:
- Transaction aggregation background jobs
- Report generation (charts, PDFs)
- Payment processing for disbursements
- Email system for receipts

**Database Schema**:
```javascript
disbursements: {
  id: String,
  charity_id: String,
  amount: Number,
  period_start: Date,
  period_end: Date,
  transaction_count: Number,
  status: "pending" | "processed" | "completed",
  processed_date: Date,
  processed_by: String, // admin_id
  receipt_url: String
}
```

**API Endpoints Needed**:
```
GET    /api/admin/contributions        - Get contribution summary
POST   /api/admin/disbursement/create  - Create disbursement
POST   /api/admin/disbursement/execute - Execute disbursement
GET    /api/admin/disbursement/history - Get disbursement history
POST   /api/admin/disbursement/receipt - Generate receipt
```

### 3.4 Compliance & Reporting
**Priority**: Medium  
**Estimated Effort**: Large

**Features**:
- Compliance rules engine
- Monitor for rule violations
- Generate compliance reports
- Transaction audit logs
- User activity logs
- System health monitoring
- Data export capabilities

**Technical Requirements**:
- Comprehensive logging system
- Report generation engine
- Data visualization (charts, graphs)

**API Endpoints Needed**:
```
GET    /api/admin/compliance/rules     - Get compliance rules
POST   /api/admin/compliance/check     - Run compliance check
GET    /api/admin/reports/transactions - Transaction reports
GET    /api/admin/reports/activity     - User activity reports
GET    /api/admin/audit-logs           - Get audit logs
POST   /api/admin/export               - Export data
```

### 3.5 System Configuration
**Priority**: Medium  
**Estimated Effort**: Medium

**Features**:
- Manage 20-category taxonomy (add/edit/remove categories)
- Configure discount thresholds (currently fixed at 33%, 66%, 99%)
- DACSAI radius rules and limits
- System-wide settings
- Feature flags for rollout control

**API Endpoints Needed**:
```
GET    /api/admin/config/categories    - Get categories
POST   /api/admin/config/categories    - Update categories
GET    /api/admin/config/discounts     - Get discount levels
POST   /api/admin/config/discounts     - Update discount levels
GET    /api/admin/config/system        - Get system settings
POST   /api/admin/config/system        - Update system settings
```

### 3.6 Dashboards & Analytics
**Priority**: Medium  
**Estimated Effort**: Large

**Features**:
- Executive dashboard with key metrics
- Transaction volume charts
- User growth metrics
- Revenue analytics
- Charity contribution totals
- Retailer performance metrics
- Consumer engagement metrics
- Real-time activity feed

**Technical Requirements**:
- Data aggregation pipelines
- Chart library integration (Chart.js, Recharts)
- Real-time data updates

---

## Phase 4: Backend Services Enhancement

### 4.1 DRLPDAC-SNL Generation ✅ COMPLETED
**Priority**: High  
**Estimated Effort**: Medium
**Status**: ✅ IMPLEMENTED (December 2025)

**Features Implemented**:
- ✅ Geographic filtering via DRLPDAC-List (first filter)
- ✅ Preference matching via DACFI-List (second filter)
- ✅ Stop-after-first-hit optimization
- ✅ Brand/generic matching logic
- ✅ Notification creation for matched DACs

**Implementation Details**:
- When RSHD is posted, system retrieves DRLP's DRLPDAC-List
- For each DAC in list, checks DACFI-List for preference match
- Creates notification only for geographic + preference matches
- Uses Haversine formula (geohash-utils) for distance calculations

### 4.2 Transaction Management
**Priority**: High  
**Estimated Effort**: Medium

**Database Schema**:
```javascript
transactions: {
  id: String,
  consumer_id: String,
  retailer_id: String,
  items: [
    {
      rshd_id: String,
      quantity: Number,
      original_price: Number,
      discounted_price: Number,
      discount_level: Number
    }
  ],
  subtotal: Number,
  savings: Number,
  contribution: Number,
  round_up: Number,
  net_proceed: Number,
  charity_id: String,
  payment_method: String,
  payment_id: String,
  status: "pending" | "completed" | "cancelled" | "refunded",
  fulfillment_type: "delivery" | "pickup",
  delivery_details: Object,
  pickup_details: Object,
  created_at: Date,
  completed_at: Date
}
```

### 4.3 Validation Engine
**Priority**: High  
**Estimated Effort**: Medium

**Features**:
- RSHD validation (price, discount, quantity, expiry)
- Consumer onboarding validation
- Charity selection validation
- Transaction validation
- Business rule enforcement

### 4.4 Audit Logging
**Priority**: Medium  
**Estimated Effort**: Small

**Features**:
- Log all user actions
- Log all admin actions
- Log all system events
- Searchable log interface
- Log retention policy

**Database Schema**:
```javascript
audit_logs: {
  id: String,
  timestamp: Date,
  user_id: String,
  user_role: String,
  action: String,
  entity_type: String,
  entity_id: String,
  changes: Object,
  ip_address: String,
  user_agent: String
}
```

---

## Phase 5: Frontend Shared Components

### 5.1 Cross-App Navigation
**Priority**: Medium  
**Estimated Effort**: Small

**Features**:
- Global navigation component
- Role-based menu items
- Quick app switcher (for users with multiple roles)

### 5.2 Notification UI
**Priority**: High  
**Estimated Effort**: Medium

**Features**:
- Notification bell icon with badge
- Notification dropdown
- Toast notifications for real-time events
- Notification preferences panel

### 5.3 Accessibility
**Priority**: Medium  
**Estimated Effort**: Medium

**Features**:
- ARIA labels throughout
- Keyboard navigation support
- Screen reader optimization
- Color contrast compliance (WCAG AA)
- Focus management

### 5.4 Error Handling
**Priority**: Medium  
**Estimated Effort**: Small

**Features**:
- Global error boundary
- User-friendly error messages
- Retry mechanisms for failed requests
- Offline mode detection
- Loading states and skeletons

---

## Technical Dependencies & Integrations

### Third-Party Services to Integrate

1. **Barcode Scanning API**
   - Options: Scandit, Cognex, Google Cloud Vision API
   - Purpose: Product identification for RSHD posting

2. **OCR Service**
   - Options: Tesseract, Google Cloud Vision, AWS Textract
   - Purpose: Expiry date reading from product images

3. **Delivery Service (DoorDash)**
   - Currently: Mocked
   - Purpose: Delivery fulfillment for consumer orders

4. **Payment Processing (Stripe)**
   - Status: Needs implementation
   - Purpose: Consumer payments and charity disbursements

5. **Email Service**
   - Options: SendGrid, AWS SES, Mailgun
   - Purpose: Transactional emails and notifications

6. **SMS Service (Optional)**
   - Options: Twilio, AWS SNS
   - Purpose: SMS notifications

7. **Push Notifications**
   - Options: Firebase Cloud Messaging, OneSignal
   - Purpose: Real-time consumer notifications

8. **Geocoding & Maps**
   - Options: Google Maps Platform, Mapbox
   - Purpose: Location-based features, DACSAI radius

---

## Database Schema Evolution

### New Collections Needed

```javascript
// Transactions
transactions: {
  id, consumer_id, retailer_id, items[], subtotal, savings, 
  contribution, round_up, net_proceed, charity_id, 
  payment_method, payment_id, status, fulfillment_type, 
  delivery_details, pickup_details, created_at, completed_at
}

// Disbursements
disbursements: {
  id, charity_id, amount, period_start, period_end, 
  transaction_count, status, processed_date, processed_by, 
  receipt_url
}

// Notifications
notifications: {
  id, user_id, type, title, message, rshd_id, 
  read, created_at, expires_at
}

// Audit Logs
audit_logs: {
  id, timestamp, user_id, user_role, action, entity_type, 
  entity_id, changes, ip_address, user_agent
}

// System Config
system_config: {
  id, key, value, updated_by, updated_at, description
}
```

### Collection Updates

```javascript
// Users - Add new fields
users: {
  // Existing fields...
  approval_status: String,
  approval_date: Date,
  approved_by: String,
  rejection_reason: String,
  notification_preferences: {
    push_enabled: Boolean,
    email_enabled: Boolean,
    sms_enabled: Boolean
  }
}

// RSHD Items - Add new fields
rshd_items: {
  // Existing fields...
  barcode: String,
  image_url: String,
  expiry_date: Date,
  contribution_percentage: Number,
  status: "active" | "expired" | "sold_out" | "removed"
}
```

---

## Testing Scope by Module

### Retailer App Testing
- RSHD posting with all fields
- Discount enforcement (only 33%, 66%, 99% allowed)
- Barcode scanning flow (mocked/real)
- Expiry date OCR (mocked/real)
- Quantity validation
- Contribution calculation accuracy
- Edit and delete RSHDs
- Approval status visibility

### Consumer App Testing
- DACSAI setup with map
- Radius selection and visualization
- Favorite categories selection
- Charity selection and round-up
- Radar view with real-time RSHDs
- Filtering by category and discount
- Notification receipt and display
- DACDRLP-List management
- Add to cart and checkout flow
- Net Proceed calculation display
- Delivery vs. pickup selection
- Payment processing

### Admin Dashboard Testing
- Retailer approval workflow
- Charity CRUD operations
- Contribution aggregation accuracy
- Disbursement creation and execution
- Receipt generation
- Compliance rule enforcement
- Report generation (all types)
- Audit log viewing and searching
- System configuration changes
- Dashboard metrics accuracy

### Backend Testing
- Net Proceed computation accuracy
- DRLPDAC-SNL generation logic
- Transaction validation
- Audit log creation
- Geospatial queries (RSHDs in radius)
- Real-time notification triggers
- Payment webhooks
- Data aggregation jobs

### Integration Testing
- End-to-end RSHD posting to consumer purchase
- Multi-role user (same email as consumer and retailer)
- Payment to disbursement flow
- Notification trigger to consumer action
- Admin approval to retailer access

---

## Development Approach

### Sprint Structure (2-week sprints recommended)

**Sprint 1-2**: Phase 1 - Retailer App Enhancement  
**Sprint 3-4**: Phase 2.1-2.2 - Consumer Onboarding & Radar View  
**Sprint 5**: Phase 2.3 - Notifications System  
**Sprint 6**: Phase 2.4-2.5 - DACDRLP-List & Checkout  
**Sprint 7-8**: Phase 3.1-3.3 - Admin Core Features  
**Sprint 9**: Phase 3.4-3.6 - Admin Compliance & Dashboards  
**Sprint 10**: Phase 4 - Backend Services Enhancement  
**Sprint 11**: Phase 5 - Frontend Shared Components  
**Sprint 12**: Integration Testing, Bug Fixes, Polish  

### Definition of Done
- [ ] Feature code completed and reviewed
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] API documentation updated
- [ ] Frontend components documented
- [ ] Manual testing completed
- [ ] Performance tested (where applicable)
- [ ] Accessibility checked
- [ ] Security reviewed
- [ ] Deployed to staging environment
- [ ] Product owner approval

---

## Risk Assessment

### High-Risk Items
1. **Third-party API integrations** (Barcode, OCR, DoorDash, Stripe)
   - Mitigation: Start with mocked versions, integrate incrementally

2. **Real-time notifications at scale**
   - Mitigation: Use proven tech (Firebase), implement rate limiting

3. **Geospatial queries performance**
   - Mitigation: Proper MongoDB indexing, caching layer

4. **Payment processing compliance**
   - Mitigation: Use Stripe's built-in compliance features, consult legal

5. **Complex Net Proceed calculations**
   - Mitigation: Comprehensive unit tests, financial audit

### Medium-Risk Items
1. Location permissions for mobile users
2. Charity disbursement accuracy
3. Multi-role user edge cases
4. Data privacy and GDPR compliance

---

## Success Metrics

### Consumer Metrics
- User registration and activation rate
- Active users (DAU, MAU)
- RSHDs discovered per user
- Conversion rate (view to purchase)
- Average order value
- Retention rate

### Retailer Metrics
- Retailer onboarding rate
- RSHDs posted per retailer
- Sell-through rate by discount level
- Retailer satisfaction score

### Platform Metrics
- Total transaction volume
- Total contributions to charities
- System uptime
- API response times
- Error rates

### Impact Metrics
- Total food waste prevented (estimated)
- Total dollars saved by consumers
- Total dollars donated to charities

---

## Next Steps

1. **Review this plan** with stakeholders for alignment
2. **Prioritize features** based on business value and dependencies
3. **Set up development environment** for team
4. **Create initial sprint backlog** for Phase 1
5. **Identify and onboard** third-party service providers
6. **Establish CI/CD pipeline** for automated testing and deployment
7. **Begin Sprint 1** with Retailer App enhancement

---

## Document Version History

- **v1.0** - Initial implementation plan based on seed summary (Created: Current Date)
