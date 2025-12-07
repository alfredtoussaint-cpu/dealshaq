from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
import stripe
import resend
import secrets
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Resend configuration
resend.api_key = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@dealshaq.com')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://dealshaq.com')

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== MODELS =====

# Auth Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # DAC, DRLP, Admin
    charity_id: Optional[str] = None
    delivery_location: Optional[Dict[str, Any]] = None  # {address, coordinates: {lat, lng}}
    dacsai_radius: Optional[float] = 5.0  # DACSAI: 0.1 - 9.9 miles

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = None  # Optional: filter by role if provided

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    charity_id: Optional[str] = None
    delivery_location: Optional[Dict[str, Any]] = None  # {address, coordinates: {lat, lng}}
    dacsai_radius: Optional[float] = 5.0  # DACSAI: 0.1 - 9.9 miles
    notification_prefs: Optional[Dict[str, bool]] = {"email": True, "push": True, "sms": False}
    created_at: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    role: Optional[str] = None

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Charity Models
class CharityCreate(BaseModel):
    name: str
    description: str
    logo_url: Optional[str] = None

class Charity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    logo_url: Optional[str] = None

# DRLP Location Models
class DRLPLocationCreate(BaseModel):
    name: str
    address: str
    coordinates: Dict[str, float]  # {lat, lng}
    charity_id: str
    operating_hours: Optional[str] = "9 AM - 9 PM"

class DRLPLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    address: str
    coordinates: Dict[str, float]
    charity_id: str
    operating_hours: str

# DealShaq 20-Category Taxonomy
VALID_CATEGORIES = [
    "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
    "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
    "Snacks & Candy", "Frozen Foods", "Beverages",
    "Alcoholic Beverages", "Deli & Prepared Foods",
    "Breakfast & Cereal", "Pasta, Rice & Grains",
    "Oils, Sauces & Spices", "Baby & Kids",
    "Health & Nutrition", "Household Essentials",
    "Personal Care", "Pet Supplies"
]

# RSHD Item Models
class RSHDItemCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str  # Must be one of VALID_CATEGORIES
    subcategory: Optional[str] = ""  # Optional, internal use only
    regular_price: float
    discount_level: int  # 1, 2, or 3 only
    quantity: int
    barcode: Optional[str] = ""
    weight: Optional[float] = None
    image_url: Optional[str] = ""
    is_taxable: bool = True
    attributes: Optional[Dict[str, Any]] = {}  # organic, gluten-free, etc.

class RSHDItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    drlp_id: str
    drlp_name: str
    drlp_address: str
    name: str
    description: str
    category: str  # One of VALID_CATEGORIES
    subcategory: Optional[str] = ""  # Optional, internal only
    regular_price: float
    drlp_discount_percent: float  # Discount DRLP gives to DealShaq
    consumer_discount_percent: float  # Discount consumer sees
    deal_price: float  # Final price consumer pays
    discount_level: int  # 1, 2, or 3
    quantity: int
    barcode: str
    weight: Optional[float] = None
    image_url: str
    is_taxable: bool
    attributes: Optional[Dict[str, Any]] = {}  # organic, gluten-free, etc.
    posted_at: str
    status: str = "available"

# Favorite Models (DACFI-List)
class FavoriteCreate(BaseModel):
    category: str  # Must be one of VALID_CATEGORIES only (no subcategories)

class Favorite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    dac_id: str
    category: str  # Top-level category only

# Order Models
class OrderItem(BaseModel):
    rshd_id: str
    name: str
    price: float
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItem]
    delivery_method: str  # delivery or pickup
    delivery_address: Optional[str] = None
    pickup_time: Optional[str] = None
    charity_roundup: Optional[float] = 0.0
    payment_method_id: str

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    dac_id: str
    dac_name: str
    drlp_id: str
    drlp_name: str
    items: List[OrderItem]
    subtotal: float
    tax: float
    delivery_fee: float
    charity_dac: float
    charity_drlp: float
    charity_roundup: float
    total: float
    delivery_method: str
    delivery_address: Optional[str] = None
    pickup_time: Optional[str] = None
    status: str = "pending"
    payment_intent_id: Optional[str] = None
    created_at: str

# Notification Models
class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    dac_id: str
    rshd_id: str
    message: str
    read: bool = False
    created_at: str

# ===== HELPER FUNCTIONS =====

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def calculate_tax(subtotal: float, is_taxable: bool = True) -> float:
    """Mock tax calculation - 8% for taxable items"""
    if not is_taxable:
        return 0.0
    return round(subtotal * 0.08, 2)

