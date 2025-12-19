# DealShaq Data Flow Diagram

This document describes the data flow and system architecture of DealShaq.

## System Overview

```mermaid
flowchart TB
    subgraph Users
        DAC["🛒 Consumer (DAC)"]
        DRLP["🏪 Retailer (DRLP)"]
        ADMIN["👤 Admin"]
    end

    subgraph Frontend["Frontend (React)"]
        CA[Consumer App]
        RA[Retailer App]
        AA[Admin App]
    end

    subgraph Backend["Backend (FastAPI)"]
        AUTH[Auth Service]
        RSHD[RSHD Service]
        NOTIF[Notification Service]
        GEO[Geographic Service]
        SCHED[Scheduler Service]
        CAT[Categorization Service]
    end

    subgraph Database["MongoDB"]
        USERS[(users)]
        DRLPLOC[(drlp_locations)]
        DACDRLP[(dacdrlp_list)]
        DRLPDAC[(drlpdac_list)]
        RSHDITEMS[(rshd_items)]
        NOTIFS[(notifications)]
        ORDERS[(orders)]
    end

    subgraph External
        GEOCODE[Geocoding API]
        LLM[OpenAI / Emergent]
    end

    DAC --> CA
    DRLP --> RA
    ADMIN --> AA

    CA --> AUTH
    CA --> NOTIF
    CA --> GEO
    RA --> AUTH
    RA --> RSHD
    AA --> AUTH

    AUTH --> USERS
    RSHD --> RSHDITEMS
    RSHD --> NOTIF
    NOTIF --> NOTIFS
    NOTIF --> DRLPDAC
    GEO --> DACDRLP
    GEO --> DRLPDAC
    GEO --> DRLPLOC
    SCHED --> USERS
    SCHED --> ORDERS
    CAT --> LLM

    CA -.-> GEOCODE
```

## Data Models

### User Document (users collection)

```mermaid
erDiagram
    USER {
        string id PK
        string email UK
        string password_hash
        string name
        string role "DAC|DRLP|Admin"
        string charity_id FK
        object delivery_location "address, coordinates"
        float dacsai_rad "0.1 to 9.9 miles"
        array favorite_items "DACFI-List"
        int auto_favorite_threshold "0|3|6"
        object notification_prefs
        string created_at
    }

    FAVORITE_ITEM {
        string item_name
        string brand "nullable"
        string generic
        boolean has_brand
        string category
        array keywords
        object attributes
        string auto_added_date "nullable"
    }

    USER ||--o{ FAVORITE_ITEM : contains
```

### Geographic Data Models

```mermaid
erDiagram
    DACDRLP_LIST {
        string id PK
        string dac_id FK
        array retailers
        float dacsai_rad
        object dacsai_center "lat, lng"
        string updated_at
    }

    RETAILER_ENTRY {
        string drlp_id FK
        string drlp_name
        object drlp_location "lat, lng"
        float distance
        boolean inside_dacsai
        boolean manually_added
        boolean manually_removed
        string added_at
    }

    DRLPDAC_LIST {
        string id PK
        string drlp_id FK
        array dac_ids "list of DAC IDs"
        string updated_at
    }

    DRLP_LOCATION {
        string id PK
        string user_id FK
        string name
        string address
        object coordinates "lat, lng"
        string store_type
        array operating_hours
    }

    DACDRLP_LIST ||--o{ RETAILER_ENTRY : contains
    DRLP_LOCATION ||--|| DRLPDAC_LIST : has
```

### RSHD and Notification Models

```mermaid
erDiagram
    RSHD_ITEM {
        string id PK
        string drlp_id FK
        string name
        string category
        float original_price
        float discounted_price
        int discount_level "1|2|3"
        int quantity
        string expiry_date
        object attributes
        string status "active|sold|expired"
        string created_at
    }

    NOTIFICATION {
        string id PK
        string dac_id FK
        string rshd_id FK
        string type "rshd_match"
        string title
        string message
        object data
        boolean is_read
        string created_at
    }

    ORDER {
        string id PK
        string dac_id FK
        string drlp_id FK
        array items
        float subtotal
        float tax
        float total
        string status
        string created_at
    }

    RSHD_ITEM ||--o{ NOTIFICATION : triggers
    ORDER }o--|| RSHD_ITEM : contains
```

## Data Flow: RSHD Notification Matching

