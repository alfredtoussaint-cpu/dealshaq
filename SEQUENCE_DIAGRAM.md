# DealShaq Transaction Flow - Sequence Diagram

This document describes the complete transaction flow from RSHD posting to charity disbursement in the DealShaq system.

---

## Complete Transaction Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│Retailer │    │ Backend │    │Consumer │    │  Admin  │    │ Charity │
│  (DRLP) │    │ Service │    │  (DAC)  │    │Dashboard│    │         │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │              │
     │ 1. Register  │              │              │              │
     │─────────────>│              │              │              │
     │              │              │              │              │
     │              │ 2. Notify Admin              │              │
     │              │─────────────────────────────>│              │
     │              │              │              │              │
     │              │              │ 3. Review & Approve         │
     │              │<─────────────────────────────│              │
     │              │              │              │              │
     │ 4. Approval  │              │              │              │
     │<─────────────│              │              │              │
     │              │              │              │              │
     │ 5. Post RSHD │              │              │              │
     │  (item with  │              │              │              │
     │   discount)  │              │              │              │
     │─────────────>│              │              │              │
     │              │              │              │              │
     │              │ 6. Validate RSHD            │              │
     │              │  - Check discount levels    │              │
     │              │  - Validate expiry          │              │
     │              │  - Verify quantity          │              │
     │              │              │              │              │
     │              │ 7. Store RSHD               │              │
     │              │  in Database                │              │
     │              │              │              │              │
     │              │ 8. Generate DRLPDAC-SNL     │              │
     │              │  (Match RSHD to consumers)  │              │
     │              │              │              │              │
     │              │ 9. Send Notification        │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │              │ 10. View RSHD               │
     │              │              │  in Radar View              │
     │              │              │              │              │
     │              │              │ 11. Add to Cart             │
     │              │<─────────────│              │              │
     │              │              │              │              │
     │              │ 12. Calculate               │              │
     │              │  Net Proceed:               │              │
     │              │  Original: $10              │              │
     │              │  Discount: 66% = $6.60      │              │
     │              │  Savings: $6.60             │              │
     │              │  Contribution: 10% of       │              │
     │              │    savings = $0.66          │              │
     │              │  Round-up: $0.34            │              │
     │              │  Net Proceed: $3.40 + $0.66 │              │
     │              │    + $0.34 = $4.40          │              │
     │              │              │              │              │
     │              │ 13. Display Net Proceed     │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │              │ 14. Choose Fulfillment      │
     │              │              │  (Delivery/Pickup)          │
     │              │<─────────────│              │              │
     │              │              │              │              │
     │              │ 15. If Delivery:            │              │
     │              │  Call DoorDash API          │              │
     │              │              │              │              │
     │              │ 16. Process Payment         │              │
     │              │  via Stripe                 │              │
     │              │              │              │              │
     │              │ 17. Create Transaction      │              │
     │              │  Record                     │              │
     │              │              │              │              │
     │              │ 18. Update RSHD Quantity    │              │
     │              │              │              │              │
     │              │ 19. Send Confirmation       │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │ 20. Notify   │              │              │              │
     │  Sale        │              │              │              │
     │<─────────────│              │              │              │
     │              │              │              │              │
     │              │ 21. Aggregate Contributions │              │
     │              │  (Background Job - Daily)   │              │
     │              │              │              │              │
     │              │ 22. Generate Report         │              │
     │              │─────────────────────────────>│              │
     │              │              │              │              │
     │              │              │ 23. Review Contributions    │
     │              │              │              │              │
     │              │              │ 24. Create Disbursement     │
     │              │<─────────────────────────────│              │
     │              │              │              │              │
     │              │ 25. Process Payment         │              │
     │              │──────────────────────────────────────────>│
     │              │              │              │              │
     │              │ 26. Generate Receipt        │              │
     │              │──────────────────────────────────────────>│
     │              │              │              │              │
     │              │              │ 27. Send Receipt to Consumer│
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │ 28. Update Dashboard        │              │
     │              │─────────────────────────────>│              │
     │              │              │              │              │
     │              │ 29. Log Transaction         │              │
     │              │  in Audit Log               │              │
     │              │              │              │              │
