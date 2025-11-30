# DealShaq System Architecture

## Overview
DealShaq is a supply-initiated grocery deals platform consisting of 3 web applications (Consumer, Retailer, Admin) and a unified backend with MongoDB database.

## System Components

### 1. Backend (FastAPI + MongoDB)
**Location**: `/app/backend/`
**Tech Stack**: Python FastAPI, Motor (async MongoDB), JWT, Stripe, Pydantic

**Key Modules**:
- `server.py` - Main application with all API endpoints
- Authentication with role-based access (DAC, DRLP, Admin)
- Discount model calculations
- RSHD matching algorithm
- Charity contribution calculations
- Tax calculations (mock)
- Stripe payment integration

**API Endpoints** (30+ total):
```
Auth:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

Charities:
- GET /api/charities
- POST /api/charities

DRLP Locations:
- POST /api/drlp/locations
- GET /api/drlp/locations
- GET /api/drlp/my-location

RSHD Items:
- POST /api/rshd/items (with discount level validation)
- GET /api/rshd/items
- GET /api/rshd/my-items
- PUT /api/rshd/items/{id}
- DELETE /api/rshd/items/{id}

Favorites (DACFI-List):
- POST /api/favorites
- GET /api/favorites
- DELETE /api/favorites/{id}

Notifications:
- GET /api/notifications
- PUT /api/notifications/{id}/read

Orders:
- POST /api/orders (with Stripe payment)
- GET /api/orders

Admin:
- GET /api/admin/stats
- GET /api/admin/users
- GET /api/admin/items
```

**Database Collections** (MongoDB):
- `users` - DACs, DRLPs, Admins with auth data
- `charities` - Partner charities
- `drlp_locations` - Retailer store locations
- `rshd_items` - Posted deals with discount levels
- `favorites` - DAC DACFI-Lists
- `orders` - Transaction records
- `notifications` - Deal alerts for DACs

### 2. Consumer App (React)
**Location**: `/app/frontend/src/apps/ConsumerApp.js` + `/app/frontend/src/components/consumer/`
**Role**: DAC (DealShaq App Consumer)

**Features**:
- **Authentication**: Email/password registration with charity selection
- **Dashboard**: Featured RSHDs, notification alerts, stats
- **Browse Deals**: View all available RSHDs with search and category filters
- **DACFI-List Management**: Add/remove favorite categories/subcategories
- **Notifications**: View deal alerts matching favorites, mark as read
- **Checkout**: 
  - Select delivery (mock DoorDash) or pickup
  - Stripe payment integration
  - Tax calculation
  - Charity contributions (DAC 0.45% + DRLP 0.45% + optional round-up)
- **Order History**: View past orders and charity impact

**Key Components**:
- `ConsumerAuth.js` - Login/register
- `ConsumerDashboard.js` - Home page
- `ConsumerBrowse.js` - RSHD catalog
- `ConsumerFavorites.js` - DACFI-List management
- `ConsumerNotifications.js` - Deal alerts
- `ConsumerCheckout.js` - Payment flow with Stripe
- `ConsumerOrders.js` - Order history

### 3. Retailer App (React)
**Location**: `/app/frontend/src/apps/RetailerApp.js` + `/app/frontend/src/components/retailer/`
**Role**: DRLP (DealShaq Retailer Location Partner)

**Features**:
- **Authentication**: Email/password registration with charity selection
- **Location Setup**: Store name, address, charity partner, operating hours
- **Post RSHD Items**:
  - Select discount level (1, 2, or 3)
  - Enter product details (name, category, regular price, quantity)
  - Barcode scanning (mock)
  - Photo capture (mock)
  - Real-time pricing preview showing both DRLP and consumer discounts
- **Inventory Management**: View, edit, delete posted RSHDs
- **Orders**: View and manage customer orders
- **Dashboard**: Sales stats, active deals, revenue tracking

