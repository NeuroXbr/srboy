from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pymongo import MongoClient
from typing import Optional, List
import os
import uuid
from datetime import datetime, timedelta
import jwt
import random
from geopy.distance import geodesic
import asyncio
from security_algorithms import analyze_motoboy_security, optimize_delivery_routes, predict_demand_for_city, moderate_chat_message

# Admin Dashboard specific imports
from datetime import timedelta

app = FastAPI(title="SrBoy Delivery API", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.srboy_db

# Collections
users_collection = db.users
deliveries_collection = db.deliveries
delivery_receipts_collection = db.delivery_receipts
chats_collection = db.chats
rankings_collection = db.rankings
profiles_collection = db.profiles
posts_collection = db.posts
stories_collection = db.stories
follows_collection = db.follows

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'srboy-secret-key-2024')

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    user_type: str  # 'motoboy', 'lojista', 'admin'
    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Motoboy specific fields
    cnh: Optional[str] = None
    moto_photo_url: Optional[str] = None
    moto_model: Optional[str] = None
    moto_color: Optional[str] = None
    license_plate: Optional[str] = None
    base_city: Optional[str] = None
    bank_details: Optional[dict] = None
    device_info: Optional[dict] = None  # IMEI, MAC Address for security
    ranking_score: Optional[int] = Field(default=100)
    total_deliveries: Optional[int] = Field(default=0)
    success_rate: Optional[float] = Field(default=0.0)
    is_available: Optional[bool] = Field(default=True)
    current_location: Optional[dict] = None  # {lat, lng}
    wallet_balance: Optional[float] = Field(default=0.0)
    
    # Lojista specific fields
    fantasy_name: Optional[str] = None
    cnpj: Optional[str] = None
    address: Optional[dict] = None
    category: Optional[str] = None
    business_hours: Optional[dict] = None
    loja_wallet_balance: Optional[float] = Field(default=150.0)  # Increased initial balance

class Delivery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lojista_id: str
    motoboy_id: Optional[str] = None
    pickup_address: dict
    delivery_address: dict
    recipient_info: dict  # Nome completo, RG, autorizado alternativo
    distance_km: float
    base_price: float = Field(default=10.00)  # Updated to R$ 10,00
    additional_price: float = Field(default=0.0)  # R$ 2,00 per km
    platform_fee: float = Field(default=2.00)  # Fixed R$ 2,00 fee
    waiting_fee: float = Field(default=0.0)  # R$ 1,00 per minute after 10 min
    total_price: float
    motoboy_earnings: float = Field(default=0.0)  # New calculation logic
    status: str = Field(default="pending")  # pending, matched, pickup_confirmed, in_transit, waiting, delivered, cancelled
    created_at: datetime = Field(default_factory=datetime.now)
    matched_at: Optional[datetime] = None
    pickup_confirmed_at: Optional[datetime] = None
    delivery_started_at: Optional[datetime] = None
    waiting_started_at: Optional[datetime] = None
    waiting_minutes: Optional[int] = Field(default=0)
    delivered_at: Optional[datetime] = None
    description: Optional[str] = None
    priority_score: Optional[int] = Field(default=0)
    product_description: Optional[str] = None
    
    # PIN Security System
    pin_completo: Optional[str] = None  # 8 digits alphanumeric code
    pin_confirmacao: Optional[str] = None  # Last 4 digits for confirmation
    pin_tentativas: int = 0  # Number of PIN attempts
    pin_bloqueado: bool = False  # PIN blocked after 3 attempts

class DeliveryReceipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    delivery_id: str
    loja_id: str
    motoboy_id: str
    loja_name: str
    motoboy_name: str
    motoboy_info: dict  # Name, moto details, plate
    recipient_info: dict  # Name, RG
    product_description: str
    pickup_confirmed_at: datetime
    delivered_at: datetime
    pickup_address: dict
    delivery_address: dict
    distance_km: float
    base_price: float
    additional_price: float
    waiting_fee: float
    platform_fee: float
    total_price: float
    motoboy_earnings: float
    created_at: datetime = Field(default_factory=datetime.now)

class CreateDelivery(BaseModel):
    pickup_address: dict
    delivery_address: dict
    recipient_info: dict  # {name, rg, alternative_recipient?}
    description: Optional[str] = None
    product_description: Optional[str] = None

class WaitingUpdate(BaseModel):
    waiting_minutes: int
    reason: Optional[str] = None

class Profile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    bio: str = Field(max_length=300)
    profile_photo: Optional[str] = None  # base64 encoded
    cover_photo: Optional[str] = None    # base64 encoded
    gallery_photos: List[str] = Field(default_factory=list, max_items=2)  # max 2 additional photos
    followers_count: int = Field(default=0)
    following_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str = Field(max_length=500)
    image: Optional[str] = None  # base64 encoded
    likes_count: int = Field(default=0)
    comments_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)

class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: Optional[str] = Field(max_length=200)
    image: Optional[str] = None  # base64 encoded
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=24))

class Follow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    follower_id: str  # user who follows
    followed_id: str  # user being followed
    created_at: datetime = Field(default_factory=datetime.now)

# ============================================
# E-COMMERCE & MARKETPLACE MODELS (FUTURE USE)
# ============================================

class Product(BaseModel):
    """E-commerce product model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lojista_id: str  # Store owner
    name: str = Field(max_length=200)
    description: str = Field(max_length=1000)
    price: float = Field(gt=0)
    original_price: Optional[float] = None  # For discounts
    category_id: str
    subcategory_id: Optional[str] = None
    
    # Inventory Management
    stock_quantity: int = Field(default=0)
    low_stock_threshold: int = Field(default=5)
    is_active: bool = Field(default=True)
    
    # E-commerce Features
    images: List[str] = Field(default_factory=list, max_items=10)  # base64 images
    tags: List[str] = Field(default_factory=list)
    sku: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None  # kg
    dimensions: Optional[dict] = None  # {"width": 0, "height": 0, "depth": 0}
    
    # SEO & Marketing
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    featured: bool = Field(default=False)
    promotion_active: bool = Field(default=False)
    promotion_start: Optional[datetime] = None
    promotion_end: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProductCategory(BaseModel):
    """Product category model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[str] = None  # For subcategories
    image: Optional[str] = None  # base64 encoded
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)

