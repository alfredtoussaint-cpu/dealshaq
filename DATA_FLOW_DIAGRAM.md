# DealShaq System - Data Flow Diagram

This document illustrates how data flows through the DealShaq system across all modules and external services.

---

## High-Level System Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          External Services                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Barcode  │  │   OCR    │  │ DoorDash │  │  Stripe  │  │  Email   │ │
│  │   API    │  │   API    │  │   API    │  │   API    │  │ Service  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────┘
        │             │             │             │             │
        ▼             ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend Services Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  FastAPI     │  │   Matching   │  │  Aggregation │  │   Queue    │ │
│  │  REST API    │  │    Engine    │  │   Service    │  │  Manager   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
│         └─────────────────┼─────────────────┼─────────────────┘        │
│                           │                 │                          │
└───────────────────────────┼─────────────────┼──────────────────────────┘
                            │                 │
                            ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       MongoDB Database Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Users   │  │   RSHD   │  │Transaction│ │Charities │  │  Audit   │ │
│  │Collection│  │Collection│  │Collection │ │Collection│  │   Logs   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │Favorites │  │Notifications│ │Disbursements│ │ Config │               │
│  │Collection│  │Collection│  │Collection │ │Collection│               │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────────────────┐
│                       Frontend Applications Layer                       │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       │
│  │  Consumer    │       │   Retailer   │       │    Admin     │       │
│  │  React App   │       │  React App   │       │  Dashboard   │       │
│  │    (DAC)     │       │    (DRLP)    │       │              │       │
│  └──────────────┘       └──────────────┘       └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Data Flows by Feature

### 1. User Registration & Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Registration Flow                                                       │
└─────────────────────────────────────────────────────────────────────────┘

Frontend (Consumer/Retailer)
  │
  │ 1. Submit Registration Form
  │    - email
  │    - password (plain text)
  │    - name
  │    - role (DAC or DRLP)
  │    - charity_id
  │    - additional role-specific data
  │
  ▼
Backend API (/api/auth/register)
  │
  │ 2. Validate Input
  │    - Check email uniqueness
  │    - Validate password strength
  │    - Verify charity exists
  │
  │ 3. Hash Password
  │    - Use Passlib bcrypt
  │
  │ 4. Create User Document
  │    {
  │      email: String,
  │      password: String (hashed),
  │      role: String,
  │      name: String,
  │      charity_id: String,
  │      approval_status: "pending" (for DRLP),
  │      created_at: Date
  │    }
  │
  ▼
MongoDB (users collection)
  │
  │ 5. Insert User Document
  │
  │ 6. Return User ID
  │
  ▼
Backend API
  │
  │ 7. Generate JWT Token
  │    - Payload: user_id, email, role
  │    - Sign with SECRET_KEY
  │
  │ 8. If DRLP: Create Notification for Admin
  │
  ▼
Frontend
  │
  │ 9. Store JWT in localStorage
  │
  │ 10. Redirect to Dashboard
  │
```

**Login Flow** (similar but with password verification instead of creation)

---

### 2. RSHD Posting Flow (Retailer)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ RSHD Creation Flow                                                      │
└─────────────────────────────────────────────────────────────────────────┘

Retailer App
  │
  │ 1. Scan Barcode (Optional)
  │    - Capture barcode image
  │
  ▼
Barcode API (External)
  │
  │ 2. Return Product Info
  │    - product_name
  │    - category
  │    - standard_price
  │
  ▼
Retailer App
  │
  │ 3. Scan Expiry Date (Optional)
  │    - Capture expiry date image
  │
  ▼
OCR API (External)
  │
  │ 4. Return Expiry Date
  │    - expiry_date (parsed)
  │
  ▼
Retailer App
  │
  │ 5. Complete RSHD Form
  │    - name
  │    - category
  │    - original_price
  │    - discount_level (33%, 66%, or 99%)
  │    - quantity
  │    - expiry_date
  │    - contribution_percentage
  │    - image (optional)
  │
  │ 6. Submit RSHD
  │
  ▼
Backend API (/api/rshd/items)
  │
  │ 7. Validate RSHD Data
  │    - discount_level in [33, 66, 99]
  │    - quantity > 0
  │    - expiry_date > today
  │    - category in taxonomy
  │
  │ 8. Calculate Discounted Price
  │    discounted_price = original_price × (1 - discount_level/100)
  │
  │ 9. Get Retailer Location
  │    - From user profile
  │
  │ 10. Create RSHD Document
  │     {
  │       id: UUID,
  │       retailer_id: String,
  │       name: String,
  │       category: String,
  │       original_price: Number,
  │       discounted_price: Number,
  │       discount_level: Number,
  │       quantity: Number,
  │       expiry_date: Date,
  │       contribution_percentage: Number,
  │       location: { lat, lng },
  │       status: "active",
  │       created_at: Date
  │     }
  │
  ▼
MongoDB (rshd_items collection)
  │
  │ 11. Insert RSHD
  │
  │ 12. Create Geospatial Index (if not exists)
  │     - db.rshd_items.createIndex({ location: "2dsphere" })
  │
  ▼
Matching Engine (Background Job)
  │
  │ 13. Query Matching Consumers
  │     - Find users with role = "DAC"
  │     - WHERE RSHD.location within user.dacsai_radius
  │     - AND RSHD.category IN user.favorite_categories
  │     - AND (user.dac_drlp_list is empty OR RSHD.retailer_id IN user.dac_drlp_list)
  │
  ▼
MongoDB (users collection)
  │
  │ 14. Return Matched Consumers
  │
  ▼
Notification Service
  │
  │ 15. For Each Matched Consumer:
  │     - Create Notification Document
  │       {
  │         user_id: String,
  │         type: "new_rshd",
  │         title: "New Deal Near You!",
  │         message: "...",
  │         rshd_id: String,
  │         read: false,
  │         created_at: Date
  │       }
  │
  ▼
MongoDB (notifications collection)
  │
  │ 16. Insert Notifications (Batch)
  │
  ▼
Push Notification Service
  │
  │ 17. Send Push Notifications
  │     - To web browsers (Web Push API)
  │     - Or mobile devices (FCM)
  │
  ▼
Consumer App
  │
  │ 18. Display Notification Banner
  │
```