```

---

## Flow Details

### 1-4: Retailer Onboarding
- Retailer registers with email, store name, and charity selection
- Backend notifies admin of pending approval
- Admin reviews retailer credentials
- Backend sends approval notification to retailer

### 5-7: RSHD Posting
- Retailer creates RSHD with:
  - Product details (name, barcode, category)
  - Original price
  - Discount level (33%, 66%, or 99%)
  - Quantity
  - Expiry date
  - Product image (optional)
- Backend validates all fields
- Backend stores RSHD in database with status "active"

### 8-9: Consumer Notification
- Backend matching engine (DRLPDAC-SNL generator) runs:
  - Finds all consumers with DACSAI overlapping retailer location
  - Filters by consumer's DACFI-List (favorite categories)
  - Checks if retailer is in consumer's DACDRLP-List (if specified)
- Backend sends push notification to matched consumers
- Backend creates notification record in database

### 10-13: Discovery & Cart
- Consumer sees RSHD in Radar View (real-time list)
- Consumer filters by category, discount level, or distance
- Consumer adds RSHD to cart
- Backend calculates preliminary Net Proceed

### 14-16: Fulfillment Selection
- Consumer chooses delivery or pickup
- If delivery: Backend calls DoorDash API with:
  - Retailer address
  - Consumer delivery address
  - Estimated delivery fee
- Backend updates Net Proceed with delivery fee (if applicable)

### 17-19: Payment & Confirmation
- Backend processes payment via Stripe
- Backend creates transaction record with:
  - All RSHD items
  - Subtotal (discounted prices)
  - Total savings
  - Contribution amount (retailer's % of savings)
  - Round-up amount (if consumer opted in)
  - Net Proceed (total charged)
  - Charity ID
  - Payment method and payment ID
  - Fulfillment details
- Backend decrements RSHD quantities
- Backend sends confirmation email to consumer
- Backend sends sale notification to retailer

### 20: Retailer Notification
- Retailer receives notification of sale
- Retailer prepares order for pickup or delivery

### 21-22: Contribution Aggregation
- Background job runs daily (or weekly)
- Backend aggregates all contributions by charity
- Backend generates contribution report for admin

### 23-25: Disbursement
- Admin reviews contribution totals
- Admin creates disbursement for charity
- Backend processes payment to charity (via Stripe or wire transfer)
- Backend updates disbursement status to "completed"

### 26-27: Receipts
- Backend generates donation receipt PDF
- Backend sends receipt to consumer via email
- Backend sends summary to charity

### 28-29: Audit & Dashboard
- Backend updates admin dashboard with latest metrics
- Backend logs all transaction details in audit log

---

## Alternative Flows

### A1: Retailer Approval Rejected
```
Admin (Step 3) ──> Reject with Reason ──> Backend ──> Notify Retailer
                                                    ──> Log Rejection
```

### A2: RSHD Validation Failure
```
Retailer (Step 5) ──> Invalid RSHD ──> Backend Validation
                                    ──> Return Error to Retailer
                                    ──> Retailer Corrects & Resubmits
```

### A3: Payment Failure
```
Consumer (Step 16) ──> Payment Failed ──> Backend
                                       ──> Notify Consumer
                                       ──> Keep Cart Items
                                       ──> Allow Retry
```

### A4: Delivery API Unavailable
```
Consumer (Step 15) ──> Choose Delivery ──> DoorDash API Error
                                        ──> Backend Fallback to Pickup Only
                                        ──> Notify Consumer
```

### A5: RSHD Sold Out
```
Consumer (Step 11) ──> Add to Cart ──> Check Inventory
                                    ──> Quantity = 0
                                    ──> Return "Sold Out" Error
                                    ──> Remove from Radar View
