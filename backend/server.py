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
from geopy.distance import geodesic
import asyncio
from security_algorithms import analyze_motoboy_security, optimize_delivery_routes, predict_demand_for_city, moderate_chat_message

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

# API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "SrBoy Delivery API v2.0", "new_features": ["waiting_fees", "digital_receipts", "enhanced_pricing"]}

@app.post("/api/auth/google")
async def google_auth(auth_data: dict):
    """Google OAuth authentication - prepared for integration"""
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
            user_data.update({
                "ranking_score": 100,
                "total_deliveries": 0,
                "success_rate": 0.0,
                "is_available": True,
                "base_city": "São Roque",
                "wallet_balance": 0.0,
                "moto_model": "Honda CG 160",
                "moto_color": "Vermelha",
                "license_plate": "ABC-1234"
            })
        elif user_type == "lojista":
            user_data.update({
                "loja_wallet_balance": 150.0,
                "fantasy_name": f"Loja {name}"
            })
        
        users_collection.insert_one(user_data)
    
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
            "wallet_balance": user_data.get("wallet_balance", user_data.get("loja_wallet_balance", 0))
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
            deliveries_collection.update_one(
                {"id": delivery["id"]},
                {
                    "$set": {
                        "motoboy_id": best_match["motoboy"]["id"],
                        "status": "matched",
                        "matched_at": datetime.now()
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
                "pricing": pricing
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
            
            # Create digital receipt
            lojista = users_collection.find_one({"id": delivery["lojista_id"]})
            motoboy = users_collection.find_one({"id": delivery["motoboy_id"]})
            if lojista and motoboy:
                receipt = create_delivery_receipt(delivery, lojista, motoboy)
                update_data["receipt_id"] = receipt["id"]
        
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
        
        # Get delivery history
        deliveries = list(deliveries_collection.find({"motoboy_id": motoboy_id}).sort("created_at", -1).limit(100))
        for delivery in deliveries:
            delivery.pop("_id", None)
        
        motoboy["delivery_history"] = deliveries
        motoboy["location_history"] = motoboy.get("location_history", [])
        
        # Analyze security
        analysis = analyze_motoboy_security(motoboy)
        
        return {"analysis": analysis}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)