---

### 3. Consumer Discovery & Radar View Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Radar View Data Flow                                                    │
└─────────────────────────────────────────────────────────────────────────┘

Consumer App
  │
  │ 1. Load Radar View
  │    - Get user location from profile
  │
  │ 2. Request RSHDs in Area
  │
  ▼
Backend API (/api/consumer/radar)
  │
  │ 3. Get User Preferences
  │    - dacsai_radius (from users collection)
  │    - favorite_categories (from favorites collection)
  │    - dac_drlp_list (from users collection)
  │
  ▼
MongoDB (users + favorites collections)
  │
  │ 4. Return User Data
  │
  ▼
Backend API
  │
  │ 5. Geospatial Query
  │    db.rshd_items.find({
  │      location: {
  │        $near: {
  │          $geometry: { type: "Point", coordinates: [user.lng, user.lat] },
  │          $maxDistance: user.dacsai_radius * 1609.34  // miles to meters
  │        }
  │      },
  │      category: { $in: user.favorite_categories },
  │      status: "active",
  │      quantity: { $gt: 0 },
  │      expiry_date: { $gte: new Date() }
  │    })
  │
  ▼
MongoDB (rshd_items collection with 2dsphere index)
  │
  │ 6. Return Matching RSHDs
  │
  ▼
Backend API
  │
  │ 7. For Each RSHD:
  │    - Calculate distance from consumer
  │    - Enrich with retailer info
  │    - Calculate potential savings
  │
  │ 8. Sort RSHDs
  │    - By distance, discount_level, or expiry_date
  │
  │ 9. Return Response
  │    {
  │      rshds: [
  │        {
  │          id, name, category,
  │          original_price, discounted_price, discount_level,
  │          quantity, expiry_date,
  │          retailer: { id, name, location },
  │          distance: Number (miles),
  │          savings: Number
  │        }
  │      ]
  │    }
  │
  ▼
Consumer App
  │
  │ 10. Render RSHD Cards
  │     - Show on map (pins)
  │     - Show in list view
  │
  │ 11. Apply Client-Side Filters
  │     - By discount level
  │     - By category
  │     - By retailer
  │
  │ 12. Real-Time Updates
  │     - Poll /api/consumer/radar every 30 seconds
  │     - Or use WebSocket for live updates
  │