```mermaid
flowchart LR
    subgraph Input
        RSHD["RSHD Posted<br/>(category, name, attributes)"]
    end

    subgraph Geographic_Filter["Step 1: Geographic Filter"]
        DRLPDAC[(DRLPDAC-List)]
        ELIGIBLE["Eligible DACs<br/>(have DRLP in DACDRLP-List)"]
    end

    subgraph Preference_Filter["Step 2: Preference Filter"]
        DACFI["DACFI-List<br/>(favorite_items)"]
        MATCH{"Match?"}
    end

    subgraph Output
        NOTIF[(Notifications)]
        SNL["DRLPDAC-SNL<br/>(Subset Notification List)"]
    end

    RSHD --> DRLPDAC
    DRLPDAC --> ELIGIBLE
    ELIGIBLE --> DACFI
    DACFI --> MATCH
    MATCH -->|Yes| SNL
    MATCH -->|No| SKIP[Skip DAC]
    SNL --> NOTIF
```

## Data Flow: DACSAI Update

```mermaid
flowchart TB
    subgraph Input
        UPDATE["DAC updates DACSAI-Rad"]
        COORDS["DAC Coordinates"]
        RADIUS["New Radius"]
    end

    subgraph Processing
        QUERY["Query all DRLP locations"]
        CALC["Calculate distances"]
        FILTER{"Inside DACSAI?"}
        CHECK{"Manual override?"}
    end

    subgraph DACDRLP["DACDRLP-List Update"]
        ADD_DRLP["Add DRLP"]
        KEEP_DRLP["Keep DRLP"]
        REMOVE_DRLP["Remove DRLP"]
    end

    subgraph DRLPDAC["DRLPDAC-List Sync"]
        ADD_DAC["Add DAC to DRLP list"]
        REMOVE_DAC["Remove DAC from DRLP list"]
    end

    UPDATE --> QUERY
    COORDS --> CALC
    RADIUS --> CALC
    QUERY --> CALC
    CALC --> FILTER

    FILTER -->|Yes| CHECK
    FILTER -->|No| CHECK

    CHECK -->|manually_removed| KEEP_DRLP
    CHECK -->|manually_added| KEEP_DRLP
    CHECK -->|Inside & not removed| ADD_DRLP
    CHECK -->|Outside & not added| REMOVE_DRLP

    ADD_DRLP --> ADD_DAC
    REMOVE_DRLP --> REMOVE_DAC
```

## API Endpoints Overview

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user (DAC/DRLP) |
| `/api/auth/login` | POST | Login and get JWT token |
| `/api/auth/me` | GET | Get current user profile |
| `/api/auth/password-reset/request` | POST | Request password reset email |
| `/api/auth/password-reset/confirm` | POST | Confirm password reset |

### DAC Geographic (DACSAI / DACDRLP-List)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dac/retailers` | GET | Get DAC's DACDRLP-List |
| `/api/dac/retailers/add` | POST | Add retailer to list |
| `/api/dac/retailers/{id}` | DELETE | Remove retailer from list |
| `/api/dac/dacsai` | PUT | Update DACSAI-Rad |
| `/api/dac/location` | PUT | Update delivery location |

### DAC Favorites (DACFI-List)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/favorites/items` | GET | Get favorite items by category |
| `/api/favorites/items` | POST | Add item to favorites |
| `/api/favorites/items/delete` | POST | Remove item from favorites |
| `/api/users/settings/auto-threshold` | PUT | Update auto-add threshold |

### DRLP Operations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/drlp/locations` | GET | List all DRLP locations |
| `/api/drlp/locations` | POST | Create DRLP location |
| `/api/drlp/my-location` | GET | Get current DRLP's location |

### RSHD Operations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rshd/items` | GET | List RSHD items (by category) |
| `/api/rshd/items` | POST | Post new RSHD item |
| `/api/rshd/my-items` | GET | Get DRLP's own items |
| `/api/rshd/items/{id}` | PUT | Update RSHD item |
| `/api/rshd/items/{id}` | DELETE | Delete RSHD item |

### Notifications
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications` | GET | Get DAC's notifications |
| `/api/notifications/{id}/read` | PUT | Mark notification as read |

### Orders
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/orders` | GET | Get user's orders |
| `/api/orders` | POST | Create new order |

## Key Principles

1. **Bidirectional Sync**: DACDRLP-List and DRLPDAC-List must always be in sync
2. **Manual Override Preservation**: User preferences (add/remove) are never auto-reverted
3. **Stop-after-first-hit**: Efficiency optimization in notification matching
4. **Brand/Generic Logic**: Flexible matching based on user preference specificity
5. **Geographic Anchoring**: All notifications are geographically relevant via DACSAI
