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
import re

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
    delivery_location: Optional[Dict[str, Any]] = None  # {address, coordinates: {lat, lng}} - DACSAI center
    dacsai_rad: Optional[float] = 5.0  # DACSAI-Rad: 0.1 - 9.9 miles (defines DACSAI size)

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
    delivery_location: Optional[Dict[str, Any]] = None  # {address, coordinates: {lat, lng}} - DACSAI center
    dacsai_rad: Optional[float] = 5.0  # DACSAI-Rad: 0.1 - 9.9 miles (defines DACSAI size)
    notification_prefs: Optional[Dict[str, bool]] = {"email": True, "push": True, "sms": False}
    favorite_items: Optional[List[Dict[str, Any]]] = []  # Item-level favorites with keywords & attributes
    auto_favorite_threshold: Optional[int] = 0  # 0=Never, 3, or 6 days
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
    "Deli & Prepared Foods", "Breakfast & Cereal",
    "Pasta, Rice & Grains", "Oils, Sauces & Spices",
    "Baby & Kids", "Health & Nutrition", "Household Essentials",
    "Personal Care", "Pet Supplies", "Miscellaneous"
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

# Item-Level Favorite Models (DACFI-List)
class FavoriteItemCreate(BaseModel):
    item_name: str  # User input: e.g., "Organic 2% Milk", "Granola"

class FavoriteItemDelete(BaseModel):
    item_name: str  # Exact match to remove

class FavoriteItem(BaseModel):
    item_name: str
    category: str
    keywords: List[str]
    attributes: Dict[str, bool]
    auto_added_date: Optional[str] = None  # null = explicit, date = implicit

class AutoThresholdUpdate(BaseModel):
    auto_favorite_threshold: int  # 0, 3, or 6

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
    except Exception as e:
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

import math