```

---

### 4. Checkout & Transaction Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Complete Checkout Flow                                                  │
└─────────────────────────────────────────────────────────────────────────┘

Consumer App
  │
  │ 1. Add Items to Cart
  │    - Store in localStorage/state
  │    cart = [
  │      { rshd_id, quantity }
  │    ]
  │
  │ 2. Navigate to Checkout
  │
  │ 3. Select Fulfillment Method
  │    - "delivery" or "pickup"
  │
  │ 4. If Delivery: Enter Delivery Address
  │
  │ 5. Submit Checkout Request
  │
  ▼
Backend API (/api/checkout)
  │
  │ 6. Validate Cart Items
  │    - Check RSHD availability
  │    - Verify quantities
  │    - Lock inventory (pessimistic lock)
  │
  ▼
MongoDB (rshd_items collection)
  │
  │ 7. Return RSHD Details
  │
  ▼
Backend API
  │
  │ 8. Calculate Order Totals
  │    For each item:
  │      item_total = rshd.discounted_price × quantity
  │      item_savings = (rshd.original_price - rshd.discounted_price) × quantity
  │      item_contribution = item_savings × rshd.contribution_percentage
  │    
  │    subtotal = sum(item_total)
  │    total_savings = sum(item_savings)
  │    total_contribution = sum(item_contribution)
  │
  │ 9. If Delivery: Call DoorDash API
  │
  ▼
DoorDash API (External)
  │
  │ 10. Return Delivery Quote
  │     {
  │       delivery_fee: Number,
  │       estimated_time: Number (minutes)
  │     }
  │
  ▼
Backend API
  │
  │ 11. Calculate Round-Up (if opted in)
  │     current_total = subtotal + total_contribution + delivery_fee
  │     round_up = Math.ceil(current_total) - current_total
  │
  │ 12. Calculate Net Proceed
  │     net_proceed = subtotal + total_contribution + round_up + delivery_fee
  │
  │ 13. Get User's Charity
  │
  ▼
MongoDB (users collection)
  │
  │ 14. Return Charity ID
  │
  ▼
Backend API
  │
  │ 15. Create Stripe Payment Intent
  │
  ▼
Stripe API (External)
  │
  │ 16. Return Payment Intent
  │     {
  │       client_secret: String,
  │       payment_intent_id: String
  │     }
  │
  ▼
Backend API
  │
  │ 17. Return Checkout Summary to Frontend
  │     {
  │       items: [...],
  │       subtotal, total_savings, total_contribution, round_up,
  │       delivery_fee (if delivery),
  │       net_proceed,
  │       charity: { id, name },
  │       payment_client_secret
  │     }
  │
  ▼
Consumer App
  │
  │ 18. Display Order Summary
  │
  │ 19. User Confirms & Enters Payment
  │
  │ 20. Submit Payment to Stripe
  │
  ▼
Stripe API
  │
  │ 21. Process Payment
  │
  │ 22. Return Payment Confirmation
  │
  ▼
Consumer App
  │
  │ 23. Confirm Payment with Backend
  │
  ▼
Backend API (/api/checkout/confirm)
  │
  │ 24. Verify Payment with Stripe
  │
  ▼
Stripe API
  │
  │ 25. Return Payment Status
  │
  ▼
Backend API
  │
  │ 26. If Payment Successful:
  │     a. Create Transaction Document
  │        {
  │          id: UUID,
  │          consumer_id, retailer_id,
  │          items: [...],
  │          subtotal, savings, contribution, round_up,
  │          net_proceed,
  │          charity_id,
  │          payment_method, payment_id,
  │          status: "completed",
  │          fulfillment_type: "delivery" | "pickup",
  │          delivery_details: {...},
  │          created_at: Date
  │        }
  │
  ▼
MongoDB (transactions collection)
  │
  │ 27. Insert Transaction
  │
  ▼
Backend API
  │
  │ 28. Update RSHD Quantities
  │     For each item:
  │       db.rshd_items.updateOne(
  │         { id: rshd_id },
  │         { $inc: { quantity: -quantity } }
  │       )
  │
  │ 29. If quantity = 0: Set status = "sold_out"
  │
  ▼
MongoDB (rshd_items collection)
  │
  │ 30. Update Complete
  │
  ▼
Backend API
  │
  │ 31. Release Inventory Lock
  │
  │ 32. Create Audit Log Entry
  │
  ▼
MongoDB (audit_logs collection)
  │
  │ 33. Log Transaction
  │
  ▼
Email Service (External)
  │
  │ 34. Send Confirmation Email to Consumer
  │     - Order details
  │     - Receipt PDF
  │
  │ 35. Send Notification to Retailer
  │     - New order alert
  │     - Order details
  │
  ▼
Consumer App & Retailer App
  │
  │ 36. Display Success Message
  │
```

---

### 5. Contribution Aggregation & Disbursement Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Charity Disbursement Flow                                               │
└─────────────────────────────────────────────────────────────────────────┘

Background Job (Daily/Weekly Cron)
  │
  │ 1. Trigger Aggregation Job
  │
  ▼
Backend Aggregation Service
  │
  │ 2. Query Transactions
  │    - WHERE created_at >= last_disbursement_date
  │    - AND status = "completed"
  │
  ▼
MongoDB (transactions collection)
  │
  │ 3. Return Transactions
  │
  ▼