```

---

## Net Proceed Calculation Example

### Scenario 1: 66% Discount, 10% Contribution, $1 Round-up
```
Original Price:     $10.00
Discount (66%):     -$6.60
──────────────────────────
Discounted Price:   $3.40
Savings:            $6.60

Contribution (10%): $0.66  (10% of $6.60 savings)
Round-up:           $0.34  (to reach $5.00)
──────────────────────────
Net Proceed:        $4.40  ($3.40 + $0.66 + $0.34)

Consumer Pays:      $4.40
Consumer Saves:     $5.60  (vs. original $10.00)
Charity Receives:   $1.00  ($0.66 contribution + $0.34 round-up)
Retailer Receives:  $3.40  (discounted price)
```

### Scenario 2: 99% Discount, 5% Contribution, No Round-up
```
Original Price:     $20.00
Discount (99%):     -$19.80
──────────────────────────
Discounted Price:   $0.20
Savings:            $19.80

Contribution (5%):  $0.99  (5% of $19.80 savings)
Round-up:           $0.00  (consumer opted out)
──────────────────────────
Net Proceed:        $1.19  ($0.20 + $0.99 + $0.00)

Consumer Pays:      $1.19
Consumer Saves:     $18.81 (vs. original $20.00)
Charity Receives:   $0.99  (contribution only)
Retailer Receives:  $0.20  (discounted price)
```

---

## Error Handling & Retry Logic

### Payment Failures
- Automatic retry (up to 3 attempts) for transient errors
- Display clear error message to consumer
- Offer alternative payment methods
- Keep cart intact for retry

### API Failures (DoorDash, Stripe, etc.)
- Circuit breaker pattern to prevent cascade failures
- Fallback to alternative options when possible
- Queue failed operations for retry
- Alert admin for persistent failures

### Inventory Conflicts
- Pessimistic locking during checkout
- Reserve items for 10 minutes during checkout process
- Release reserved items if checkout abandoned
- Real-time inventory updates across all consumers

---

## Security Considerations

### Payment Security
- All payments processed via Stripe (PCI compliant)
- No credit card data stored in DealShaq database
- Use Stripe tokens for payment processing
- Implement 3D Secure for high-value transactions

### Transaction Integrity
- Atomic operations for inventory updates
- Transaction rollback on payment failure
- Audit trail for all financial transactions
- Reconciliation reports for financial accuracy

### Access Control
- Consumers can only view their own transactions
- Retailers can only view transactions for their RSHDs
- Admins have full read access (with audit logging)
- Role-based permissions enforced at API level

---

## Performance Optimization

### Caching Strategy
- Cache RSHD listings (TTL: 1 minute)
- Cache consumer preferences
- Cache geospatial queries for popular locations
- Invalidate cache on RSHD updates

### Database Indexing
```javascript
// Recommended indexes
rshd_items: [
  { location: "2dsphere" },  // Geospatial queries
  { category: 1, discount_level: 1 },  // Filtering
  { expiry_date: 1 },  // Cleanup jobs
  { retailer_id: 1, status: 1 }  // Retailer dashboard
]

transactions: [
  { consumer_id: 1, created_at: -1 },  // Consumer history
  { retailer_id: 1, created_at: -1 },  // Retailer history
  { charity_id: 1, created_at: -1 },  // Contribution aggregation
  { status: 1, created_at: -1 }  // Admin dashboard
]
```

### Load Balancing
- Distribute DRLPDAC-SNL generation across workers
- Queue notification sending for batch processing
- Separate read/write database instances for high traffic

---

## Monitoring & Alerts

### Key Metrics to Monitor
- Transaction success rate
- Payment failure rate
- Average checkout time
- RSHD posting rate
- Notification delivery rate
- API response times
- Database query performance

### Alerts to Configure
- Payment failure rate > 5%
- API error rate > 2%
- Database query time > 1 second
- Pending retailer approvals > 10
- Failed disbursements
- Low charity contribution balance

---

This sequence diagram provides the foundation for implementing the complete DealShaq transaction flow, from RSHD posting through charity disbursement, with comprehensive error handling and security measures.