def calculate_distance_miles(coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
    """Calculate distance between two coordinates using Haversine formula
    
    Args:
        coord1: {lat, lng} - First coordinate (e.g., DAC's delivery location)
        coord2: {lat, lng} - Second coordinate (e.g., DRLP's location)
    
    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles
    
    lat1 = math.radians(coord1["lat"])
    lat2 = math.radians(coord2["lat"])
    dlat = math.radians(coord2["lat"] - coord1["lat"])
    dlng = math.radians(coord2["lng"] - coord1["lng"])
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return round(R * c, 2)

async def initialize_dacdrlp_list(dac_id: str, delivery_location: Dict[str, Any], dacsai_rad: float):
    """Initialize DACDRLP-List for new DAC with geographic filtering
    
    Populates DACDRLP-List with all DRLPs domiciled inside the DAC's DACSAI.
    Also updates each DRLP's DRLPDAC-List to include this DAC (bidirectional sync).
    
    Args:
        dac_id: The DAC's user ID
        delivery_location: {address, coordinates: {lat, lng}} - Center of DACSAI
        dacsai_rad: Radius in miles (0.1 - 9.9) - Defines DACSAI size
    """
    retailers = []
    dac_coords = delivery_location.get("coordinates") if delivery_location else None
    
    if dac_coords:
        # Find all DRLP locations
        all_drlp_locations = await db.drlp_locations.find({}, {"_id": 0}).to_list(10000)
        
        for drlp_loc in all_drlp_locations:
            drlp_coords = drlp_loc.get("coordinates")
            if not drlp_coords:
                continue
            
            # Calculate distance from DAC to DRLP
            distance = calculate_distance_miles(dac_coords, drlp_coords)
            
            # Check if DRLP is inside DACSAI
            if distance <= dacsai_rad:
                retailers.append({
                    "drlp_id": drlp_loc["user_id"],
                    "drlp_name": drlp_loc["name"],
                    "drlp_location": drlp_coords,
                    "distance": distance,
                    "inside_dacsai": True,
                    "manually_added": False,
                    "manually_removed": False,
                    "added_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Bidirectional sync: Add DAC to this DRLP's DRLPDAC-List
                await add_dac_to_drlpdac_list(drlp_loc["user_id"], dac_id)
    
    # Create DACDRLP-List document
    await db.dacdrlp_list.insert_one({
        "dac_id": dac_id,
        "retailers": retailers,
        "dacsai_rad": dacsai_rad,
        "dacsai_center": dac_coords,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Initialized DACDRLP-List for DAC {dac_id} with {len(retailers)} retailers inside DACSAI (radius: {dacsai_rad} miles)")

async def add_dac_to_drlpdac_list(drlp_id: str, dac_id: str):
    """Add a DAC to a DRLP's DRLPDAC-List (bidirectional sync)"""
    result = await db.drlpdac_list.update_one(
        {"drlp_id": drlp_id},
        {
            "$addToSet": {"dac_ids": dac_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    logger.info(f"Added DAC {dac_id} to DRLP {drlp_id}'s DRLPDAC-List")

async def remove_dac_from_drlpdac_list(drlp_id: str, dac_id: str):
    """Remove a DAC from a DRLP's DRLPDAC-List (bidirectional sync)"""
    result = await db.drlpdac_list.update_one(
        {"drlp_id": drlp_id},
        {
            "$pull": {"dac_ids": dac_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    logger.info(f"Removed DAC {dac_id} from DRLP {drlp_id}'s DRLPDAC-List")

async def initialize_drlpdac_list(drlp_id: str, drlp_location: Dict[str, float]):
    """Initialize DRLPDAC-List for a new DRLP
    
    Finds all DACs whose DACSAI contains this DRLP's location and adds them.
    Also updates each DAC's DACDRLP-List to include this DRLP (bidirectional sync).
    """
    dac_ids = []
    
    # Find all DACs with delivery locations
    all_dacs = await db.users.find(
        {"role": "DAC", "delivery_location.coordinates": {"$exists": True}},
        {"_id": 0, "id": 1, "delivery_location": 1, "dacsai_rad": 1}
    ).to_list(10000)
    
    for dac in all_dacs:
        dac_coords = dac.get("delivery_location", {}).get("coordinates")
        dacsai_rad = dac.get("dacsai_rad", 5.0)
        
        if not dac_coords:
            continue
        
        # Calculate distance from DAC to this DRLP
        distance = calculate_distance_miles(dac_coords, drlp_location)
        
        # Check if this DRLP is inside DAC's DACSAI
        if distance <= dacsai_rad:
            dac_ids.append(dac["id"])
            
            # Bidirectional sync: Add this DRLP to DAC's DACDRLP-List
            await add_drlp_to_dacdrlp_list(dac["id"], drlp_id, drlp_location, distance)
    
    # Create DRLPDAC-List document
    await db.drlpdac_list.insert_one({
        "drlp_id": drlp_id,
        "dac_ids": dac_ids,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Initialized DRLPDAC-List for DRLP {drlp_id} with {len(dac_ids)} DACs")

async def add_drlp_to_dacdrlp_list(dac_id: str, drlp_id: str, drlp_location: Dict[str, float], distance: float):
    """Add a DRLP to a DAC's DACDRLP-List (called during DRLP registration)"""
    # Get DRLP name
    drlp_loc = await db.drlp_locations.find_one({"user_id": drlp_id}, {"_id": 0, "name": 1})
    drlp_name = drlp_loc.get("name", "Unknown") if drlp_loc else "Unknown"
    
    retailer_entry = {
        "drlp_id": drlp_id,
        "drlp_name": drlp_name,
        "drlp_location": drlp_location,
        "distance": distance,
        "inside_dacsai": True,
        "manually_added": False,
        "manually_removed": False,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.dacdrlp_list.update_one(
        {"dac_id": dac_id},
        {
            "$push": {"retailers": retailer_entry},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )

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
    
    # Validate DACSAI-Rad for DAC users
    if user_data.role == "DAC" and user_data.dacsai_rad:
        if not (0.1 <= user_data.dacsai_rad <= 9.9):
            raise HTTPException(
                status_code=400,
                detail="DACSAI-Rad must be between 0.1 and 9.9 miles"
            )
    
    user_dict = user_data.model_dump()
    user_dict["id"] = str(uuid.uuid4())
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    user_dict["notification_prefs"] = {"email": True, "push": True, "sms": False}
    
    # Initialize Enhanced DACFI-List fields for DAC users
    if user_data.role == "DAC":
        user_dict["favorite_items"] = []
        user_dict["auto_favorite_threshold"] = 0  # Default: Never
    
    del user_dict["password"]
    
    await db.users.insert_one(user_dict)
    
    # For DAC users, initialize DACDRLP-List with geographic filtering
    if user_data.role == "DAC":
        delivery_location = user_data.delivery_location
        dacsai_rad = user_data.dacsai_rad or 5.0
        await initialize_dacdrlp_list(user_dict["id"], delivery_location, dacsai_rad)
    
    access_token = create_access_token(data={"sub": user_dict["id"]})
    
    # Remove MongoDB _id and password_hash from response
    user_response = {k: v for k, v in user_dict.items() if k not in ["password_hash", "_id"]}
    
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
    """Match RSHD with DAC item-level favorites and create notifications
    
    Enhanced Matching Logic with Geographic Filtering (V1.0):
    1. GEOGRAPHIC FILTER: Query DRLPDAC-List to get DACs who consider this DRLP local
    2. PREFERENCE FILTER: Check if RSHD matches DAC's DACFI-List (favorite_items)
    3. Brand-specific favorites require brand + generic match
    4. Generic favorites match any brand
    5. STOP after first match per DAC (efficiency optimization)
    """
    notified_dacs = set()  # Track DACs already notified
    drlp_id = item["drlp_id"]
    
    # STEP 1: GEOGRAPHIC FILTER - Get DACs from DRLPDAC-List
    # This list contains all DACs who have this DRLP in their DACDRLP-List
    drlpdac_doc = await db.drlpdac_list.find_one({"drlp_id": drlp_id}, {"_id": 0})
    
    if not drlpdac_doc:
        logger.info(f"No DRLPDAC-List found for DRLP {drlp_id} - no DACs in geographic range")
        return
    
    eligible_dac_ids = drlpdac_doc.get("dac_ids", [])
    
    if not eligible_dac_ids:
        logger.info(f"DRLPDAC-List for DRLP {drlp_id} is empty - no DACs in geographic range")
        return
    
    logger.info(f"Found {len(eligible_dac_ids)} DACs in DRLPDAC-List for DRLP {drlp_id}")
    
    # STEP 2: PREFERENCE FILTER - Check each DAC's favorite_items
    # Only query users who are in the DRLPDAC-List (geographic filter already applied)
    users_with_item_favs = await db.users.find({
        "id": {"$in": eligible_dac_ids},
        "favorite_items": {"$exists": True, "$ne": []}
    }, {"_id": 0, "id": 1, "favorite_items": 1}).to_list(10000)
    
    item_name_lower = item["name"].lower()
    item_organic = item.get("attributes", {}).get("organic", False)
    
    for user in users_with_item_favs:
        dac_id = user["id"]
        
        # Skip if already notified (stop-after-first-hit)
        if dac_id in notified_dacs:
            continue
        
        # Check item-level favorites (DACFI-List)
        for fav_item in user.get("favorite_items", []):
            # Must match category first
            if fav_item.get("category") != item["category"]:
                continue
            
            # OPTION C (HYBRID) MATCHING LOGIC:
            # If favorite has brand specified (has_brand=True) → strict brand matching
            # If favorite has no brand (has_brand=False) → flexible generic matching
            
            has_brand = fav_item.get("has_brand", False)
            
            if has_brand:
                # STRICT BRAND MATCHING: Brand must match
                fav_brand_keywords = fav_item.get("brand_keywords", [])
                brand_match = any(
                    brand_kw in item_name_lower 
                    for brand_kw in fav_brand_keywords
                )
                
                if not brand_match:
                    continue  # Brand doesn't match, skip this favorite
                
                # Brand matches, now check generic
                generic_keywords = fav_item.get("generic_keywords", [])
                generic_match = any(
                    gen_kw in item_name_lower 
                    for gen_kw in generic_keywords
                )
                
                if not generic_match:
                    continue  # Generic doesn't match either
                
            else:
                # FLEXIBLE GENERIC MATCHING: Any brand is OK
                generic_keywords = fav_item.get("generic_keywords", [])
                generic_match = any(
                    gen_kw in item_name_lower 
                    for gen_kw in generic_keywords
                )
                
                if not generic_match:
                    continue  # Generic doesn't match
            
            # Check organic attribute if specified
            fav_organic = fav_item.get("attributes", {}).get("organic")
            if fav_organic is True and not item_organic:
                continue  # DAC wants organic only, item is not organic
            
            # Match found! Create notification and stop checking for this DAC
            await _create_notification(dac_id, item)
            notified_dacs.add(dac_id)
            logger.info(
                f"Match: RSHD '{item['name']}' matched DAC {dac_id} favorite "
                f"'{fav_item.get('item_name')}' (brand_match: {has_brand})"
            )
            break  # STOP after first match for this DAC
    
    logger.info(f"Notification matching complete: {len(notified_dacs)} DACs notified for RSHD '{item['name']}'")

async def _create_notification(dac_id: str, item: Dict):
    """Helper to create a single notification"""
    notification = {
        "id": str(uuid.uuid4()),
        "dac_id": dac_id,
        "rshd_id": item["id"],
        "message": f"New deal on {item['name']} - {item['consumer_discount_percent']}% off at {item['drlp_name']}!",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    logger.info(f"Created notification for DAC {dac_id} for RSHD {item['id']} ({item['name']})")

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

# ===== ITEM-LEVEL FAVORITES ROUTES (Enhanced DACFI-List) =====

@api_router.post("/favorites/items")
async def add_favorite_item(item_data: FavoriteItemCreate, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can add favorite items")
    
    from categorization_service import categorize_item
    
    # Categorize item with brand/generic parsing
    category, keywords, attributes, brand_info = await categorize_item(item_data.item_name)
    
    # Check if item already exists in favorites
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "favorite_items": 1})
    existing_items = user.get("favorite_items", [])
    
    for existing_item in existing_items:
        if existing_item["item_name"].lower() == item_data.item_name.lower():
            raise HTTPException(status_code=400, detail="Item already in favorites")
    
    # Create favorite item with brand/generic structure
    favorite_item = {
        "item_name": item_data.item_name,
        "brand": brand_info.get("brand"),
        "generic": brand_info.get("generic"),
        "has_brand": brand_info.get("has_brand", False),
        "category": category,
        "keywords": keywords,
        "brand_keywords": brand_info.get("brand_keywords", []),
        "generic_keywords": brand_info.get("generic_keywords", []),
        "attributes": attributes,
        "auto_added_date": None  # Explicit addition
    }
    
    # Add to user's favorite_items
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$push": {"favorite_items": favorite_item}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to add favorite item")
    
    logger.info(
        f"Added favorite item '{item_data.item_name}' "
        f"(brand: {brand_info.get('brand')}, generic: {brand_info.get('generic')}, "
        f"category: {category}) for user {current_user['id']}"
    )
    
    return {
        "message": "Favorite item added",
        "item": favorite_item
    }

@api_router.get("/favorites/items")
async def get_favorite_items(current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can view favorite items")
    
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "favorite_items": 1})
    
    favorite_items = user.get("favorite_items", [])
    
    # Organize by category
    organized = {}
    for item in favorite_items:
        category = item.get("category", "Miscellaneous")
        if category not in organized:
            organized[category] = []
        organized[category].append(item)
    
    return {
        "items_by_category": organized,
        "total_items": len(favorite_items)
    }

@api_router.post("/favorites/items/test-delete")
async def test_delete_favorite_item(item_data: FavoriteItemDelete, current_user: Dict = Depends(get_current_user)):
    print(f"TEST DELETE: Received request to delete '{item_data.item_name}' for user {current_user['id']}")
    return {"message": f"Test delete for {item_data.item_name}"}

@api_router.delete("/favorites/items/remove")
async def remove_favorite_item(item_name: str, current_user: Dict = Depends(get_current_user)):
    print(f"REMOVE FUNCTION CALLED: item_name='{item_name}', user_role='{current_user['role']}'")
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can remove favorite items")
    
    # Remove item from user's favorite_items (exact match)
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$pull": {"favorite_items": {"item_name": item_name}}}
    )
    
    print(f"REMOVE: Delete result: matched={result.matched_count}, modified={result.modified_count}")
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Favorite item not found")
    
    return {"message": "Favorite item removed"}

@api_router.post("/favorites/items/delete")
async def delete_favorite_item_post(item_data: FavoriteItemDelete, current_user: Dict = Depends(get_current_user)):
    """Delete favorite item using POST (standard approach for body-based deletion)"""
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can remove favorite items")
    
    # Remove item from user's favorite_items (case-insensitive match)
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$pull": {"favorite_items": {"item_name": {"$regex": f"^{item_data.item_name}$", "$options": "i"}}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Favorite item not found")
    
    logger.info(f"Removed favorite item '{item_data.item_name}' for user {current_user['id']}")
    
    return {"message": "Favorite item removed"}

@api_router.put("/users/settings/auto-threshold")
async def update_auto_threshold(threshold_data: AutoThresholdUpdate, current_user: Dict = Depends(get_current_user)):
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can update auto-add settings")
    
    # Validate threshold value
    if threshold_data.auto_favorite_threshold not in [0, 3, 6]:
        raise HTTPException(
            status_code=400, 
            detail="Auto-favorite threshold must be 0 (Never), 3, or 6 days"
        )
    
    # Update user's auto_favorite_threshold
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"auto_favorite_threshold": threshold_data.auto_favorite_threshold}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Note: modified_count can be 0 if the value is the same, which is OK
    
    threshold_text = {0: "Never", 3: "3 days", 6: "6 days"}
    logger.info(f"Updated auto-add threshold to '{threshold_text[threshold_data.auto_favorite_threshold]}' for user {current_user['id']}")
    
    return {
        "message": "Auto-add settings updated",
        "threshold": threshold_data.auto_favorite_threshold
    }

# ===== DACDRLP-LIST MANAGEMENT ROUTES =====

@api_router.get("/dac/retailers")
async def get_dacdrlp_list(current_user: Dict = Depends(get_current_user)):
    """Get current DAC's DACDRLP-List (retailers they receive notifications from)"""
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can view their retailer list")
    
    dacdrlp_doc = await db.dacdrlp_list.find_one({"dac_id": current_user["id"]}, {"_id": 0})
    
    if not dacdrlp_doc:
        return {
            "dac_id": current_user["id"],
            "retailers": [],
            "dacsai_rad": current_user.get("dacsai_rad", 5.0),
            "message": "No DACDRLP-List found"
        }
    
    return dacdrlp_doc

@api_router.post("/dac/retailers/add")
async def add_retailer_to_dacdrlp_list(drlp_id: str, current_user: Dict = Depends(get_current_user)):
    """Manually add a DRLP (outside DACSAI) to DAC's DACDRLP-List
    
    Bidirectional sync: Also adds DAC to that DRLP's DRLPDAC-List
    """
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can add retailers")
    
    dac_id = current_user["id"]
    
    # Get DRLP location info
    drlp_loc = await db.drlp_locations.find_one({"user_id": drlp_id}, {"_id": 0})
    if not drlp_loc:
        raise HTTPException(status_code=404, detail="DRLP not found")
    
    # Check if already in list
    dacdrlp_doc = await db.dacdrlp_list.find_one({"dac_id": dac_id})
    if dacdrlp_doc:
        existing = any(r["drlp_id"] == drlp_id and not r.get("manually_removed", False) 
                       for r in dacdrlp_doc.get("retailers", []))
        if existing:
            raise HTTPException(status_code=400, detail="DRLP already in your retailer list")
    
    # Calculate distance
    delivery_location = current_user.get("delivery_location")
    dac_coords = delivery_location.get("coordinates") if delivery_location else None
    drlp_coords = drlp_loc.get("coordinates")
    distance = 0.0
    inside_dacsai = False
    
    if dac_coords and drlp_coords:
        distance = calculate_distance_miles(dac_coords, drlp_coords)
        dacsai_rad = current_user.get("dacsai_rad", 5.0)
        inside_dacsai = distance <= dacsai_rad
    
    retailer_entry = {
        "drlp_id": drlp_id,
        "drlp_name": drlp_loc.get("name", "Unknown"),
        "drlp_location": drlp_coords,
        "distance": distance,
        "inside_dacsai": inside_dacsai,
        "manually_added": True,  # User explicitly added this DRLP
        "manually_removed": False,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add to DACDRLP-List
    await db.dacdrlp_list.update_one(
        {"dac_id": dac_id},
        {
            "$push": {"retailers": retailer_entry},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    # Bidirectional sync: Add DAC to DRLP's DRLPDAC-List
    await add_dac_to_drlpdac_list(drlp_id, dac_id)
    
    logger.info(f"DAC {dac_id} manually added DRLP {drlp_id} to DACDRLP-List")
    
    return {
        "message": "Retailer added to your list",
        "retailer": retailer_entry
    }

@api_router.delete("/dac/retailers/{drlp_id}")
async def remove_retailer_from_dacdrlp_list(drlp_id: str, current_user: Dict = Depends(get_current_user)):
    """Remove a DRLP from DAC's DACDRLP-List (stop receiving notifications)
    
    Bidirectional sync: Also removes DAC from that DRLP's DRLPDAC-List
    """
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can remove retailers")
    
    dac_id = current_user["id"]
    
    # Find the retailer in the list
    dacdrlp_doc = await db.dacdrlp_list.find_one({"dac_id": dac_id})
    if not dacdrlp_doc:
        raise HTTPException(status_code=404, detail="DACDRLP-List not found")
    
    retailer_found = None
    for r in dacdrlp_doc.get("retailers", []):
        if r["drlp_id"] == drlp_id and not r.get("manually_removed", False):
            retailer_found = r
            break
    
    if not retailer_found:
        raise HTTPException(status_code=404, detail="DRLP not found in your retailer list")
    
    # Mark as manually_removed (preserve record for override tracking)
    await db.dacdrlp_list.update_one(
        {"dac_id": dac_id, "retailers.drlp_id": drlp_id},
        {
            "$set": {
                "retailers.$.manually_removed": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Bidirectional sync: Remove DAC from DRLP's DRLPDAC-List
    await remove_dac_from_drlpdac_list(drlp_id, dac_id)
    
    logger.info(f"DAC {dac_id} removed DRLP {drlp_id} from DACDRLP-List")
    
    return {"message": "Retailer removed from your list. You will no longer receive notifications from this store."}

class DeliveryLocationUpdate(BaseModel):
    address: str
    coordinates: Dict[str, float]  # {lat, lng}

class DacsaiUpdate(BaseModel):
    delivery_location: Optional[DeliveryLocationUpdate] = None
    dacsai_rad: Optional[float] = None

@api_router.put("/dac/location")
async def update_dac_location(location_data: DeliveryLocationUpdate, current_user: Dict = Depends(get_current_user)):
    """Update DAC's delivery location (DACSAI center)"""
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can update delivery location")
    
    dac_id = current_user["id"]
    
    # Update user's delivery location
    await db.users.update_one(
        {"id": dac_id},
        {"$set": {"delivery_location": location_data.model_dump()}}
    )
    
    logger.info(f"Updated delivery location for DAC {dac_id}")
    return {"message": "Delivery location updated", "delivery_location": location_data.model_dump()}

@api_router.put("/dac/dacsai")
async def update_dacsai(dacsai_rad: float, delivery_location: Optional[DeliveryLocationUpdate] = None, current_user: Dict = Depends(get_current_user)):
    """Update DAC's DACSAI-Rad (shopping area radius) and optionally delivery location
    
    Recalculates which DRLPs are inside DACSAI and updates DACDRLP-List accordingly.
    Preserves manual overrides (manually_added and manually_removed flags).
    """
    if current_user["role"] != "DAC":
        raise HTTPException(status_code=403, detail="Only DAC users can update DACSAI")
    
    # Validate radius
    if not (0.1 <= dacsai_rad <= 9.9):
        raise HTTPException(status_code=400, detail="DACSAI-Rad must be between 0.1 and 9.9 miles")
    
    dac_id = current_user["id"]
    
    # If delivery location is provided, update it first
    if delivery_location:
        await db.users.update_one(
            {"id": dac_id},
            {"$set": {"delivery_location": delivery_location.model_dump()}}
        )
        dac_coords = delivery_location.coordinates
    else:
        existing_location = current_user.get("delivery_location")
        dac_coords = existing_location.get("coordinates") if existing_location else None
    
    if not dac_coords:
        raise HTTPException(status_code=400, detail="Delivery location not set. Please provide delivery_location or update your profile first.")
    
    # Update user's dacsai_rad
    await db.users.update_one(
        {"id": dac_id},
        {"$set": {"dacsai_rad": dacsai_rad}}
    )
    
    # Get current DACDRLP-List
    dacdrlp_doc = await db.dacdrlp_list.find_one({"dac_id": dac_id})
    current_retailers = dacdrlp_doc.get("retailers", []) if dacdrlp_doc else []
    
    # Track manual overrides
    manually_added = {r["drlp_id"]: r for r in current_retailers if r.get("manually_added")}
    manually_removed = {r["drlp_id"] for r in current_retailers if r.get("manually_removed")}
    
    # Recalculate which DRLPs are inside new DACSAI
    all_drlp_locations = await db.drlp_locations.find({}, {"_id": 0}).to_list(10000)
    new_retailers = []
    new_dac_ids_for_drlps = {}  # Track which DRLP's DRLPDAC-Lists need updating
    
    for drlp_loc in all_drlp_locations:
        drlp_id = drlp_loc["user_id"]
        drlp_coords = drlp_loc.get("coordinates")
        
        if not drlp_coords:
            continue
        
        distance = calculate_distance_miles(dac_coords, drlp_coords)
        inside_dacsai = distance <= dacsai_rad
        
        # Skip if manually removed (DAC doesn't want notifications)
        if drlp_id in manually_removed:
            continue
        
        # Check if should be in list
        if inside_dacsai or drlp_id in manually_added:
            new_retailers.append({
                "drlp_id": drlp_id,
                "drlp_name": drlp_loc.get("name", "Unknown"),
                "drlp_location": drlp_coords,
                "distance": distance,
                "inside_dacsai": inside_dacsai,
                "manually_added": drlp_id in manually_added,
                "manually_removed": False,
                "added_at": manually_added.get(drlp_id, {}).get("added_at", datetime.now(timezone.utc).isoformat())
            })
            new_dac_ids_for_drlps[drlp_id] = True
    
    # Update DACDRLP-List
    await db.dacdrlp_list.update_one(
        {"dac_id": dac_id},
        {
            "$set": {
                "retailers": new_retailers,
                "dacsai_rad": dacsai_rad,
                "dacsai_center": dac_coords,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Update DRLPDAC-Lists (bidirectional sync)
    # First, remove DAC from all DRLPDAC-Lists
    await db.drlpdac_list.update_many(
        {},
        {"$pull": {"dac_ids": dac_id}}
    )
    
    # Then add DAC to relevant DRLPDAC-Lists
    for drlp_id in new_dac_ids_for_drlps:
        await add_dac_to_drlpdac_list(drlp_id, dac_id)
    
    logger.info(f"Updated DACSAI for DAC {dac_id}: radius={dacsai_rad}, {len(new_retailers)} retailers in list")
    
    return {
        "message": "DACSAI updated",
        "dacsai_rad": dacsai_rad,
        "retailers_count": len(new_retailers)
    }

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

# Initialize scheduler on startup
@app.on_event("startup")
async def startup_event():
    from scheduler_service import start_scheduler
    logger.info("Starting application...")
    scheduler = start_scheduler(db)
    logger.info("Scheduler initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
