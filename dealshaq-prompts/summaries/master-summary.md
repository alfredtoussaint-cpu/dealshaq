# DealShaq Master Summary

**Last Updated:** December 19, 2025

## System Overview
DealShaq is a surplus-driven grocery discount marketplace connecting retailers (DRLPs) with consumers (DACs). Retailers post time-sensitive deals (RSHDs), and the system notifies interested local consumers.

## Core Implemented Features

### Geographic Filtering (DACSAI)
- **DACSAI:** Circular area around DAC's delivery location (center + radius)
- **DACSAI-Rad:** Configurable radius (0.1-9.9 miles)
- **DACDRLP-List:** Retailers a DAC receives notifications from
- **DRLPDAC-List:** DACs who receive notifications from a DRLP
- **Bidirectional Sync:** Lists are always kept in sync

### Notification System
1. Geographic filter: Only DACs in DRLPDAC-List considered
2. Preference filter: Match against DACFI-List
3. Brand/generic matching logic
4. Stop-after-first-hit optimization

### Discount Model
| Level | Consumer Discount | Description |
|-------|------------------|-------------|
| 1 | 50% OFF | Standard Deal |
| 2 | 60% OFF | Hot Deal |
| 3 | 75% OFF | Sizzling Hot Deal |

## Technology Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI (Python), MongoDB
- **Libraries:** geohash-utils (distance calculation)
- **Email:** Resend API