def calculate_delivery_fee(delivery_method: str) -> float:
    """Mock delivery fee calculation"""
    if delivery_method == "delivery":
        return 5.99
    return 0.0

def calculate_charity_contributions(net_proceed: float) -> Dict[str, float]:
    """Calculate charity contributions: 0.45% each for DAC and DRLP"""
    dac_share = round(net_proceed * 0.0045, 2)
    drlp_share = round(net_proceed * 0.0045, 2)
    return {"dac_share": dac_share, "drlp_share": drlp_share}

async def initialize_dacdrlp_list(dac_id: str):
    """Initialize DACDRLP-List for new DAC
    
    V1.0: Simplified - all DRLPs visible to all DACs
    V2.0: Will use DACSAI radius to filter DRLPs geographically
    """
    # For now, create empty DACDRLP-List
    # In v2.0, this will populate with DRLPs within DACSAI
    await db.dacdrlp_list.insert_one({
        "dac_id": dac_id,
        "retailers": [],  # Will be populated in v2.0 based on DACSAI
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })

def calculate_discount_mapping(discount_level: int, regular_price: float) -> Dict[str, float]:
    """
    Calculate discount percentages and final price based on DealShaq discount model
    
    Discount Levels:
    - Level 1: DRLP → DealShaq: 60%, Consumer sees: 50% off
    - Level 2: DRLP → DealShaq: 75%, Consumer sees: 60% off
    - Level 3: DRLP → DealShaq: 90%, Consumer sees: 75% off
    - Level 0: INACTIVE (15% → 0%)
    """
    # Discount mapping: {level: (drlp_discount, consumer_discount)}
    discount_map = {
        1: (60.0, 50.0),
        2: (75.0, 60.0),
        3: (90.0, 75.0),
    }
    
    if discount_level not in discount_map:
        raise ValueError(f"Invalid discount level {discount_level}. Only levels 1-3 are supported in Version 1.0")
    
    drlp_discount, consumer_discount = discount_map[discount_level]
    
    # Calculate final consumer price
    deal_price = round(regular_price * (1 - consumer_discount / 100), 2)
    
    return {
        "drlp_discount_percent": drlp_discount,
        "consumer_discount_percent": consumer_discount,
        "deal_price": deal_price
    }

# ===== API ROUTES =====

# Health Check
@api_router.get("/")
async def root():
    return {"message": "DealShaq API is running"}

# Get valid categories
@api_router.get("/categories")
async def get_categories():
    """Return the 20 valid grocery categories for taxonomy"""
    return {"categories": VALID_CATEGORIES}