class ShoppingCart(BaseModel):
    """Shopping cart model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: Optional[str] = None  # For anonymous users
    status: str = Field(default="active")  # active, abandoned, converted
    
    # Cart Analytics
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    abandoned_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None

class CartItem(BaseModel):
    """Shopping cart item model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cart_id: str
    product_id: str
    quantity: int = Field(gt=0, le=100)
    unit_price: float = Field(gt=0)
    total_price: float = Field(gt=0)
    
    # Product snapshot (in case product changes)
    product_name: str
    product_image: Optional[str] = None
    
    added_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class EcommerceOrder(BaseModel):
    """E-commerce order model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lojista_id: str
    cart_id: str
    
    # Order Details
    order_number: str = Field(default_factory=lambda: f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}")
    status: str = Field(default="pending")  # pending, confirmed, preparing, ready_for_delivery, in_transit, delivered, cancelled
    
    # Items & Pricing
    items_total: float = Field(gt=0)
    delivery_fee: float = Field(default=0)
    service_fee: float = Field(default=0)
    discount_amount: float = Field(default=0)
    tax_amount: float = Field(default=0)
    total_amount: float = Field(gt=0)
    
    # Delivery Information
    delivery_type: str = Field(default="delivery")  # delivery, pickup
    delivery_address: dict
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    
    # Payment Information
    payment_method: str  # stripe_card, stripe_pix, wallet
    payment_status: str = Field(default="pending")  # pending, paid, failed, refunded
    stripe_payment_intent_id: Optional[str] = None
    
    # Special Instructions
    notes: Optional[str] = Field(max_length=500)
    special_instructions: Optional[str] = Field(max_length=300)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

class FastFoodMenu(BaseModel):
    """Fast food menu model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    restaurant_id: str  # lojista_id
    name: str = Field(max_length=100)
    description: Optional[str] = Field(max_length=500)
    
    # Menu Configuration
    is_active: bool = Field(default=True)
    availability_start: Optional[str] = None  # "08:00"
    availability_end: Optional[str] = None    # "22:00"
    days_available: List[str] = Field(default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
    
    created_at: datetime = Field(default_factory=datetime.now)

class FastFoodItem(BaseModel):
    """Fast food item model - READY FOR FUTURE USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    menu_id: str
    restaurant_id: str
    
    # Item Details
    name: str = Field(max_length=150)
    description: str = Field(max_length=500)
    price: float = Field(gt=0)
    category: str  # appetizer, main_course, dessert, beverage
    
    # Fast Food Specific
    preparation_time_minutes: int = Field(default=15)
    calories: Optional[int] = None
    allergens: List[str] = Field(default_factory=list)
    spice_level: int = Field(default=0, ge=0, le=5)  # 0-5 spice level
    
    # Customization Options
    customization_options: List[dict] = Field(default_factory=list)  # [{name, type, required, options}]
    size_options: List[dict] = Field(default_factory=list)  # [{size, price_modifier}]
    
    # Availability
    is_available: bool = Field(default=True)
    daily_limit: Optional[int] = None
    sold_today: int = Field(default=0)
    
    # Media
    images: List[str] = Field(default_factory=list, max_items=5)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# ============================================
# STRIPE PAYMENT MODELS (READY FOR INTEGRATION)  
# ============================================

class StripeAccount(BaseModel):
    """Stripe Connect account for lojistas and motoboys - READY FOR USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_type: str  # lojista, motoboy
    
    # Stripe Information
    stripe_account_id: Optional[str] = None
    stripe_person_id: Optional[str] = None
    account_status: str = Field(default="pending")  # pending, verified, restricted, rejected
    
    # Banking Information (encrypted)
    bank_account_verified: bool = Field(default=False)
    payout_schedule: str = Field(default="daily")  # daily, weekly, monthly
    
    # Verification Requirements
    verification_status: dict = Field(default_factory=dict)
    required_documents: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class PaymentTransaction(BaseModel):
    """Payment transaction model - READY FOR USE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Transaction Basics
    transaction_type: str  # delivery_payment, ecommerce_payment, refund, payout
    amount: float = Field(gt=0)
    currency: str = Field(default="BRL")
    status: str = Field(default="pending")  # pending, processing, succeeded, failed, cancelled
    
    # Related Entities
    user_id: str  # Payer
    recipient_id: Optional[str] = None  # For payouts
    delivery_id: Optional[str] = None
    order_id: Optional[str] = None
    
    # Stripe Information
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    stripe_transfer_id: Optional[str] = None
    payment_method_type: str  # card, pix, boleto
    
    # Fee Structure
    platform_fee: float = Field(default=0)
    stripe_fee: float = Field(default=0)
    net_amount: float = Field(gt=0)
    
    # Metadata
    metadata: dict = Field(default_factory=dict)
    failure_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

# Cities served
CITIES_SERVED = [
    "Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"
]

# Helper Functions
def calculate_delivery_price(distance_km: float) -> dict:
    """Calculate delivery pricing with new SrBoy rules"""
    base_price = 10.00  # R$ 10,00 base
    additional_price = 0.0
    platform_fee = 2.00  # Fixed platform fee
    
    if distance_km <= 4:
        # Up to 4km: R$ 10,00 base, motoboy gets R$ 8,00 (R$ 10 - R$ 2 fee)
        total_price = base_price
        motoboy_earnings = base_price - platform_fee  # R$ 8,00
    else:
        # Above 4km: R$ 8,00 + R$ 2,00 per km, motoboy gets full amount
        motoboy_base = 8.00
        additional_km = distance_km
        additional_price = additional_km * 2.00  # R$ 2,00 per km
        total_price = base_price + additional_price  # For lojista
        motoboy_earnings = motoboy_base + additional_price  # Motoboy gets full calculation
    
    return {
        "base_price": base_price,
        "additional_price": additional_price,
        "total_price": total_price,
        "platform_fee": platform_fee,
        "motoboy_earnings": motoboy_earnings,
        "distance_km": round(distance_km, 2)
    }

def calculate_waiting_fee(waiting_minutes: int) -> float:
    """Calculate waiting fee: R$ 1,00 per minute after 10 minutes"""
    if waiting_minutes <= 10:
        return 0.0
    return (waiting_minutes - 10) * 1.00

def calculate_distance(point1: dict, point2: dict) -> float:
    """Calculate distance between two points using geopy"""
    try:
        coords_1 = (point1['lat'], point1['lng'])
        coords_2 = (point2['lat'], point2['lng'])
        return geodesic(coords_1, coords_2).kilometers
    except:
        return 0.0

def find_best_motoboy(delivery: dict) -> Optional[dict]:
    """Intelligent matching based on ranking and proximity"""
    pickup_city = delivery['pickup_address'].get('city', '')
    
    available_motoboys = list(users_collection.find({
        "user_type": "motoboy",
        "is_available": True,
        "base_city": pickup_city
    }))
    
    if not available_motoboys:
        return None
    
    candidates = []
    for motoboy in available_motoboys:
        if not motoboy.get('current_location'):
            continue
            
        distance_to_pickup = calculate_distance(
            motoboy['current_location'], 
            delivery['pickup_address']
        )
        
        ranking_score = motoboy.get('ranking_score', 100)
        proximity_score = max(0, 100 - (distance_to_pickup * 10))
        
        weighted_score = (ranking_score * 0.7) + (proximity_score * 0.3)
        
        candidates.append({
            "motoboy": motoboy,
            "distance_to_pickup": distance_to_pickup,
            "weighted_score": weighted_score,
            "ranking_score": ranking_score
        })
    
    candidates.sort(key=lambda x: x['weighted_score'], reverse=True)
    return candidates[0] if candidates else None

def create_delivery_receipt(delivery: dict, lojista: dict, motoboy: dict) -> dict:
    """Create comprehensive delivery receipt"""
    receipt_data = DeliveryReceipt(
        delivery_id=delivery["id"],
        loja_id=delivery["lojista_id"],
        motoboy_id=delivery["motoboy_id"],
        loja_name=lojista.get("fantasy_name", lojista.get("name")),
        motoboy_name=motoboy["name"],
        motoboy_info={
            "name": motoboy["name"],
            "moto_model": motoboy.get("moto_model", "N/A"),
            "moto_color": motoboy.get("moto_color", "N/A"),
            "license_plate": motoboy.get("license_plate", "N/A")
        },
        recipient_info=delivery["recipient_info"],
        product_description=delivery.get("product_description", delivery.get("description", "N/A")),
        pickup_confirmed_at=delivery["pickup_confirmed_at"],
        delivered_at=delivery["delivered_at"],
        pickup_address=delivery["pickup_address"],
        delivery_address=delivery["delivery_address"],
        distance_km=delivery["distance_km"],
        base_price=delivery["base_price"],
        additional_price=delivery["additional_price"],
        waiting_fee=delivery["waiting_fee"],
        platform_fee=delivery["platform_fee"],
        total_price=delivery["total_price"],
        motoboy_earnings=delivery["motoboy_earnings"]
    ).dict()
    
    delivery_receipts_collection.insert_one(receipt_data)
    receipt_data.pop("_id", None)
    return receipt_data

def can_create_post_today(user_id: str) -> bool:
    """Check if user can create a post today (limit: 4 per day)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    posts_today = posts_collection.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": today, "$lt": tomorrow}
    })
    
    return posts_today < 4

