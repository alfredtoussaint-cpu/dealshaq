# DealShaq Seed Summary

DealShaq is structured into five modules:  
- **Retailer App (DRLP)**  
- **Consumer App (DAC)**  
- **Admin Dashboard**  
- **Backend Services**  
- **Frontend Shared Components**

---

## Admin Duties
- Approve/reject DRLP onboarding, suspend/remove non‑compliant DRLPs  
- Maintain charity list, validate selections  
- Aggregate contributions, execute disbursements, issue receipts  
- Generate dashboards and compliance reports  
- Monitor logs, enforce compliance rules  
- Manage taxonomy, discount thresholds, DACSAI radius rules  
- Handle escalations and overrides  

---

## Responsibility Matrix (Condensed)
- **Retailer App**: RSHD posting, discount enforcement, barcode/expiry/quantity validation, contribution calculation  
- **Consumer App**: Onboarding validation, favorites validation, charity + round‑up selection, Net Proceed at checkout, notifications  
- **Backend Services**: Store data, compute Net Proceed, aggregate transactions, generate DRLPDAC‑SNL, maintain logs  
- **Admin Dashboard**: Governance, approvals, compliance, reporting, system configuration, overrides  
- **Frontend Shared**: Shared login/authentication, notifications, cross‑app navigation, accessibility, error handling  

---

## Testing Scope
- **Retailer App**: RSHD posting, discount enforcement, validations, contribution calculation  
- **Consumer App**: Onboarding/favorites validation, charity + round‑up, Net Proceed, notifications  
- **Admin Dashboard**: DRLP approvals, charity validation, aggregation, disbursement, compliance reporting, audit logs, config updates  
- **Backend Services**: Net Proceed computation, aggregation, DRLPDAC‑SNL generation, validation, audit logging, disbursement files  
- **Frontend Shared**: Login/auth flows, notifications, navigation, accessibility, error handling
