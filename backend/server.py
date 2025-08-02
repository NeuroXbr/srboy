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

app = FastAPI(title="Super Boy Delivery API", version="1.0.0")

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
db = client.superboy_db

# Collections
users_collection = db.users
deliveries_collection = db.deliveries
chats_collection = db.chats
rankings_collection = db.rankings

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'super-boy-secret-key')

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
    license_plate: Optional[str] = None
    base_city: Optional[str] = None
    bank_details: Optional[dict] = None
    device_info: Optional[dict] = None  # IMEI, MAC Address for security
    ranking_score: Optional[int] = Field(default=100)
    total_deliveries: Optional[int] = Field(default=0)
    success_rate: Optional[float] = Field(default=0.0)
    is_available: Optional[bool] = Field(default=True)
    current_location: Optional[dict] = None  # {lat, lng}
    
    # Lojista specific fields
    fantasy_name: Optional[str] = None
    cnpj: Optional[str] = None
    address: Optional[dict] = None
    category: Optional[str] = None
    business_hours: Optional[dict] = None
    wallet_balance: Optional[float] = Field(default=0.0)

class Delivery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lojista_id: str
    motoboy_id: Optional[str] = None
    pickup_address: dict
    delivery_address: dict
    distance_km: float
    base_price: float = Field(default=9.00)  # R$ 9,00 minimum
    additional_price: float = Field(default=0.0)  # R$ 2,50 per km after 4th km
    platform_fee: float = Field(default=2.00)  # Fixed R$ 2,00 fee
    total_price: float
    status: str = Field(default="pending")  # pending, matched, in_progress, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.now)
    matched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    description: Optional[str] = None
    priority_score: Optional[int] = Field(default=0)

class CreateDelivery(BaseModel):
    pickup_address: dict
    delivery_address: dict
    description: Optional[str] = None

class MatchingResult(BaseModel):
    delivery_id: str
    motoboy_id: str
    motoboy_name: str
    motoboy_ranking: int
    distance_to_pickup: float
    estimated_time: int

# Cities served
CITIES_SERVED = [
    "Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"
]

# Helper Functions
def calculate_delivery_price(distance_km: float) -> dict:
    """Calculate fair and transparent delivery pricing"""
    base_price = 9.00  # R$ 9,00 minimum
    additional_price = 0.0
    
    if distance_km > 4:
        additional_km = distance_km - 4
        additional_price = additional_km * 2.50  # R$ 2,50 per km after 4th km
    
    total_price = base_price + additional_price
    platform_fee = 2.00  # Fixed platform fee
    motoboy_earning = total_price - platform_fee
    
    return {
        "base_price": base_price,
        "additional_price": additional_price,
        "total_price": total_price,
        "platform_fee": platform_fee,
        "motoboy_earning": motoboy_earning,
        "distance_km": round(distance_km, 2)
    }

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
    # Get available motoboys in the pickup city
    pickup_city = delivery['pickup_address'].get('city', '')
    
    available_motoboys = list(users_collection.find({
        "user_type": "motoboy",
        "is_available": True,
        "base_city": pickup_city
    }))
    
    if not available_motoboys:
        return None
    
    # Calculate scores for each motoboy
    candidates = []
    for motoboy in available_motoboys:
        if not motoboy.get('current_location'):
            continue
            
        # Distance to pickup
        distance_to_pickup = calculate_distance(
            motoboy['current_location'], 
            delivery['pickup_address']
        )
        
        # Weighted score: 70% ranking, 30% proximity
        ranking_score = motoboy.get('ranking_score', 100)
        proximity_score = max(0, 100 - (distance_to_pickup * 10))  # Closer = higher score
        
        weighted_score = (ranking_score * 0.7) + (proximity_score * 0.3)
        
        candidates.append({
            "motoboy": motoboy,
            "distance_to_pickup": distance_to_pickup,
            "weighted_score": weighted_score,
            "ranking_score": ranking_score
        })
    
    # Sort by weighted score (highest first)
    candidates.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    return candidates[0] if candidates else None

# API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Super Boy Delivery API"}