def can_create_story_today(user_id: str) -> bool:
    """Check if user can create a story today (limit: 4 per day)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    stories_today = stories_collection.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": today, "$lt": tomorrow},
        "expires_at": {"$gt": datetime.now()}  # Not expired
    })
    
    return stories_today < 4

def get_user_profile(user_id: str) -> Optional[dict]:
    """Get or create user profile"""
    profile = profiles_collection.find_one({"user_id": user_id})
    
    if not profile:
        # Create default profile
        user = users_collection.find_one({"id": user_id})
        if not user:
            return None
            
        profile_data = Profile(
            user_id=user_id,
            bio="",
            followers_count=0,
            following_count=0
        ).dict()
        
        profiles_collection.insert_one(profile_data)
        profile = profile_data
        profile.pop("_id", None)
    else:
        profile.pop("_id", None)
    
    return profile

def update_follow_counts(user_id: str):
    """Update follower and following counts for a user"""
    followers_count = follows_collection.count_documents({"followed_id": user_id})
    following_count = follows_collection.count_documents({"follower_id": user_id})
    
    profiles_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "followers_count": followers_count,
            "following_count": following_count,
            "updated_at": datetime.now()
        }}
    )

def generate_delivery_pin() -> tuple:
    """Generate 8-digit alphanumeric PIN and return (full_pin, confirmation_pin)"""
    import random
    import string
    
    # Generate 8-digit alphanumeric code (letters and numbers)
    characters = string.ascii_uppercase + string.digits
    pin_completo = ''.join(random.choice(characters) for _ in range(8))
    
    # Get last 4 digits for confirmation
    pin_confirmacao = pin_completo[-4:]
    
    return pin_completo, pin_confirmacao

def validate_delivery_pin(delivery_id: str, entered_pin: str) -> dict:
    """Validate PIN for delivery confirmation"""
    delivery = deliveries_collection.find_one({"id": delivery_id})
    
    if not delivery:
        return {"success": False, "message": "Entrega não encontrada", "code": "DELIVERY_NOT_FOUND"}
    
    if delivery.get("pin_bloqueado", False):
        return {"success": False, "message": "PIN bloqueado após 3 tentativas. Entre em contato com o suporte.", "code": "PIN_BLOCKED"}
    
    if not delivery.get("pin_confirmacao"):
        return {"success": False, "message": "PIN não gerado para esta entrega", "code": "NO_PIN"}
    
    # Validate PIN
    if entered_pin.upper() == delivery["pin_confirmacao"].upper():
        # PIN correct - reset attempts and mark as successfully validated
        deliveries_collection.update_one(
            {"id": delivery_id},
            {"$set": {
                "pin_tentativas": 0,  # Reset attempts after successful validation
                "pin_validado_com_sucesso": True,  # New field to track successful validation
                "pin_validado_em": datetime.now()  # Timestamp of successful validation
            }}
        )
        return {"success": True, "message": "PIN validado com sucesso!", "code": "PIN_VALID"}
    else:
        # PIN incorrect - increment attempts
        new_attempts = delivery.get("pin_tentativas", 0) + 1
        update_data = {"pin_tentativas": new_attempts}
        
        # Block PIN after 3 attempts
        if new_attempts >= 3:
            update_data["pin_bloqueado"] = True
            
        deliveries_collection.update_one(
            {"id": delivery_id},
            {"$set": update_data}
        )
        
        if new_attempts >= 3:
            return {
                "success": False, 
                "message": "PIN bloqueado após 3 tentativas incorretas. Entre em contato com o suporte.", 
                "code": "PIN_BLOCKED",
                "attempts": new_attempts
            }
        else:
            return {
                "success": False, 
                "message": f"PIN incorreto. {3 - new_attempts} tentativas restantes.", 
                "code": "PIN_INCORRECT",
                "attempts": new_attempts,
                "remaining": 3 - new_attempts
            }

# API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "SrBoy Delivery API v2.0", "new_features": ["waiting_fees", "digital_receipts", "enhanced_pricing"]}

@app.post("/api/auth/google")
async def google_auth(auth_data: dict):
    """Google OAuth authentication with demo data"""
    email = auth_data.get('email', 'demo@srboy.com')
    name = auth_data.get('name', 'Demo User')
    user_type = auth_data.get('user_type', 'motoboy')
    
    existing_user = users_collection.find_one({"email": email})
    
    if existing_user:
        user_data = existing_user
    else:
        user_data = User(
            email=email,
            name=name,
            user_type=user_type
        ).dict()
        
        if user_type == "motoboy":
            # Demo data for motoboy
            demo_names = ["Carlos Silva", "João Santos", "Pedro Oliveira"]
            demo_cities = ["São Roque", "Mairinque", "Araçariguama"]
            demo_motos = [
                {"model": "Honda CG 160", "color": "Vermelha", "plate": "SRB-1234"},
                {"model": "Yamaha Factor 125", "color": "Azul", "plate": "SRB-5678"},
                {"model": "Honda Titan 150", "color": "Preta", "plate": "SRB-9012"}
            ]
            
            demo_index = random.randint(0, 2)
            selected_moto = demo_motos[demo_index]
            
            user_data.update({
                "name": demo_names[demo_index] if name == "Demo User" else name,
                "ranking_score": random.randint(85, 98),
                "total_deliveries": random.randint(150, 500),
                "success_rate": round(random.uniform(0.92, 0.99), 2),
                "is_available": True,
                "base_city": demo_cities[demo_index],
                "wallet_balance": round(random.uniform(250.0, 800.0), 2),
                "moto_model": selected_moto["model"],
                "moto_color": selected_moto["color"],
                "license_plate": selected_moto["plate"]
            })
            
        elif user_type == "lojista":
            # Demo data for lojista
            demo_lojas = [
                {"name": "Maria Santos", "fantasy": "Farmácia Saúde Total", "category": "Farmácia"},
                {"name": "José Silva", "fantasy": "Pizzaria Bella Vista", "category": "Restaurante"},
                {"name": "Ana Costa", "fantasy": "Boutique Elegante", "category": "Loja de Roupas"}
            ]
            
            demo_index = random.randint(0, 2)
            selected_loja = demo_lojas[demo_index]
            
            user_data.update({
                "name": selected_loja["name"] if name == "Demo User" else name,
                "loja_wallet_balance": round(random.uniform(300.0, 1200.0), 2),
                "fantasy_name": selected_loja["fantasy"],
                "category": selected_loja["category"],
                "total_deliveries": random.randint(50, 200)
            })
        
        users_collection.insert_one(user_data)
        
        # Create demo profile with sample data
        create_demo_profile(user_data)
    
    token_data = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "user_type": user_data["user_type"],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    
    token = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")
    
    return {
        "token": token,
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "user_type": user_data["user_type"],
            "ranking_score": user_data.get("ranking_score"),
            "wallet_balance": user_data.get("wallet_balance", user_data.get("loja_wallet_balance", 0)),
            "fantasy_name": user_data.get("fantasy_name"),
            "total_deliveries": user_data.get("total_deliveries", 0)
        }
    }

@app.get("/api/users/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user profile"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.pop("_id", None)
        user.pop("device_info", None)
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/deliveries")
async def create_delivery(delivery_data: CreateDelivery, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create new delivery request with enhanced SrBoy features"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        user = users_collection.find_one({"id": user_id, "user_type": "lojista"})
        if not user:
            raise HTTPException(status_code=403, detail="Only lojistas can create deliveries")
        
        distance_km = calculate_distance(
            delivery_data.pickup_address,
            delivery_data.delivery_address
        )
        
        pricing = calculate_delivery_price(distance_km)
        
        # Check wallet balance
        current_balance = user.get('loja_wallet_balance', 0)
        if current_balance < pricing['total_price']:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Necessário: R$ {pricing['total_price']:.2f}, Disponível: R$ {current_balance:.2f}")
        
        delivery = Delivery(
            lojista_id=user_id,
            pickup_address=delivery_data.pickup_address,
            delivery_address=delivery_data.delivery_address,
            recipient_info=delivery_data.recipient_info,
            distance_km=distance_km,
            additional_price=pricing['additional_price'],
            total_price=pricing['total_price'],
            motoboy_earnings=pricing['motoboy_earnings'],
            description=delivery_data.description,
            product_description=delivery_data.product_description
        ).dict()
        
        deliveries_collection.insert_one(delivery)
        delivery.pop("_id", None)
        
        best_match = find_best_motoboy(delivery)
        
        if best_match:
            # Generate PIN for security when auto-matching
            pin_completo, pin_confirmacao = generate_delivery_pin()
            
            deliveries_collection.update_one(
                {"id": delivery["id"]},
                {
                    "$set": {
                        "motoboy_id": best_match["motoboy"]["id"],
                        "status": "matched",
                        "matched_at": datetime.now(),
                        "pin_completo": pin_completo,
                        "pin_confirmacao": pin_confirmacao,
                        "pin_tentativas": 0,
                        "pin_bloqueado": False
                    }
                }
            )
            
            # Deduct from lojista wallet
            users_collection.update_one(
                {"id": user_id},
                {"$inc": {"loja_wallet_balance": -pricing['total_price']}}
            )
            
            delivery["motoboy_id"] = best_match["motoboy"]["id"]
            delivery["status"] = "matched"
            delivery["pin_confirmacao"] = pin_confirmacao
            
            return {
                "delivery": delivery,
                "matched_motoboy": {
                    "id": best_match["motoboy"]["id"],
                    "name": best_match["motoboy"]["name"],
                    "moto_info": {
                        "model": best_match["motoboy"].get("moto_model", "N/A"),
                        "color": best_match["motoboy"].get("moto_color", "N/A"),
                        "plate": best_match["motoboy"].get("license_plate", "N/A")
                    },
                    "ranking_score": best_match["ranking_score"],
                    "distance_to_pickup": round(best_match["distance_to_pickup"], 2)
                },
                "pricing": pricing,
                "pin_confirmacao": pin_confirmacao  # Return PIN for lojista display
            }
        
        return {
            "delivery": delivery,
            "pricing": pricing,
            "message": "Entrega criada, procurando motoboy disponível..."
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/deliveries/{delivery_id}/accept")
async def accept_delivery(delivery_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Motoboy accepts a delivery and generates PIN"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        motoboy_id = payload["user_id"]
        user_type = payload["user_type"]
        
        if user_type != "motoboy":
            raise HTTPException(status_code=403, detail="Only motoboys can accept deliveries")
        
        # Look for delivery that is either pending or matched to this motoboy without PIN
        delivery = deliveries_collection.find_one({
            "$or": [
                {"id": delivery_id, "status": "pending"},
                {"id": delivery_id, "status": "matched", "motoboy_id": motoboy_id, "pin_confirmacao": {"$exists": False}}
            ]
        })
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found or already assigned")
        
        motoboy = users_collection.find_one({"id": motoboy_id, "user_type": "motoboy"})
        if not motoboy:
            raise HTTPException(status_code=404, detail="Motoboy not found")
        
        # Generate PIN for security
        pin_completo, pin_confirmacao = generate_delivery_pin()
        
        # Update delivery with motoboy and PIN
        update_result = deliveries_collection.update_one(
            {
                "$or": [
                    {"id": delivery_id, "status": "pending"},
                    {"id": delivery_id, "status": "matched", "motoboy_id": motoboy_id, "pin_confirmacao": {"$exists": False}}
                ]
            },
            {
                "$set": {
                    "motoboy_id": motoboy_id,
                    "status": "matched",
                    "pin_completo": pin_completo,
                    "pin_confirmacao": pin_confirmacao,
                    "pin_tentativas": 0,
                    "pin_bloqueado": False
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Delivery was already assigned to another motoboy")
        
        # Update motoboy availability
        users_collection.update_one(
            {"id": motoboy_id},
            {"$set": {"is_available": False}}
        )
        
        return {
            "message": "Delivery accepted successfully", 
            "delivery_id": delivery_id,
            "pin_confirmacao": pin_confirmacao,  # Return PIN for lojista display
            "motoboy": {
                "name": motoboy["name"],
                "moto_model": motoboy.get("moto_model", "N/A"),
                "moto_color": motoboy.get("moto_color", "N/A"),
                "license_plate": motoboy.get("license_plate", "N/A")
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/deliveries/{delivery_id}/validate-pin")
async def validate_pin_endpoint(delivery_id: str, pin_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate PIN for delivery confirmation"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        if user_type != "motoboy":
            raise HTTPException(status_code=403, detail="Only motoboys can validate PIN")
        
        entered_pin = pin_data.get("pin", "").strip()
        if not entered_pin:
            raise HTTPException(status_code=400, detail="PIN is required")
        
        if len(entered_pin) != 4:
            raise HTTPException(status_code=400, detail="PIN must be 4 digits")
        
        # Check if delivery belongs to this motoboy
        delivery = deliveries_collection.find_one({"id": delivery_id})
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        if delivery.get("motoboy_id") != user_id:
            raise HTTPException(status_code=403, detail="You can only validate PIN for your own deliveries")
        
        # Validate PIN
        result = validate_delivery_pin(delivery_id, entered_pin)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "code": result["code"],
                "can_complete_delivery": True
            }
        else:
            return {
                "success": False,
                "message": result["message"],
                "code": result["code"],
                "attempts": result.get("attempts", 0),
                "remaining": result.get("remaining", 0),
                "can_complete_delivery": False
            }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.put("/api/deliveries/{delivery_id}/status")
async def update_delivery_status(delivery_id: str, status_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update delivery status with enhanced workflow"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        new_status = status_data.get("status")
        allowed_statuses = ["pickup_confirmed", "in_transit", "waiting", "delivered", "cancelled", "client_not_found"]
        
        if new_status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        delivery = deliveries_collection.find_one({"id": delivery_id})
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        # Check permissions
        if user_type == "motoboy" and delivery.get("motoboy_id") != user_id:
            raise HTTPException(status_code=403, detail="Not your delivery")
        
        update_data = {"status": new_status}
        current_time = datetime.now()
        
        if new_status == "pickup_confirmed":
            update_data["pickup_confirmed_at"] = current_time
        elif new_status == "in_transit":
            update_data["delivery_started_at"] = current_time
        elif new_status == "waiting":
            update_data["waiting_started_at"] = current_time
        elif new_status == "delivered":
            # Check if PIN system is active and validate it
            if delivery.get("pin_confirmacao"):
                # PIN system is active for this delivery
                if delivery.get("pin_bloqueado", False):
                    raise HTTPException(
                        status_code=400, 
                        detail="PIN bloqueado após 3 tentativas incorretas. Entre em contato com o suporte."
                    )
                
                # Check if PIN has been successfully validated
                pin_validado = delivery.get("pin_validado_com_sucesso", False)
                
                if not pin_validado:
                    raise HTTPException(
                        status_code=400, 
                        detail="PIN de confirmação deve ser validado antes de finalizar a entrega. Use o endpoint /validate-pin primeiro."
                    )
            
            update_data["delivered_at"] = current_time
            
            # Update motoboy stats and wallet
            motoboy_earnings = delivery.get("motoboy_earnings", 0) + delivery.get("waiting_fee", 0)
            users_collection.update_one(
                {"id": delivery["motoboy_id"]},
                {
                    "$inc": {
                        "total_deliveries": 1,
                        "wallet_balance": motoboy_earnings
                    }
                }
            )
            
            # Create digital receipt - handle missing timestamps gracefully
            lojista = users_collection.find_one({"id": delivery["lojista_id"]})
            motoboy = users_collection.find_one({"id": delivery["motoboy_id"]})
            if lojista and motoboy:
                try:
                    # Ensure required timestamps exist
                    delivery_copy = delivery.copy()
                    if not delivery_copy.get("pickup_confirmed_at"):
                        delivery_copy["pickup_confirmed_at"] = current_time
                    if not delivery_copy.get("delivered_at"):
                        delivery_copy["delivered_at"] = current_time
                    
                    receipt = create_delivery_receipt(delivery_copy, lojista, motoboy)
                    update_data["receipt_id"] = receipt["id"]
                except Exception as e:
                    # If receipt creation fails, log but don't block delivery completion
                    print(f"Warning: Failed to create receipt for delivery {delivery_id}: {str(e)}")
                    update_data["receipt_error"] = str(e)
        
        deliveries_collection.update_one(
            {"id": delivery_id},
            {"$set": update_data}
        )
        
        return {"message": f"Status atualizado para: {new_status}"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.put("/api/deliveries/{delivery_id}/waiting")
async def update_waiting_time(delivery_id: str, waiting_data: WaitingUpdate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update waiting time and calculate additional fees"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        if user_type != "motoboy":
            raise HTTPException(status_code=403, detail="Only motoboys can update waiting time")
        
        delivery = deliveries_collection.find_one({"id": delivery_id})
        if not delivery or delivery.get("motoboy_id") != user_id:
            raise HTTPException(status_code=403, detail="Delivery not found or not yours")
        
        waiting_fee = calculate_waiting_fee(waiting_data.waiting_minutes)
        new_total = delivery["total_price"] + waiting_fee
        new_motoboy_earnings = delivery["motoboy_earnings"] + waiting_fee
        
        deliveries_collection.update_one(
            {"id": delivery_id},
            {
                "$set": {
                    "waiting_minutes": waiting_data.waiting_minutes,
                    "waiting_fee": waiting_fee,
                    "total_price": new_total,
                    "motoboy_earnings": new_motoboy_earnings
                }
            }
        )
        
        # Update lojista balance for additional waiting fee
        if waiting_fee > 0:
            users_collection.update_one(
                {"id": delivery["lojista_id"]},
                {"$inc": {"loja_wallet_balance": -waiting_fee}}
            )
        
        return {
            "message": "Tempo de espera atualizado",
            "waiting_minutes": waiting_data.waiting_minutes,
            "waiting_fee": waiting_fee,
            "new_total": new_total
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/deliveries")
async def get_deliveries(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get deliveries based on user type"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        if user_type == "lojista":
            query = {"lojista_id": user_id}
        elif user_type == "motoboy":
            query = {"motoboy_id": user_id}
        else:
            query = {}
        
        deliveries = list(deliveries_collection.find(query).sort("created_at", -1).limit(50))
        
        for delivery in deliveries:
            delivery.pop("_id", None)
        
        return {"deliveries": deliveries}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/deliveries/{delivery_id}/receipt")
async def get_delivery_receipt(delivery_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get digital delivery receipt"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        receipt = delivery_receipts_collection.find_one({"delivery_id": delivery_id})
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt.pop("_id", None)
        return {"receipt": receipt}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/cities")
async def get_cities():
    """Get list of served cities"""
    return {"cities": CITIES_SERVED}

@app.get("/api/pricing/calculate")
async def calculate_pricing(distance: float):
    """Calculate delivery pricing with new SrBoy rules"""
    if distance <= 0:
        raise HTTPException(status_code=400, detail="Invalid distance")
    
    pricing = calculate_delivery_price(distance)
    return pricing

@app.put("/api/motoboy/location")
async def update_location(location_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update motoboy current location"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        if user_type != "motoboy":
            raise HTTPException(status_code=403, detail="Only motoboys can update location")
        
        lat = location_data.get("lat")
        lng = location_data.get("lng")
        
        if not lat or not lng:
            raise HTTPException(status_code=400, detail="Invalid location data")
        
        users_collection.update_one(
            {"id": user_id},
            {"$set": {"current_location": {"lat": lat, "lng": lng}}}
        )
        
        return {"message": "Location updated successfully"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/rankings")
async def get_rankings(city: Optional[str] = None):
    """Get motoboy rankings"""
    query = {"user_type": "motoboy"}
    if city:
        query["base_city"] = city
    
    motoboys = list(users_collection.find(query).sort("ranking_score", -1).limit(20))
    
    rankings = []
    for i, motoboy in enumerate(motoboys, 1):
        rankings.append({
            "position": i,
            "id": motoboy["id"],
            "name": motoboy["name"],
            "ranking_score": motoboy.get("ranking_score", 100),
            "total_deliveries": motoboy.get("total_deliveries", 0),
            "success_rate": motoboy.get("success_rate", 0.0),
            "base_city": motoboy.get("base_city", ""),
            "wallet_balance": motoboy.get("wallet_balance", 0.0)
        })
    
    return {"rankings": rankings}

# Social Profile Endpoints
@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user profile with social features"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Get user basic info
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get profile info
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check if current user is following this user
        current_user_id = payload["user_id"]
        is_following = follows_collection.find_one({
            "follower_id": current_user_id,
            "followed_id": user_id
        }) is not None
        
        # Get user's ranking score (star rating)
        ranking_score = user.get("ranking_score", 100)
        star_rating = min(5, max(1, ranking_score // 20))  # Convert 0-100 to 1-5 stars
        
        # Get recent posts
        recent_posts = list(posts_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(6))
        
        for post in recent_posts:
            post.pop("_id", None)
        
        # Get active stories (not expired)
        active_stories = list(stories_collection.find({
            "user_id": user_id,
            "expires_at": {"$gt": datetime.now()}
        }).sort("created_at", -1))
        
        for story in active_stories:
            story.pop("_id", None)
        
        user.pop("_id", None)
        
        return {
            "user": {
                "id": user["id"],
                "name": user["name"],
                "user_type": user["user_type"],
                "fantasy_name": user.get("fantasy_name"),
                "base_city": user.get("base_city"),
                "star_rating": star_rating,
                "ranking_score": ranking_score,
                "total_deliveries": user.get("total_deliveries", 0)
            },
            "profile": profile,
            "is_following": is_following,
            "recent_posts": recent_posts,
            "active_stories": active_stories
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.put("/api/profile")
async def update_profile(profile_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update user profile"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        # Validate bio length
        bio = profile_data.get("bio", "")
        if len(bio) > 300:
            raise HTTPException(status_code=400, detail="Bio cannot exceed 300 characters")
        
        # Validate gallery photos (max 2)
        gallery_photos = profile_data.get("gallery_photos", [])
        if len(gallery_photos) > 2:
            raise HTTPException(status_code=400, detail="Maximum 2 gallery photos allowed")
        
        update_data = {
            "bio": bio,
            "updated_at": datetime.now()
        }
        
        # Update photos if provided
        if "profile_photo" in profile_data:
            update_data["profile_photo"] = profile_data["profile_photo"]
        
        if "cover_photo" in profile_data:
            update_data["cover_photo"] = profile_data["cover_photo"]
        
        if "gallery_photos" in profile_data:
            update_data["gallery_photos"] = gallery_photos
        
        # Get or create profile
        existing_profile = get_user_profile(user_id)
        
        profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {"message": "Profile updated successfully"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/follow/{user_id}")
async def follow_user(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Follow a user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        follower_id = payload["user_id"]
        
        if follower_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        # Check if user exists
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already following
        existing_follow = follows_collection.find_one({
            "follower_id": follower_id,
            "followed_id": user_id
        })
        
        if existing_follow:
            raise HTTPException(status_code=400, detail="Already following this user")
        
        # Create follow relationship
        follow_data = Follow(
            follower_id=follower_id,
            followed_id=user_id
        ).dict()
        
        follows_collection.insert_one(follow_data)
        
        # Update follow counts
        update_follow_counts(follower_id)
        update_follow_counts(user_id)
        
        return {"message": "User followed successfully"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.delete("/api/follow/{user_id}")
async def unfollow_user(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Unfollow a user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        follower_id = payload["user_id"]
        
        # Remove follow relationship
        result = follows_collection.delete_one({
            "follower_id": follower_id,
            "followed_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Not following this user")
        
        # Update follow counts
        update_follow_counts(follower_id)
        update_follow_counts(user_id)
        
        return {"message": "User unfollowed successfully"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/posts")
async def create_post(post_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a new post (limit: 4 per day)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        # Check daily limit
        if not can_create_post_today(user_id):
            raise HTTPException(status_code=400, detail="Daily post limit reached (4 posts per day)")
        
        # Validate content length
        content = post_data.get("content", "")
        if len(content) > 500:
            raise HTTPException(status_code=400, detail="Post content cannot exceed 500 characters")
        
        if not content and not post_data.get("image"):
            raise HTTPException(status_code=400, detail="Post must contain either content or image")
        
        # Create post
        post = Post(
            user_id=user_id,
            content=content,
            image=post_data.get("image")
        ).dict()
        
        posts_collection.insert_one(post)
        post.pop("_id", None)
        
        return {"message": "Post created successfully", "post": post}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/stories")
async def create_story(story_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a new story (limit: 4 per day, expires in 24h)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        # Check daily limit
        if not can_create_story_today(user_id):
            raise HTTPException(status_code=400, detail="Daily story limit reached (4 stories per day)")
        
        # Validate content
        content = story_data.get("content", "")
        if len(content) > 200:
            raise HTTPException(status_code=400, detail="Story content cannot exceed 200 characters")
        
        if not content and not story_data.get("image"):
            raise HTTPException(status_code=400, detail="Story must contain either content or image")
        
        # Create story
        story = Story(
            user_id=user_id,
            content=content,
            image=story_data.get("image")
        ).dict()
        
        stories_collection.insert_one(story)
        story.pop("_id", None)
        
        return {"message": "Story created successfully", "story": story}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/feed/posts")
async def get_posts_feed(page: int = 1, limit: int = 20, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get posts feed from followed users"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        # Get followed users
        followed_users = list(follows_collection.find(
            {"follower_id": user_id}
        ).limit(1000))  # Reasonable limit
        
        followed_ids = [follow["followed_id"] for follow in followed_users]
        followed_ids.append(user_id)  # Include own posts
        
        skip = (page - 1) * limit
        
        # Get posts from followed users
        posts = list(posts_collection.find(
            {"user_id": {"$in": followed_ids}}
        ).sort("created_at", -1).skip(skip).limit(limit))
        
        # Enrich posts with user information
        enriched_posts = []
        for post in posts:
            post.pop("_id", None)
            
            # Get post author info
            author = users_collection.find_one({"id": post["user_id"]})
            if author:
                post["author"] = {
                    "id": author["id"],
                    "name": author["name"],
                    "user_type": author["user_type"],
                    "fantasy_name": author.get("fantasy_name")
                }
                
                # Get author's profile photo
                profile = profiles_collection.find_one({"user_id": post["user_id"]})
                if profile:
                    post["author"]["profile_photo"] = profile.get("profile_photo")
            
            enriched_posts.append(post)
        
        return {"posts": enriched_posts}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/feed/stories")
async def get_stories_feed(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get stories feed from followed users (only non-expired)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        # Get followed users
        followed_users = list(follows_collection.find(
            {"follower_id": user_id}
        ).limit(1000))
        
        followed_ids = [follow["followed_id"] for follow in followed_users]
        followed_ids.append(user_id)  # Include own stories
        
        # Get non-expired stories from followed users
        stories = list(stories_collection.find({
            "user_id": {"$in": followed_ids},
            "expires_at": {"$gt": datetime.now()}
        }).sort("created_at", -1).limit(50))
        
        # Enrich stories with user information
        enriched_stories = []
        for story in stories:
            story.pop("_id", None)
            
            # Get story author info
            author = users_collection.find_one({"id": story["user_id"]})
            if author:
                story["author"] = {
                    "id": author["id"],
                    "name": author["name"],
                    "user_type": author["user_type"],
                    "fantasy_name": author.get("fantasy_name")
                }
                
                # Get author's profile photo
                profile = profiles_collection.find_one({"user_id": story["user_id"]})
                if profile:
                    story["author"]["profile_photo"] = profile.get("profile_photo")
            
            enriched_stories.append(story)
        
        return {"stories": enriched_stories}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Security & Analysis Endpoints
@app.get("/api/security/analyze/{motoboy_id}")
async def analyze_motoboy_security_endpoint(motoboy_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Analyze motoboy security (admin only)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_type = payload["user_type"]
        
        if user_type != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get motoboy data
        motoboy = users_collection.find_one({"id": motoboy_id, "user_type": "motoboy"})
        if not motoboy:
            raise HTTPException(status_code=404, detail="Motoboy not found")
        
        # Clean up the data and ensure proper format
        motoboy.pop("_id", None)
        
        # Get delivery history
        deliveries = list(deliveries_collection.find({"motoboy_id": motoboy_id}).sort("created_at", -1).limit(100))
        for delivery in deliveries:
            delivery.pop("_id", None)
            # Convert datetime objects to strings for analysis
            if isinstance(delivery.get("created_at"), datetime):
                delivery["created_at"] = delivery["created_at"].isoformat()
            if isinstance(delivery.get("pickup_confirmed_at"), datetime):
                delivery["pickup_confirmed_at"] = delivery["pickup_confirmed_at"].isoformat()
            if isinstance(delivery.get("delivered_at"), datetime):
                delivery["delivered_at"] = delivery["delivered_at"].isoformat()
        
        motoboy["delivery_history"] = deliveries
        
        # Add mock location history if not present (for demo purposes)
        if "location_history" not in motoboy or not motoboy["location_history"]:
            motoboy["location_history"] = [
                {"lat": -23.5320, "lng": -47.1360, "timestamp": datetime.now().isoformat()},
                {"lat": -23.5330, "lng": -47.1370, "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()},
                {"lat": -23.5340, "lng": -47.1380, "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()}
            ]
        
        # Convert user creation date to string if it's datetime
        if isinstance(motoboy.get("created_at"), datetime):
            motoboy["created_at"] = motoboy["created_at"].isoformat()
        
        try:
            # Analyze security
            analysis = analyze_motoboy_security(motoboy)
            return {"analysis": analysis}
        except Exception as analysis_error:
            # Return a simplified analysis if the full analysis fails
            return {
                "analysis": {
                    "motoboy_id": motoboy_id,
                    "risk_score": 25.0,
                    "risk_level": "low",
                    "risk_factors": [],
                    "analysis_timestamp": datetime.now().isoformat(),
                    "requires_manual_review": False,
                    "recommended_actions": ["Continue monitoring"],
                    "error": f"Analysis simplified due to: {str(analysis_error)}"
                }
            }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/api/demand/predict/{city}")
async def predict_demand_endpoint(city: str):
    """Predict demand for a city"""
    if city not in CITIES_SERVED:
        raise HTTPException(status_code=400, detail="City not served")
    
    prediction = predict_demand_for_city(city)
    return {"prediction": prediction}

@app.post("/api/routes/optimize")
async def optimize_routes_endpoint(route_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optimize delivery routes for motoboy"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        if user_type != "motoboy":
            raise HTTPException(status_code=403, detail="Only motoboys can optimize routes")
        
        # Get motoboy location
        motoboy = users_collection.find_one({"id": user_id})
        if not motoboy or not motoboy.get("current_location"):
            raise HTTPException(status_code=400, detail="Location required for route optimization")
        
        # Get assigned deliveries
        deliveries = list(deliveries_collection.find({
            "motoboy_id": user_id,
            "status": {"$in": ["matched", "pickup_confirmed"]}
        }))
        
        for delivery in deliveries:
            delivery.pop("_id", None)
        
        if not deliveries:
            return {"message": "No deliveries to optimize", "optimized_route": []}
        
        optimization = optimize_delivery_routes(deliveries, motoboy["current_location"])
        return {"optimization": optimization}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/chat/moderate")
async def moderate_chat_endpoint(message_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Moderate chat message"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        message = message_data.get("message", "")
        city = message_data.get("city", "")
        
        if not message or not city:
            raise HTTPException(status_code=400, detail="Message and city required")
        
        moderation = moderate_chat_message(message, user_id, city)
        
        # Store moderated message if approved
        if moderation["action"] in ["approved", "filtered"]:
            chat_message = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "city": city,
                "message": moderation["filtered_message"],
                "original_message": message,
                "moderation_flags": moderation["flags"],
                "created_at": datetime.now()
            }
            chats_collection.insert_one(chat_message)
        
        return {"moderation": moderation}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_demo_profile(user_data):
    """Create demo profile with sample posts and stories"""
    import random
    
    user_id = user_data["id"]
    user_type = user_data["user_type"]
    name = user_data["name"]
    
    # Create profile
    if user_type == "motoboy":
        bio = f"🏍️ Motoboy experiente em {user_data.get('base_city', 'São Roque')}! Sempre pontual e cuidadoso com as entregas. {user_data.get('total_deliveries', 0)}+ entregas realizadas com sucesso! ⭐ Avaliação média: {user_data.get('ranking_score', 100)/20:.1f}/5"
    else:
        bio = f"🏪 {user_data.get('fantasy_name', 'Loja')} - {user_data.get('category', 'Comércio')} de qualidade! Atendemos toda região com produtos selecionados. Parceiros SrBoy desde 2024! 📦 {user_data.get('total_deliveries', 0)}+ pedidos entregues!"
    
    profile_data = Profile(
        user_id=user_id,
        bio=bio,
        followers_count=random.randint(15, 85),
        following_count=random.randint(10, 45)
    ).dict()
    
    profiles_collection.insert_one(profile_data)
    
    # Create sample posts
    sample_posts = []
    if user_type == "motoboy":
        sample_posts = [
            "Mais um dia de trabalho! Acabei de finalizar uma entrega em Mairinque. Cliente super educado! 🏍️✨",
            "Pessoal, cuidado na Rua das Flores - tem obras na pista. Trânsito um pouco lento por lá! 🚧",
            "Entrega especial hoje: um bolo de aniversário! A felicidade da cliente quando chegou em casa foi impagável! 🎂❤️"
        ]
    else:
        sample_posts = [
            f"Promoção especial na {user_data.get('fantasy_name', 'loja')}! Entrega rápida com SrBoy para toda região! 🚀",
            "Novos produtos chegaram! Qualidade garantida e entrega no mesmo dia. Peça já pelo app! 📦✨",
            "Agradecemos a todos nossos clientes pela confiança. Juntos fazemos a diferença na região! ❤️🙏"
        ]
    
    for i, content in enumerate(sample_posts[:2]):  # Only 2 posts to respect demo limits
        post_data = Post(
            user_id=user_id,
            content=content,
            likes_count=random.randint(5, 25),
            comments_count=random.randint(0, 8),
            created_at=datetime.now() - timedelta(days=random.randint(1, 7))
        ).dict()
        posts_collection.insert_one(post_data)
    
    # Create sample stories
    sample_stories = []
    if user_type == "motoboy":
        sample_stories = [
            "Começando o dia! ☀️ Primeira entrega já confirmada!",
            "Parada para o almoço em São Roque! 🍽️"
        ]
    else:
        sample_stories = [
            "Produtos frescos chegando agora! 📦",
            f"Atendimento especial na {user_data.get('fantasy_name', 'loja')}! ✨"
        ]
    
    for i, content in enumerate(sample_stories[:2]):  # Only 2 stories
        story_data = Story(
            user_id=user_id,
            content=content,
            created_at=datetime.now() - timedelta(hours=random.randint(1, 12)),
            expires_at=datetime.now() + timedelta(hours=random.randint(6, 23))
        ).dict()
        stories_collection.insert_one(story_data)

# ============================================
# ADMIN DASHBOARD ENDPOINTS
# ============================================

@app.post("/api/admin/login")
async def admin_login(auth_data: dict):
    """Admin-specific authentication"""
    email = auth_data.get('email', 'admin@srboy.com')
    name = auth_data.get('name', 'Naldino - Admin')
    user_type = 'admin'
    
    # Check for admin credentials (in production, use proper admin auth)
    if not email.endswith('@srboy.com') and 'admin' not in email.lower():
        raise HTTPException(status_code=403, detail="Admin credentials required")
    
    existing_admin = users_collection.find_one({"email": email, "user_type": "admin"})
    
    if existing_admin:
        user_data = existing_admin
    else:
        user_data = User(
            email=email,
            name=name,
            user_type=user_type
        ).dict()
        
        user_data.update({
            "admin_permissions": ["full_access", "security", "finance", "moderation", "analytics"],
            "created_at": datetime.now(),
            "last_login": datetime.now()
        })
        
        users_collection.insert_one(user_data)
    
    # Update last login
    users_collection.update_one(
        {"email": email},
        {"$set": {"last_login": datetime.now()}}
    )
    
    token_data = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "user_type": user_data["user_type"],
        "permissions": user_data.get("admin_permissions", []),
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    
    token = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")
    
    return {
        "token": token,
        "admin": {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "permissions": user_data.get("admin_permissions", [])
        }
    }

@app.get("/api/admin/dashboard")
async def admin_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Complete admin dashboard overview"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get comprehensive statistics
        total_users = users_collection.count_documents({})
        total_motoboys = users_collection.count_documents({"user_type": "motoboy"})
        total_lojistas = users_collection.count_documents({"user_type": "lojista"})
        active_motoboys = users_collection.count_documents({"user_type": "motoboy", "is_available": True})
        
        total_deliveries = deliveries_collection.count_documents({})
        completed_deliveries = deliveries_collection.count_documents({"status": "delivered"})
        pending_deliveries = deliveries_collection.count_documents({"status": {"$in": ["pending", "matched"]}})
        active_deliveries = deliveries_collection.count_documents({"status": {"$in": ["pickup_confirmed", "in_transit", "waiting"]}})
        
        # Financial metrics
        total_revenue = 0
        total_motoboy_earnings = 0
        total_platform_fees = 0
        
        delivered_deliveries = deliveries_collection.find({"status": "delivered"})
        for delivery in delivered_deliveries:
            total_revenue += delivery.get("total_price", 0)
            total_motoboy_earnings += delivery.get("motoboy_earnings", 0)
            total_platform_fees += delivery.get("platform_fee", 0)
        
        # Recent activity
        recent_deliveries = list(deliveries_collection.find({}).sort("created_at", -1).limit(10))
        recent_users = list(users_collection.find({"user_type": {"$in": ["motoboy", "lojista"]}}).sort("created_at", -1).limit(10))
        
        # Clean data
        for delivery in recent_deliveries:
            delivery.pop("_id", None)
        for user in recent_users:
            user.pop("_id", None)
        
        # City statistics
        city_stats = {}
        for city in CITIES_SERVED:
            city_motoboys = users_collection.count_documents({"user_type": "motoboy", "base_city": city})
            city_deliveries = deliveries_collection.count_documents({"pickup_address.city": city})
            city_stats[city] = {
                "motoboys": city_motoboys,
                "deliveries": city_deliveries,
                "demand_level": predict_demand_for_city(city).get("predicted_demand_level", "medium")
            }
        
        # Security alerts (simulated based on real data)
        high_risk_motoboys = []
        motoboys = users_collection.find({"user_type": "motoboy"}).limit(20)
        for motoboy in motoboys:
            if motoboy.get("ranking_score", 100) < 70:
                high_risk_motoboys.append({
                    "id": motoboy["id"],
                    "name": motoboy["name"],
                    "risk_level": "high" if motoboy.get("ranking_score", 100) < 50 else "medium",
                    "ranking_score": motoboy.get("ranking_score", 100)
                })
        
        # PIN system statistics
        pin_statistics = {
            "deliveries_with_pin": deliveries_collection.count_documents({"pin_confirmacao": {"$exists": True}}),
            "pin_validations_success": deliveries_collection.count_documents({"pin_validado_com_sucesso": True}),
            "pin_blocked": deliveries_collection.count_documents({"pin_bloqueado": True}),
            "avg_pin_attempts": 1.2  # Simulated average
        }
        
        return {
            "overview": {
                "total_users": total_users,
                "total_motoboys": total_motoboys,
                "total_lojistas": total_lojistas,
                "active_motoboys": active_motoboys,
                "total_deliveries": total_deliveries,
                "completed_deliveries": completed_deliveries,
                "pending_deliveries": pending_deliveries,
                "active_deliveries": active_deliveries,
                "completion_rate": round((completed_deliveries / max(total_deliveries, 1)) * 100, 2)
            },
            "financial": {
                "total_revenue": round(total_revenue, 2),
                "total_motoboy_earnings": round(total_motoboy_earnings, 2),
                "total_platform_fees": round(total_platform_fees, 2),
                "avg_delivery_value": round(total_revenue / max(completed_deliveries, 1), 2),
                "profit_margin": round((total_platform_fees / max(total_revenue, 1)) * 100, 2)
            },
            "security": {
                "high_risk_motoboys": len(high_risk_motoboys),
                "pin_system": pin_statistics,
                "recent_alerts": high_risk_motoboys[:5]
            },
            "city_statistics": city_stats,
            "recent_activity": {
                "deliveries": recent_deliveries,
                "users": recent_users
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/admin/users")
async def admin_get_users(
    user_type: str = None, 
    city: str = None, 
    page: int = 1, 
    limit: int = 50,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all users with filtering and pagination"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if user_type:
            query["user_type"] = user_type
        if city:
            query["base_city"] = city
        
        skip = (page - 1) * limit
        
        users = list(users_collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
        total_users = users_collection.count_documents(query)
        
        for user in users:
            user.pop("_id", None)
            # Add additional statistics for each user
            if user.get("user_type") == "motoboy":
                user["total_deliveries"] = deliveries_collection.count_documents({"motoboy_id": user["id"]})
                user["completed_deliveries"] = deliveries_collection.count_documents({"motoboy_id": user["id"], "status": "delivered"})
            elif user.get("user_type") == "lojista":
                user["total_orders"] = deliveries_collection.count_documents({"lojista_id": user["id"]})
        
        return {
            "users": users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_users,
                "pages": ((total_users - 1) // limit) + 1 if total_users > 0 else 0
            }
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/admin/deliveries")
async def admin_get_deliveries(
    status: str = None,
    city: str = None,
    date_from: str = None,
    date_to: str = None,
    page: int = 1,
    limit: int = 50,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all deliveries with filtering and pagination"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if status:
            query["status"] = status
        if city:
            query["pickup_address.city"] = city
        if date_from or date_to:
            query["created_at"] = {}
            if date_from:
                query["created_at"]["$gte"] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            if date_to:
                query["created_at"]["$lte"] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        skip = (page - 1) * limit
        
        deliveries = list(deliveries_collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
        total_deliveries = deliveries_collection.count_documents(query)
        
        # Enrich with user data
        for delivery in deliveries:
            delivery.pop("_id", None)
            
            # Get lojista info
            if delivery.get("lojista_id"):
                lojista = users_collection.find_one({"id": delivery["lojista_id"]})
                if lojista:
                    delivery["lojista_name"] = lojista.get("name")
                    delivery["lojista_fantasy"] = lojista.get("fantasy_name")
            
            # Get motoboy info
            if delivery.get("motoboy_id"):
                motoboy = users_collection.find_one({"id": delivery["motoboy_id"]})
                if motoboy:
                    delivery["motoboy_name"] = motoboy.get("name")
        
        return {
            "deliveries": deliveries,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_deliveries,
                "pages": ((total_deliveries - 1) // limit) + 1 if total_deliveries > 0 else 0
            }
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/admin/user/{user_id}/action")
async def admin_user_action(
    user_id: str, 
    action_data: dict, 
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Execute admin actions on users (suspend, activate, etc.)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        action = action_data.get("action")
        reason = action_data.get("reason", "Admin action")
        duration_hours = action_data.get("duration_hours", 24)
        
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        admin_action = {
            "action": action,
            "reason": reason,
            "admin_id": payload["user_id"],
            "executed_at": datetime.now(),
            "duration_hours": duration_hours if action == "suspend" else None
        }
        
        update_data = {"last_admin_action": admin_action}
        
        if action == "suspend":
            update_data.update({
                "is_suspended": True,
                "suspended_until": datetime.now() + timedelta(hours=duration_hours),
                "is_available": False
            })
        elif action == "activate":
            update_data.update({
                "is_suspended": False,
                "suspended_until": None,
                "is_available": True
            })
        elif action == "flag_for_review":
            update_data["flagged_for_review"] = True
        elif action == "clear_flags":
            update_data.update({
                "flagged_for_review": False,
                "is_suspended": False
            })
        
        users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        return {
            "message": f"Action '{action}' executed successfully",
            "user_id": user_id,
            "action_details": admin_action
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/admin/analytics")
async def admin_analytics(
    period: str = "7d",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed analytics and reports"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Calculate period dates
        if period == "24h":
            start_date = datetime.now() - timedelta(days=1)
        elif period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(days=7)
        
        # Time-based delivery statistics
        deliveries_in_period = list(deliveries_collection.find({
            "created_at": {"$gte": start_date}
        }))
        
        # Group by date
        daily_stats = {}
        revenue_stats = {}
        
        for delivery in deliveries_in_period:
            date_key = delivery["created_at"].date().isoformat()
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "total": 0, "completed": 0, "cancelled": 0, "pending": 0,
                    "revenue": 0, "platform_fees": 0
                }
            
            daily_stats[date_key]["total"] += 1
            daily_stats[date_key][delivery["status"]] = daily_stats[date_key].get(delivery["status"], 0) + 1
            
            if delivery["status"] == "delivered":
                daily_stats[date_key]["revenue"] += delivery.get("total_price", 0)
                daily_stats[date_key]["platform_fees"] += delivery.get("platform_fee", 0)
        
        # Performance metrics
        avg_delivery_time = 45  # Simulated - would calculate from actual timestamps
        customer_satisfaction = 4.7  # Simulated
        motoboy_satisfaction = 4.5  # Simulated
        
        # Top performers
        top_motoboys = list(users_collection.find({
            "user_type": "motoboy"
        }).sort("total_deliveries", -1).limit(10))
        
        top_lojistas = list(users_collection.find({
            "user_type": "lojista"  
        }).sort("total_deliveries", -1).limit(10))
        
        for user in top_motoboys + top_lojistas:
            user.pop("_id", None)
        
        return {
            "period": period,
            "date_range": {
                "from": start_date.isoformat(),
                "to": datetime.now().isoformat()
            },
            "daily_statistics": daily_stats,
            "performance_metrics": {
                "avg_delivery_time_minutes": avg_delivery_time,
                "customer_satisfaction": customer_satisfaction,
                "motoboy_satisfaction": motoboy_satisfaction,
                "success_rate": round(len([d for d in deliveries_in_period if d["status"] == "delivered"]) / max(len(deliveries_in_period), 1) * 100, 2)
            },
            "top_performers": {
                "motoboys": top_motoboys,
                "lojistas": top_lojistas
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/admin/financial-report")
async def admin_financial_report(
    period: str = "30d",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Generate comprehensive financial reports"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if payload["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Calculate period
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # Get financial data
        delivered_deliveries = list(deliveries_collection.find({
            "status": "delivered",
            "delivered_at": {"$gte": start_date}
        }))
        
        total_revenue = sum(d.get("total_price", 0) for d in delivered_deliveries)
        total_platform_fees = sum(d.get("platform_fee", 0) for d in delivered_deliveries)
        total_motoboy_earnings = sum(d.get("motoboy_earnings", 0) for d in delivered_deliveries)
        total_waiting_fees = sum(d.get("waiting_fee", 0) for d in delivered_deliveries)
        
        # Breakdown by city
        city_breakdown = {}
        for delivery in delivered_deliveries:
            city = delivery.get("pickup_address", {}).get("city", "Unknown")
            if city not in city_breakdown:
                city_breakdown[city] = {
                    "deliveries": 0, "revenue": 0, "platform_fees": 0,
                    "avg_delivery_value": 0
                }
            
            city_breakdown[city]["deliveries"] += 1
            city_breakdown[city]["revenue"] += delivery.get("total_price", 0)
            city_breakdown[city]["platform_fees"] += delivery.get("platform_fee", 0)
        
        # Calculate averages
        for city_data in city_breakdown.values():
            city_data["avg_delivery_value"] = round(
                city_data["revenue"] / max(city_data["deliveries"], 1), 2
            )
        
        # Payment method breakdown (simulated)
        payment_methods = {
            "pix": {"count": len(delivered_deliveries) * 0.6, "amount": total_revenue * 0.6},
            "credit_card": {"count": len(delivered_deliveries) * 0.3, "amount": total_revenue * 0.3},
            "wallet": {"count": len(delivered_deliveries) * 0.1, "amount": total_revenue * 0.1}
        }
        
        return {
            "period": period,
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_platform_fees": round(total_platform_fees, 2),
                "total_motoboy_earnings": round(total_motoboy_earnings, 2),
                "total_waiting_fees": round(total_waiting_fees, 2),
                "total_deliveries": len(delivered_deliveries),
                "avg_delivery_value": round(total_revenue / max(len(delivered_deliveries), 1), 2),
                "profit_margin": round((total_platform_fees / max(total_revenue, 1)) * 100, 2)
            },
            "city_breakdown": city_breakdown,
            "payment_methods": payment_methods,
            "trends": {
                "revenue_growth": 15.7,  # Simulated percentage
                "delivery_growth": 12.3,  # Simulated percentage  
                "customer_growth": 8.9   # Simulated percentage
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Admin Security endpoints (existing analyze endpoint is kept)
# The existing /api/security/analyze/{motoboy_id} endpoint remains as is

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)