**Key Components**:
- `RetailerAuth.js` - Login/register
- `RetailerDashboard.js` - Home page with stats
- `RetailerPostItem.js` - RSHD creation with discount level selector
- `RetailerInventory.js` - Manage posted items
- `RetailerOrders.js` - Fulfill customer orders

### 4. Admin Dashboard (React)
**Location**: `/app/frontend/src/apps/AdminApp.js` + `/app/frontend/src/components/admin/`
**Role**: Admin (System Administrator)

**Features**:
- **Authentication**: Admin-only login
- **System Overview Dashboard**:
  - Total DACs, DRLPs, orders, active items
  - Revenue analytics
  - Charity impact tracking (DAC + DRLP + round-up totals)
  - Discount model distribution (Level 1/2/3 breakdown)
- **User Management**: View all DACs, DRLPs, Admins by role
- **Transaction Reports**: Complete order history with financial details
- **360° Visibility**: All system operations, notifications, API calls

**Key Components**:
- `AdminAuth.js` - Admin login
- `AdminDashboard.js` - Overview with discount model analysis
- `AdminUsers.js` - User management by role
- `AdminTransactions.js` - Order history and revenue

## Data Flow: Supply-Initiated Transaction

### Step 1: RSHD Posting (Sales Initiation)
```
DRLP Associate → Retailer App → POST /api/rshd/items
                                    ↓
                            Backend validates:
                            - Discount level (1-3 only)
                            - Calculate consumer discount
                            - Calculate final price
                                    ↓
                            Store in database
```

### Step 2: Smart Matching
```
Backend receives RSHD
    ↓
Get DRLP location from database
    ↓
Find all DACs with this DRLP in their DACDRLP-List (geographic match)
    ↓
For each DAC:
    - Check if RSHD category/subcategory matches their DACFI-List
    - If match: Add to DRLPDAC-SNL
    ↓
Generate notifications for matched DACs
```

### Step 3: Notification Dispatch
```
For each DAC in DRLPDAC-SNL:
    ↓
Create notification record
    ↓
In-app notification (real-time in Consumer app)
    ↓
[Future: Push notification, Email, SMS]
```

### Step 4: Consumer Purchase
```
DAC views notification → Consumer App
    ↓
Browses RSHD details
    ↓
Adds to cart
    ↓
Checkout:
    - Select delivery (mock DoorDash) or pickup
    - Calculate tax (mock jurisdiction-based)
    - Calculate charity contributions
    - Process Stripe payment
    ↓
Order created → Notifications sent → Inventory updated
```

### Step 5: Admin Oversight
```
Admin Dashboard
    ↓
Real-time stats:
    - New orders
    - Revenue tracking
    - Charity contributions
    - Discount level distribution
    ↓
Transaction reports
    ↓
User management
```

## Discount Model Integration

### Backend Calculation
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

### Frontend Display
- **Consumer sees**: `consumer_discount_percent` (50%, 60%, 75%)
- **Retailer sees**: Both `drlp_discount_percent` and `consumer_discount_percent`
- **Admin sees**: Distribution across levels + both discount types

## Authentication & Authorization

### JWT-Based Auth
- Token stored in localStorage
- Included in all API requests via Bearer header
- Expires after 24 hours
- Role-based access control enforced at API level

### Roles
- **DAC**: Consumer with favorites, shopping area, order history
- **DRLP**: Retailer with location, inventory, order fulfillment
- **Admin**: System oversight with full access

### Protected Routes
- Frontend: Role-specific app routing
- Backend: `@Depends(get_current_user)` on protected endpoints

## Integration Points

### Real Integrations (v1.0)
- **Stripe**: Payment processing (test mode)
- **MongoDB**: Database for all collections
- **JWT**: Authentication tokens