# ===== AUTH ROUTES =====

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # SECURITY: Block public Admin registration
    if user_data.role == "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin accounts cannot be created through public registration. Contact system administrator."
        )
    
    # Only allow DAC and DRLP registration
    if user_data.role not in ["DAC", "DRLP"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Only 'DAC' (Consumer) and 'DRLP' (Retailer) registration allowed."
        )
    
    # Check if user exists with this email AND role (same email allowed for different roles)
    existing = await db.users.find_one({"email": user_data.email, "role": user_data.role})
    if existing:
        raise HTTPException(status_code=400, detail=f"Email already registered as {user_data.role}")
    
    # Validate DACSAI radius for DAC users
    if user_data.role == "DAC" and user_data.dacsai_radius:
        if not (0.1 <= user_data.dacsai_radius <= 9.9):
            raise HTTPException(
                status_code=400,
                detail="DACSAI radius must be between 0.1 and 9.9 miles"
            )
    
    user_dict = user_data.model_dump()
    user_dict["id"] = str(uuid.uuid4())
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    user_dict["notification_prefs"] = {"email": True, "push": True, "sms": False}
    del user_dict["password"]
    
    await db.users.insert_one(user_dict)
    
    # For DAC users, initialize DACDRLP-List (v1.0: simplified, all DRLPs visible)
    if user_data.role == "DAC":
        await initialize_dacdrlp_list(user_dict["id"])
    
    access_token = create_access_token(data={"sub": user_dict["id"]})
    
    user_response = {k: v for k, v in user_dict.items() if k != "password_hash"}
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    # Build query - filter by role if provided (allows same email for different roles)
    query = {"email": credentials.email}
    if credentials.role:
        query["role"] = credentials.role
    
    user = await db.users.find_one(query, {"_id": 0})
    
    if not user:
        if credentials.role:
            raise HTTPException(status_code=401, detail=f"No {credentials.role} account found with this email")
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: Dict = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/password-reset/request")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset - sends email with reset link"""
    success_response = {
        "message": "If an account exists with this email, a password reset link has been sent.",
        "status": "success"
    }
    
    try:
        query = {"email": request.email}
        if request.role:
            query["role"] = request.role
        
        user = await db.users.find_one(query, {"_id": 0})
        
        if not user:
            return success_response
        
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        reset_token_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "token_hash": token_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False
        }
        
        await db.password_reset_tokens.insert_one(reset_token_data)
        
        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">DealShaq Password Reset</h2>
                    
                    <p>Hello,</p>
                    
                    <p>We received a request to reset your password for your DealShaq account. If you didn't make this request, you can safely ignore this email.</p>
                    
                    <p>To reset your password, click the button below:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #2563eb; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f3f4f6; padding: 10px; border-radius: 5px;">
                        <code>{reset_link}</code>
                    </p>
                    
                    <p style="color: #ef4444; font-weight: bold;">
                        This link will expire in 60 minutes.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        If you have any questions, please contact our support team at support@dealshaq.com
                    </p>
                </div>
            </body>
        </html>
        """
        
        params = {
            "from": SENDER_EMAIL,
            "to": [request.email],
            "subject": "Reset Your DealShaq Password",
            "html": html_content
        }
        
        email_response = resend.Emails.send(params)
        logger.info(f"Password reset email sent to {request.email}. Email ID: {email_response.get('id')}")
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
    
    return success_response

@api_router.post("/auth/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm):
    """Confirm password reset with token and new password"""
    
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    
    token_record = await db.password_reset_tokens.find_one(
        {"token_hash": token_hash},
        {"_id": 0}
    )
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if token_record.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used"
        )
    
    expires_at = datetime.fromisoformat(token_record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    user = await db.users.find_one({"id": token_record["user_id"]}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    hashed_password = hash_password(request.new_password)
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password_hash": hashed_password,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await db.password_reset_tokens.update_one(
        {"id": token_record["id"]},
        {"$set": {"used": True}}
    )
    
    try:
        confirmation_html = """
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #16a34a;">Password Changed Successfully</h2>
                    
                    <p>Hello,</p>
                    
                    <p>Your DealShaq password has been successfully changed. You can now log in with your new password.</p>
                    
                    <p style="color: #ef4444;">
                        If you didn't make this change, please contact us immediately at support@dealshaq.com
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        Thank you for using DealShaq!
                    </p>
                </div>
            </body>
        </html>
        """
        
        confirmation_params = {
            "from": SENDER_EMAIL,
            "to": [user["email"]],
            "subject": "Your DealShaq Password Was Changed",
            "html": confirmation_html
        }
        
        resend.Emails.send(confirmation_params)
        logger.info(f"Password confirmation email sent to {user['email']}")
        
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")
    
    return {
        "message": "Password has been successfully reset. You can now log in with your new password.",
        "status": "success"
    }

# ===== CHARITY ROUTES =====

@api_router.post("/charities", response_model=Charity)
async def create_charity(charity_data: CharityCreate, current_user: Dict = Depends(get_current_user)):
    charity_dict = charity_data.model_dump()
    charity_dict["id"] = str(uuid.uuid4())
    
    await db.charities.insert_one(charity_dict)
    return charity_dict

@api_router.get("/charities", response_model=List[Charity])
async def get_charities():
    charities = await db.charities.find({}, {"_id": 0}).to_list(1000)
    return charities

# ===== DRLP LOCATION ROUTES =====

@api_router.post("/drlp/locations", response_model=DRLPLocation)
async def create_drlp_location(location_data: DRLPLocationCreate, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DRLP":
        raise HTTPException(status_code=403, detail="Only DRLP users can create locations")
    
    location_dict = location_data.model_dump()
    location_dict["id"] = str(uuid.uuid4())
    location_dict["user_id"] = current_user["id"]
    
    await db.drlp_locations.insert_one(location_dict)
    return location_dict

@api_router.get("/drlp/locations", response_model=List[DRLPLocation])
async def get_drlp_locations():
    locations = await db.drlp_locations.find({}, {"_id": 0}).to_list(1000)
    return locations

@api_router.get("/drlp/my-location", response_model=DRLPLocation)
async def get_my_drlp_location(current_user: Dict = Depends(get_current_user)):
    location = await db.drlp_locations.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

# ===== RSHD ITEM ROUTES =====

@api_router.post("/rshd/items", response_model=RSHDItem)
async def create_rshd_item(item_data: RSHDItemCreate, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DRLP":
        raise HTTPException(status_code=403, detail="Only DRLP users can post items")
    
    # Validate category (must be one of 20 valid categories)
    if item_data.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    # Validate discount level (only 1-3 allowed in v1.0)
    if item_data.discount_level not in [1, 2, 3]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid discount level. Only levels 1, 2, and 3 are supported in Version 1.0. Level 0 is inactive."
        )
    
    # Get DRLP location
    location = await db.drlp_locations.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not location:
        raise HTTPException(status_code=404, detail="DRLP location not found")
    
    # Calculate discount percentages and final price
    discount_info = calculate_discount_mapping(item_data.discount_level, item_data.regular_price)
    
    item_dict = item_data.model_dump()
    item_dict["id"] = str(uuid.uuid4())
    item_dict["drlp_id"] = current_user["id"]
    item_dict["drlp_name"] = location["name"]
    item_dict["drlp_address"] = location["address"]
    item_dict["drlp_discount_percent"] = discount_info["drlp_discount_percent"]
    item_dict["consumer_discount_percent"] = discount_info["consumer_discount_percent"]
    item_dict["deal_price"] = discount_info["deal_price"]
    item_dict["posted_at"] = datetime.now(timezone.utc).isoformat()
    item_dict["status"] = "available"
    
    await db.rshd_items.insert_one(item_dict)
    
    # Create notifications for matching DACs
    await create_matching_notifications(item_dict)
    
    return item_dict

async def create_matching_notifications(item: Dict):
    """Match RSHD with DAC favorites and create notifications
    
    Matching Logic:
    - Only matches on top-level category (subcategories ignored)
    - DAC with "Fruits" in DACFI-List gets notified for ALL fruits RSHDs
    - Existence-check model: O(n) where n = DACs with this category
    """
    # Find DACs with matching category in their DACFI-List
    matching_favorites = await db.favorites.find({
        "category": item["category"]  # Top-level category only
    }, {"_id": 0}).to_list(1000)
    
    dac_ids = list(set([fav["dac_id"] for fav in matching_favorites]))
    
    for dac_id in dac_ids:
        notification = {
            "id": str(uuid.uuid4()),
            "dac_id": dac_id,
            "rshd_id": item["id"],
            "message": f"New deal on {item['name']} - {item['consumer_discount_percent']}% off at {item['drlp_name']}!",
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)

@api_router.get("/rshd/items", response_model=List[RSHDItem])
async def get_rshd_items(category: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    query = {"status": "available", "quantity": {"$gt": 0}}
    if category:
        query["category"] = category
    
    items = await db.rshd_items.find(query, {"_id": 0}).sort("posted_at", -1).to_list(1000)
    return items

@api_router.get("/rshd/my-items", response_model=List[RSHDItem])
async def get_my_rshd_items(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DRLP":
        raise HTTPException(status_code=403, detail="Only DRLP users can view their items")
    
    items = await db.rshd_items.find({"drlp_id": current_user["id"]}, {"_id": 0}).sort("posted_at", -1).to_list(1000)
    return items

@api_router.put("/rshd/items/{item_id}")
async def update_rshd_item(item_id: str, update_data: Dict, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DRLP":
        raise HTTPException(status_code=403, detail="Only DRLP users can update items")
    
    result = await db.rshd_items.update_one(
        {"id": item_id, "drlp_id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item updated successfully"}

@api_router.delete("/rshd/items/{item_id}")
async def delete_rshd_item(item_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DRLP":
        raise HTTPException(status_code=403, detail="Only DRLP users can delete items")
    
    result = await db.rshd_items.delete_one({"id": item_id, "drlp_id": current_user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}

# ===== FAVORITE ROUTES =====

@api_router.post("/favorites", response_model=Favorite)
async def create_favorite(favorite_data: FavoriteCreate, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can create favorites")
    
    # Validate category (must be one of 20 valid categories)
    if favorite_data.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    # Check if already exists
    existing = await db.favorites.find_one({
        "dac_id": current_user["id"],
        "category": favorite_data.category
    })
    if existing:
        raise HTTPException(status_code=400, detail="Category already in favorites")
    
    favorite_dict = favorite_data.model_dump()
    favorite_dict["id"] = str(uuid.uuid4())
    favorite_dict["dac_id"] = current_user["id"]
    
    await db.favorites.insert_one(favorite_dict)
    return favorite_dict

@api_router.get("/favorites", response_model=List[Favorite])
async def get_favorites(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can view favorites")
    
    favorites = await db.favorites.find({"dac_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return favorites

@api_router.delete("/favorites/{favorite_id}")
async def delete_favorite(favorite_id: str, current_user: Dict = Depends(get_current_user)):
    result = await db.favorites.delete_one({"id": favorite_id, "dac_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Favorite removed"}

# ===== NOTIFICATION ROUTES =====

@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can view notifications")
    
    notifications = await db.notifications.find({"dac_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: Dict = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "dac_id": current_user["id"]},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

# ===== ORDER ROUTES =====

@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can create orders")
    
    # Calculate totals
    subtotal = sum(item.price * item.quantity for item in order_data.items)
    
    # Get first item's DRLP info
    first_item = await db.rshd_items.find_one({"id": order_data.items[0].rshd_id}, {"_id": 0})
    if not first_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    tax = calculate_tax(subtotal, first_item.get("is_taxable", True))
    delivery_fee = calculate_delivery_fee(order_data.delivery_method)
    
    # Calculate charity contributions
    net_proceed = subtotal + tax + delivery_fee - 0  # Assuming full amount to DealShaq
    charity_contrib = calculate_charity_contributions(net_proceed)
    
    total = subtotal + tax + delivery_fee + order_data.charity_roundup
    
    # Process Stripe payment
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # Convert to cents
            currency="usd",
            payment_method=order_data.payment_method_id,
            confirm=True,
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never"
            }
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
    
    order_dict = {
        "id": str(uuid.uuid4()),
        "dac_id": current_user["id"],
        "dac_name": current_user["name"],
        "drlp_id": first_item["drlp_id"],
        "drlp_name": first_item["drlp_name"],
        "items": [item.model_dump() for item in order_data.items],
        "subtotal": subtotal,
        "tax": tax,
        "delivery_fee": delivery_fee,
        "charity_dac": charity_contrib["dac_share"],
        "charity_drlp": charity_contrib["drlp_share"],
        "charity_roundup": order_data.charity_roundup,
        "total": total,
        "delivery_method": order_data.delivery_method,
        "delivery_address": order_data.delivery_address,
        "pickup_time": order_data.pickup_time,
        "status": "confirmed",
        "payment_intent_id": payment_intent.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.insert_one(order_dict)
    
    # Update item quantities
    for item in order_data.items:
        await db.rshd_items.update_one(
            {"id": item.rshd_id},
            {"$inc": {"quantity": -item.quantity}}
        )
    
    return order_dict

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] == "DAC":
        orders = await db.orders.find({"dac_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    elif current_user["role"] == "DRLP":
        orders = await db.orders.find({"drlp_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    else:  # Admin
        orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return orders

# ===== ADMIN ROUTES =====

@api_router.get("/admin/stats")
async def get_admin_stats(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_dacs = await db.users.count_documents({"role": "DAC"})
    total_drlps = await db.users.count_documents({"role": "DRLP"})
    total_orders = await db.orders.count_documents({})
    total_items = await db.rshd_items.count_documents({"status": "available"})
    
    # Calculate total revenue and charity contributions
    orders = await db.orders.find({}, {"_id": 0}).to_list(10000)
    total_revenue = sum(order["total"] for order in orders)
    total_charity_dac = sum(order["charity_dac"] for order in orders)
    total_charity_drlp = sum(order["charity_drlp"] for order in orders)
    total_charity_roundup = sum(order["charity_roundup"] for order in orders)
    
    return {
        "total_dacs": total_dacs,
        "total_drlps": total_drlps,
        "total_orders": total_orders,
        "total_items": total_items,
        "total_revenue": round(total_revenue, 2),
        "total_charity_dac": round(total_charity_dac, 2),
        "total_charity_drlp": round(total_charity_drlp, 2),
        "total_charity_roundup": round(total_charity_roundup, 2),
        "total_charity": round(total_charity_dac + total_charity_drlp + total_charity_roundup, 2)
    }

@api_router.post("/admin/create-admin")
async def create_admin(user_data: UserCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new Admin account - requires existing Admin authentication"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only existing Admins can create new Admin accounts")
    
    # Force role to Admin
    user_data.role = "Admin"
    
    # Check if admin with this email exists
    existing = await db.users.find_one({"email": user_data.email, "role": "Admin"})
    if existing:
        raise HTTPException(status_code=400, detail="Admin account with this email already exists")
    
    user_dict = user_data.model_dump()
    user_dict["id"] = str(uuid.uuid4())
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    user_dict["notification_prefs"] = {"email": True, "push": True, "sms": False}
    del user_dict["password"]
    
    await db.users.insert_one(user_dict)
    
    logger.info(f"New Admin account created by {current_user['email']}: {user_dict['email']}")
    
    return {"message": "Admin account created successfully", "email": user_dict["email"]}

@api_router.get("/admin/users")
async def get_all_users(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(10000)
    return users

@api_router.get("/admin/items")
async def get_all_items(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    items = await db.rshd_items.find({}, {"_id": 0}).to_list(10000)
    return items

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