@app.post("/api/auth/google")
async def google_auth(auth_data: dict):
    """Google OAuth authentication - prepared for integration"""
    # TODO: Integrate with Google OAuth when credentials are provided
    # For now, create demo user for development
    
    email = auth_data.get('email', 'demo@superboy.com')
    name = auth_data.get('name', 'Demo User')
    user_type = auth_data.get('user_type', 'motoboy')
    
    # Check if user exists
    existing_user = users_collection.find_one({"email": email})
    
    if existing_user:
        user_data = existing_user
    else:
        # Create new user
        user_data = User(
            email=email,
            name=name,
            user_type=user_type
        ).dict()
        
        # Add type-specific defaults
        if user_type == "motoboy":
            user_data.update({
                "ranking_score": 100,
                "total_deliveries": 0,
                "success_rate": 0.0,
                "is_available": True,
                "base_city": "São Roque"  # Default city
            })
        elif user_type == "lojista":
            user_data.update({
                "wallet_balance": 100.0  # Demo balance
            })
        
        users_collection.insert_one(user_data)
    
    # Create JWT token
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
            "wallet_balance": user_data.get("wallet_balance")
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
        
        # Remove sensitive data
        user.pop("_id", None)
        user.pop("device_info", None)
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/deliveries")
async def create_delivery(delivery_data: CreateDelivery, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create new delivery request - Lojista only"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        
        # Verify user is lojista
        user = users_collection.find_one({"id": user_id, "user_type": "lojista"})
        if not user:
            raise HTTPException(status_code=403, detail="Only lojistas can create deliveries")
        
        # Calculate distance and pricing
        distance_km = calculate_distance(
            delivery_data.pickup_address,
            delivery_data.delivery_address
        )
        
        pricing = calculate_delivery_price(distance_km)
        
        # Check wallet balance
        if user.get('wallet_balance', 0) < pricing['total_price']:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")
        
        # Create delivery
        delivery = Delivery(
            lojista_id=user_id,
            pickup_address=delivery_data.pickup_address,
            delivery_address=delivery_data.delivery_address,
            distance_km=distance_km,
            additional_price=pricing['additional_price'],
            total_price=pricing['total_price'],
            description=delivery_data.description
        ).dict()
        
        deliveries_collection.insert_one(delivery)
        
        # Remove MongoDB _id for JSON serialization
        delivery.pop("_id", None)
        
        # Try to match with best motoboy
        best_match = find_best_motoboy(delivery)
        
        if best_match:
            # Update delivery with matched motoboy
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
                {"$inc": {"wallet_balance": -pricing['total_price']}}
            )
            
            delivery["motoboy_id"] = best_match["motoboy"]["id"]
            delivery["status"] = "matched"
            
            return {
                "delivery": delivery,
                "matched_motoboy": {
                    "id": best_match["motoboy"]["id"],
                    "name": best_match["motoboy"]["name"],
                    "ranking_score": best_match["ranking_score"],
                    "distance_to_pickup": round(best_match["distance_to_pickup"], 2)
                },
                "pricing": pricing
            }
        
        return {
            "delivery": delivery,
            "pricing": pricing,
            "message": "Delivery created, searching for available motoboy..."
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
        
        # Query based on user type
        if user_type == "lojista":
            query = {"lojista_id": user_id}
        elif user_type == "motoboy":
            query = {"motoboy_id": user_id}
        else:  # admin
            query = {}
        
        deliveries = list(deliveries_collection.find(query).sort("created_at", -1).limit(50))
        
        # Remove MongoDB _id
        for delivery in deliveries:
            delivery.pop("_id", None)
        
        return {"deliveries": deliveries}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.put("/api/deliveries/{delivery_id}/status")
async def update_delivery_status(delivery_id: str, status_data: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update delivery status"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]
        user_type = payload["user_type"]
        
        new_status = status_data.get("status")
        allowed_statuses = ["in_progress", "completed", "cancelled"]
        
        if new_status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        # Get delivery
        delivery = deliveries_collection.find_one({"id": delivery_id})
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        # Check permissions
        if user_type == "motoboy" and delivery.get("motoboy_id") != user_id:
            raise HTTPException(status_code=403, detail="Not your delivery")
        
        # Update delivery
        update_data = {"status": new_status}
        if new_status == "completed":
            update_data["completed_at"] = datetime.now()
            
            # Update motoboy stats
            users_collection.update_one(
                {"id": delivery["motoboy_id"]},
                {"$inc": {"total_deliveries": 1}}
            )
        
        deliveries_collection.update_one(
            {"id": delivery_id},
            {"$set": update_data}
        )
        
        return {"message": f"Delivery status updated to {new_status}"}
        
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
    """Calculate delivery pricing"""
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
            "base_city": motoboy.get("base_city", "")
        })
    
    return {"rankings": rankings}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)