### Mock Integrations (v1.0)
- **DoorDash API**: Delivery scheduling (hardcoded fee: $5.99)
- **Tax API**: Jurisdiction-based tax calculation (flat 8%)
- **Barcode Scanner**: UPC/PLU scanning (manual entry)
- **Photo Capture**: Item images (URL input)
- **Push Notifications**: In-app only
- **SMS/Email Notifications**: Not implemented

### Future Integrations (v2.0+)
- Real DoorDash API for delivery logistics
- TaxJar/Avalara for accurate tax calculations
- Mobile barcode scanning via camera
- Firebase for push notifications
- Twilio for SMS alerts
- SendGrid for email notifications

## Environment Configuration

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=dealshaq_db
JWT_SECRET_KEY=dealshaq-secret-key-change-in-production
STRIPE_SECRET_KEY=sk_test_...
CORS_ORIGINS=*
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://dealshaq-discounts.preview.emergentagent.com
```

## Deployment Architecture

### Services
- **Backend**: FastAPI on port 8001 (supervisor managed)
- **Frontend**: React on port 3000 (supervisor managed)
- **MongoDB**: Running locally on port 27017

### Hot Reload
- Both services restart automatically on code changes
- Manual restart required for .env changes or new dependencies

### URL Routing (Kubernetes Ingress)
- `/api/*` → Backend (port 8001)
- `/*` → Frontend (port 3000)

## Key Technical Decisions

### Why Supply-Initiated?
- Maximizes efficiency for perishables and urgent inventory
- Reduces noise for consumers (no spam)
- Retailer-driven urgency creates natural time constraints
- Geographic + preference matching ensures relevance

### Why MongoDB?
- Flexible schema for evolving models
- Fast read/write for matching algorithm
- Easy to query nested structures (DACFI-Lists, coordinates)
- Native support for arrays and objects

### Why React Single-Page Apps?
- Responsive design works on mobile browsers
- Fast development with Shadcn UI components
- Client-side routing for smooth UX
- Easy to separate Consumer/Retailer/Admin concerns

### Why JWT Auth?
- Stateless authentication
- Role-based access built into token
- Easy to validate on backend
- Works across multiple apps

## Performance Considerations

### Matching Algorithm Optimization
- Existence-check model (O(n) where n = # of DACs with this DRLP in their list)
- Pre-filter by geography before checking preferences
- Batch notification creation for multiple matches

### Database Indexes
- `users.email` for fast login lookups
- `users.role` for admin user queries
- `rshd_items.status` + `quantity` for active deals
- `favorites.dac_id` for matching algorithm
- `notifications.dac_id` + `read` for notification lists

## Security Measures

### Authentication
- Passwords hashed with bcrypt
- JWT tokens with expiration
- Role validation on all protected routes

### Data Protection
- MongoDB _id field excluded from responses
- password_hash never returned in API responses
- CORS configured for specific origins

### Payment Security
- Stripe handles all payment data (PCI compliant)
- No credit card numbers stored in database
- Payment intents used for secure transaction flow

## Testing Strategy

### Backend Testing
- Manual API testing via curl
- Python test scripts for calculations
- Validation testing for discount levels

### Frontend Testing
- Manual testing via browser
- Screenshot testing for UI verification
- End-to-end flow testing planned

### Integration Testing
- Stripe test mode for payment flows
- Mock services for DoorDash, tax calculations

## Monitoring & Observability

### Logs
- Backend: `/var/log/supervisor/backend.*.log`
- Frontend: `/var/log/supervisor/frontend.*.log`
- Structured logging with timestamps

### Admin Dashboard Metrics
- Real-time system stats
- Transaction volume
- Charity contributions
- Discount level distribution
- User counts by role

## Documentation

### Files Created
- `/app/DISCOUNT_MODEL.md` - Discount level specifications
- `/app/VALUE_PROPOSITION.md` - Platform value proposition
- `/app/SYSTEM_ARCHITECTURE.md` - This file
- `/app/README.md` - Project overview (existing)

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Production-ready MVP with mock integrations