Backend Aggregation Service
  │
  │ 4. Aggregate by Charity
  │    charity_totals = transactions.reduce((acc, txn) => {
  │      if (!acc[txn.charity_id]) {
  │        acc[txn.charity_id] = {
  │          total_contribution: 0,
  │          total_round_up: 0,
  │          transaction_count: 0
  │        }
  │      }
  │      acc[txn.charity_id].total_contribution += txn.contribution
  │      acc[txn.charity_id].total_round_up += txn.round_up
  │      acc[txn.charity_id].transaction_count++
  │      return acc
  │    }, {})
  │
  │ 5. For Each Charity:
  │     total_amount = total_contribution + total_round_up
  │
  │ 6. Create Disbursement Documents
  │    {
  │      id: UUID,
  │      charity_id: String,
  │      amount: Number,
  │      period_start: Date,
  │      period_end: Date,
  │      transaction_count: Number,
  │      status: "pending",
  │      created_at: Date
  │    }
  │
  ▼
MongoDB (disbursements collection)
  │
  │ 7. Insert Disbursements
  │
  ▼
Backend Aggregation Service
  │
  │ 8. Generate Report
  │    - CSV file with all transactions
  │    - PDF summary by charity
  │
  │ 9. Notify Admin
  │
  ▼
Admin Dashboard
  │
  │ 10. Admin Reviews Disbursements
  │     - Verify amounts
  │     - Check transaction details
  │
  │ 11. Admin Approves Disbursement
  │
  ▼
Backend API (/api/admin/disbursement/execute)
  │
  │ 12. Process Payment to Charity
  │
  ▼
Stripe API (or Wire Transfer)
  │
  │ 13. Execute Payment
  │
  │ 14. Return Payment Confirmation
  │
  ▼
Backend API
  │
  │ 15. Update Disbursement Status
  │     - status = "completed"
  │     - processed_date = Date
  │     - processed_by = admin_id
  │
  ▼
MongoDB (disbursements collection)
  │
  │ 16. Update Document
  │
  ▼
Backend API
  │
  │ 17. Generate Donation Receipts
  │     - PDF for each contributing consumer
  │
  ▼
Email Service
  │
  │ 18. Send Receipts to Consumers
  │     - Email with PDF attachment
  │
  │ 19. Send Summary to Charity
  │     - Disbursement details
  │     - Transaction breakdown
  │
  ▼
Admin Dashboard
  │
  │ 20. Update Dashboard Metrics
  │     - Total disbursed
  │     - Disbursement history chart
  │
```

---

## Data Storage & Retrieval Patterns

### Read-Heavy Operations
- **Radar View** (frequent polling)
  - Cache RSHD listings per location
  - Use Redis for 30-second TTL cache
  - Invalidate on RSHD updates

- **Consumer Preferences** (every API call)
  - Cache in-memory after login
  - Invalidate on preference update

### Write-Heavy Operations
- **Transaction Creation** (peak times)
  - Use queue for notification sending
  - Batch insert audit logs
  - Async inventory updates

### Real-Time Operations
- **Notification Delivery**
  - Use message queue (Redis/RabbitMQ)
  - Workers process queue in parallel
  - Retry failed deliveries

---

## Data Consistency & Integrity

### Atomic Operations
```javascript
// Example: Update RSHD quantity atomically
session = client.start_session()
try {
  session.start_transaction()
  
  // Check quantity
  rshd = db.rshd_items.find_one({ id: rshd_id }, session=session)
  if rshd.quantity < order_quantity:
    throw Error("Insufficient quantity")
  
  // Decrement quantity
  db.rshd_items.update_one(
    { id: rshd_id },
    { $inc: { quantity: -order_quantity } },
    session=session
  )
  
  // Create transaction
  db.transactions.insert_one(transaction_doc, session=session)
  
  session.commit_transaction()
} catch (error) {
  session.abort_transaction()
  throw error
} finally {
  session.end_session()
}
```

### Eventual Consistency
- Notification delivery (can be delayed)
- Dashboard metrics (updated every 5 minutes)
- Contribution aggregation (daily job)

---

## Data Retention & Archival

### Active Data (Hot Storage)
- Users: Indefinite
- RSHDs: Until expired + 7 days
- Transactions: Current year
- Notifications: 30 days

### Archived Data (Cold Storage)
- Transactions: Previous years (S3/Cloud Storage)
- Audit Logs: > 1 year old
- Disbursements: All historical (for tax purposes)

---

## Data Privacy & Security

### PII Protection
- Passwords: Hashed with bcrypt
- Payment info: Never stored (Stripe tokens only)
- Email addresses: Encrypted at rest
- Location data: Pseudonymized in analytics

### Access Control
- Row-level security in queries
- JWT token validation on every API call
- Role-based access control (RBAC)
- Audit logging for all data access

---

This data flow diagram provides a comprehensive view of how data moves through the DealShaq system, from user input through processing, storage, and eventual output across all three applications and external integrations.
