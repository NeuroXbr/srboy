"""
SrBoy Delivery API v2.0 - Google Cloud Platform Production
Migrated from MongoDB to PostgreSQL for enterprise scalability
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
import os
import uuid
from datetime import datetime, timedelta
import logging
from geopy.distance import geodesic
import asyncio
import random
import string

# Import our database models and connections
from database import (
    get_db, init_database, test_connection,
    User, Delivery, DeliveryReceipt, Profile, Post, Story, Follow,
    InventoryItem, InventoryBatch, StripeAccount, PaymentTransaction
)

# Import Google Authentication
from google_auth import (
    verify_google_auth_token, create_user_jwt_token, validate_user_jwt_token,
    get_user_type_from_email
)

# Import security and payment modules
from security_algorithms import analyze_motoboy_security, optimize_delivery_routes, predict_demand_for_city, moderate_chat_message
from stripe_payments import stripe_payments, get_stripe_public_key, calculate_platform_fee, format_currency_brl

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app configuration
app = FastAPI(
    title="SrBoy Delivery API v2.0 - GCP Production",
    description="Enterprise-grade delivery platform on Google Cloud Platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# ============================================
# CORS CONFIGURATION FOR PRODUCTION
# ============================================
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://srdeliveri.com').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================
# SECURITY AND CONFIGURATION
# ============================================
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'srboy-gcp-production-secret-2024')

# Feature flags
FEATURE_INVENTORY_ENABLED = os.environ.get('FEATURE_INVENTORY_ENABLED', 'true').lower() == 'true'
INVENTORY_BULK_UPLOAD_ENABLED = os.environ.get('INVENTORY_BULK_UPLOAD_ENABLED', 'true').lower() == 'true'
INVENTORY_MANUAL_ENTRY_ENABLED = os.environ.get('INVENTORY_MANUAL_ENTRY_ENABLED', 'true').lower() == 'true'
ECOMMERCE_MODULE_ENABLED = os.environ.get('ECOMMERCE_MODULE_ENABLED', 'true').lower() == 'true'

# File upload configuration
MAX_UPLOAD_SIZE_MB = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 50))
ALLOWED_FILE_EXTENSIONS = os.environ.get('ALLOWED_FILE_EXTENSIONS', '.xlsx,.xls,.csv').split(',')
UPLOAD_TEMP_PATH = os.environ.get('UPLOAD_TEMP_PATH', '/tmp/srboy_uploads')
INVENTORY_BATCH_SIZE = int(os.environ.get('INVENTORY_BATCH_SIZE', 1000))

# Create upload directory
os.makedirs(UPLOAD_TEMP_PATH, exist_ok=True)

# Cities served
CITIES_SERVED = [
    "Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"
]

# ============================================
# PYDANTIC MODELS FOR API
# ============================================

class UserCreate(BaseModel):
    email: str
    name: str
    user_type: str
    google_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    user_type: str
    photo_url: Optional[str] = None
    ranking_score: Optional[int] = None
    wallet_balance: Optional[float] = None
    total_deliveries: Optional[int] = None

class DeliveryCreate(BaseModel):
    pickup_address: dict
    delivery_address: dict
    recipient_info: dict
    description: Optional[str] = None
    product_description: Optional[str] = None

class DeliveryResponse(BaseModel):
    id: str
    lojista_id: str
    motoboy_id: Optional[str] = None
    status: str
    total_price: float
    distance_km: float
    created_at: datetime

class InventoryItemCreate(BaseModel):
    nome: str = Field(max_length=200)
    descricao: Optional[str] = Field(max_length=1000)
    preco: float = Field(gt=0)
    codigo_interno: Optional[str] = Field(max_length=50)
    estoque: int = Field(default=0, ge=0)
    categoria: Optional[str] = Field(max_length=100)

class InventoryItemUpdate(BaseModel):
    nome: Optional[str] = Field(max_length=200)
    descricao: Optional[str] = Field(max_length=1000)
    preco: Optional[float] = Field(gt=0)
    codigo_interno: Optional[str] = Field(max_length=50)
    estoque: Optional[int] = Field(ge=0)
    categoria: Optional[str] = Field(max_length=100)
    ativo: Optional[bool] = None

# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_delivery_price(distance_km: float) -> dict:
    """Calculate delivery pricing with SrBoy rules"""
    base_price = 10.00  # R$ 10,00 base
    additional_price = 0.0
    platform_fee = 2.00  # Fixed platform fee
    
    if distance_km <= 4:
        total_price = base_price
        motoboy_earnings = base_price - platform_fee  # R$ 8,00
    else:
        motoboy_base = 8.00
        additional_km = distance_km
        additional_price = additional_km * 2.00  # R$ 2,00 per km
        total_price = base_price + additional_price
        motoboy_earnings = motoboy_base + additional_price
    
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

def generate_delivery_pin() -> tuple:
    """Generate 8-digit alphanumeric PIN and return (full_pin, confirmation_pin)"""
    characters = string.ascii_uppercase + string.digits
    pin_completo = ''.join(random.choice(characters) for _ in range(8))
    pin_confirmacao = pin_completo[-4:]
    return pin_completo, pin_confirmacao

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = validate_user_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

# ============================================
# DATABASE INITIALIZATION
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting SrBoy API v2.0 - GCP Production")
    
    # Test database connection
    if not test_connection():
        logger.error("Failed to connect to PostgreSQL database")
        raise Exception("Database connection failed")
    
    # Initialize database tables
    if not init_database():
        logger.error("Failed to initialize database tables")
        raise Exception("Database initialization failed")
    
    logger.info("✅ Database initialized successfully")
    logger.info(f"✅ CORS configured for: {CORS_ALLOWED_ORIGINS}")
    logger.info(f"✅ Feature flags: Inventory={FEATURE_INVENTORY_ENABLED}, Ecommerce={ECOMMERCE_MODULE_ENABLED}")

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SrBoy Delivery API v2.0 - GCP Production",
        "database": "PostgreSQL",
        "features": {
            "inventory": FEATURE_INVENTORY_ENABLED,
            "ecommerce": ECOMMERCE_MODULE_ENABLED,
            "google_auth": True
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/auth/google")
async def google_auth(auth_data: dict, db: Session = Depends(get_db)):
    """Google OAuth authentication"""
    try:
        # Extract Google ID token from request
        id_token = auth_data.get('id_token')
        user_type = auth_data.get('user_type', 'lojista')  # Default to lojista
        
        if not id_token:
            # Fallback to demo mode for testing
            email = auth_data.get('email', 'demo@srboy.com')
            name = auth_data.get('name', 'Demo User')
            google_id = f"demo_{uuid.uuid4().hex[:8]}"
        else:
            # Verify Google token
            google_info = verify_google_auth_token(id_token)
            if not google_info:
                raise HTTPException(status_code=400, detail="Invalid Google token")
            
            email = google_info['email']
            name = google_info['name']
            google_id = google_info['google_id']
            user_type = get_user_type_from_email(email, google_info)
        
        # Check if user exists
        existing_user = db.query(User).filter(
            or_(User.email == email, User.google_id == google_id)
        ).first()
        
        if existing_user:
            # Update existing user
            if google_id and not existing_user.google_id:
                existing_user.google_id = google_id
            if 'picture' in locals() and google_info:
                existing_user.photo_url = google_info.get('picture', '')
            
            db.commit()
            user = existing_user
        else:
            # Create new user
            demo_data = generate_demo_user_data(user_type)
            
            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
                name=name,
                user_type=user_type,
                google_id=google_id,
                photo_url=google_info.get('picture', '') if 'google_info' in locals() else '',
                **demo_data
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            user = new_user
            
            # Create demo profile
            create_demo_profile(db, user)
        
        # Create JWT token
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'user_type': user.user_type,
            'google_id': user.google_id
        }
        
        token = create_user_jwt_token(user_data)
        
        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "user_type": user.user_type,
                "ranking_score": user.ranking_score,
                "wallet_balance": user.wallet_balance or user.loja_wallet_balance or 0,
                "total_deliveries": user.total_deliveries,
                "photo_url": user.photo_url
            }
        }
        
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/api/users/profile")
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    user = db.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "user_type": user.user_type,
        "photo_url": user.photo_url,
        "ranking_score": user.ranking_score,
        "total_deliveries": user.total_deliveries,
        "wallet_balance": user.wallet_balance or user.loja_wallet_balance or 0,
        "base_city": user.base_city,
        "fantasy_name": user.fantasy_name,
        "is_available": user.is_available,
        "created_at": user.created_at.isoformat()
    }

# ============================================
# DELIVERY SYSTEM ENDPOINTS
# ============================================

@app.post("/api/deliveries")
async def create_delivery(
    delivery_data: DeliveryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new delivery request"""
    if current_user['user_type'] != 'lojista':
        raise HTTPException(status_code=403, detail="Only lojistas can create deliveries")
    
    user = db.query(User).filter(User.id == current_user['user_id']).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate distance and pricing
    distance_km = calculate_distance(
        delivery_data.pickup_address,
        delivery_data.delivery_address
    )
    
    pricing = calculate_delivery_price(distance_km)
    
    # Check wallet balance
    current_balance = user.loja_wallet_balance or 0
    if current_balance < pricing['total_price']:
        raise HTTPException(
            status_code=400,
            detail=f"Saldo insuficiente. Necessário: R$ {pricing['total_price']:.2f}, Disponível: R$ {current_balance:.2f}"
        )
    
    # Create delivery
    new_delivery = Delivery(
        id=str(uuid.uuid4()),
        lojista_id=current_user['user_id'],
        pickup_address=delivery_data.pickup_address,
        delivery_address=delivery_data.delivery_address,
        recipient_info=delivery_data.recipient_info,
        distance_km=distance_km,
        additional_price=pricing['additional_price'],
        total_price=pricing['total_price'],
        motoboy_earnings=pricing['motoboy_earnings'],
        description=delivery_data.description,
        product_description=delivery_data.product_description
    )
    
    db.add(new_delivery)
    db.commit()
    db.refresh(new_delivery)
    
    # Find best motoboy (simplified for now)
    best_motoboy = find_best_motoboy(db, delivery_data.pickup_address)
    
    if best_motoboy:
        # Auto-assign and generate PIN
        pin_completo, pin_confirmacao = generate_delivery_pin()
        
        new_delivery.motoboy_id = best_motoboy.id
        new_delivery.status = "matched"
        new_delivery.matched_at = datetime.now()
        new_delivery.pin_completo = pin_completo
        new_delivery.pin_confirmacao = pin_confirmacao
        
        # Deduct from lojista wallet
        user.loja_wallet_balance -= pricing['total_price']
        
        db.commit()
        
        return {
            "delivery": {
                "id": new_delivery.id,
                "status": new_delivery.status,
                "total_price": new_delivery.total_price,
                "distance_km": new_delivery.distance_km,
                "pin_confirmacao": pin_confirmacao
            },
            "matched_motoboy": {
                "id": best_motoboy.id,
                "name": best_motoboy.name,
                "ranking_score": best_motoboy.ranking_score
            },
            "pricing": pricing
        }
    
    return {
        "delivery": {
            "id": new_delivery.id,
            "status": new_delivery.status,
            "total_price": new_delivery.total_price,
            "distance_km": new_delivery.distance_km
        },
        "pricing": pricing,
        "message": "Entrega criada, procurando motoboy disponível..."
    }

@app.get("/api/deliveries")
async def get_deliveries(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get deliveries based on user type"""
    query = db.query(Delivery)
    
    if current_user['user_type'] == 'lojista':
        query = query.filter(Delivery.lojista_id == current_user['user_id'])
    elif current_user['user_type'] == 'motoboy':
        query = query.filter(Delivery.motoboy_id == current_user['user_id'])
    
    deliveries = query.order_by(desc(Delivery.created_at)).limit(50).all()
    
    return {
        "deliveries": [
            {
                "id": d.id,
                "status": d.status,
                "total_price": d.total_price,
                "distance_km": d.distance_km,
                "created_at": d.created_at.isoformat(),
                "pickup_address": d.pickup_address,
                "delivery_address": d.delivery_address,
                "motoboy_id": d.motoboy_id,
                "pin_confirmacao": d.pin_confirmacao if current_user['user_type'] == 'lojista' else None
            }
            for d in deliveries
        ]
    }

# ============================================
# INVENTORY MANAGEMENT ENDPOINTS
# ============================================

@app.get("/api/inventario/produtos")
async def get_inventory_items(
    page: int = 1,
    limit: int = 20,
    categoria: Optional[str] = None,
    busca: Optional[str] = None,
    apenas_ativos: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get inventory items with pagination and filters"""
    if not FEATURE_INVENTORY_ENABLED:
        return {
            "enabled": False,
            "message": "Módulo de inventário desabilitado. Contate o administrador.",
            "produtos": [],
            "total": 0
        }
    
    if current_user['user_type'] != 'lojista':
        raise HTTPException(status_code=403, detail="Apenas lojistas podem ver inventário")
    
    # Build query
    query = db.query(InventoryItem).filter(InventoryItem.lojista_id == current_user['user_id'])
    
    if apenas_ativos:
        query = query.filter(InventoryItem.ativo == True)
    
    if categoria:
        query = query.filter(InventoryItem.categoria == categoria)
    
    if busca:
        search_filter = or_(
            InventoryItem.nome.ilike(f"%{busca}%"),
            InventoryItem.descricao.ilike(f"%{busca}%"),
            InventoryItem.codigo_interno.ilike(f"%{busca}%")
        )
        query = query.filter(search_filter)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    skip = (page - 1) * limit
    items = query.order_by(desc(InventoryItem.created_at)).offset(skip).limit(limit).all()
    
    # Get categories
    categories = db.query(InventoryItem.categoria).filter(
        InventoryItem.lojista_id == current_user['user_id'],
        InventoryItem.ativo == True,
        InventoryItem.categoria.isnot(None)
    ).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Statistics
    total_products = db.query(InventoryItem).filter(
        InventoryItem.lojista_id == current_user['user_id'],
        InventoryItem.ativo == True
    ).count()
    
    low_stock_products = db.query(InventoryItem).filter(
        InventoryItem.lojista_id == current_user['user_id'],
        InventoryItem.ativo == True,
        InventoryItem.estoque <= InventoryItem.estoque_minimo
    ).count()
    
    return {
        "enabled": True,
        "produtos": [
            {
                "id": item.id,
                "nome": item.nome,
                "descricao": item.descricao,
                "preco": item.preco,
                "codigo_interno": item.codigo_interno,
                "estoque": item.estoque,
                "estoque_minimo": item.estoque_minimo,
                "categoria": item.categoria,
                "unidade_medida": item.unidade_medida,
                "ativo": item.ativo,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            }
            for item in items
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": ((total_count - 1) // limit) + 1 if total_count > 0 else 0
        },
        "filters": {
            "categorias": categories
        },
        "statistics": {
            "total_products": total_products,
            "low_stock_products": low_stock_products
        }
    }

@app.post("/api/inventario/produto")
async def create_inventory_item(
    item_data: InventoryItemCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create inventory item manually"""
    if not FEATURE_INVENTORY_ENABLED or not INVENTORY_MANUAL_ENTRY_ENABLED:
        return {
            "enabled": False,
            "message": "Cadastro manual de inventário desabilitado.",
            "success": False
        }
    
    if current_user['user_type'] != 'lojista':
        raise HTTPException(status_code=403, detail="Apenas lojistas podem gerenciar inventário")
    
    # Check for duplicate code
    if item_data.codigo_interno:
        existing = db.query(InventoryItem).filter(
            InventoryItem.lojista_id == current_user['user_id'],
            InventoryItem.codigo_interno == item_data.codigo_interno,
            InventoryItem.ativo == True
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Já existe um produto com este código interno")
    
    # Create item
    new_item = InventoryItem(
        id=str(uuid.uuid4()),
        lojista_id=current_user['user_id'],
        nome=item_data.nome,
        descricao=item_data.descricao,
        preco=item_data.preco,
        codigo_interno=item_data.codigo_interno,
        estoque=item_data.estoque,
        categoria=item_data.categoria,
        import_source="manual"
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {
        "success": True,
        "message": "Produto cadastrado com sucesso",
        "produto": {
            "id": new_item.id,
            "nome": new_item.nome,
            "preco": new_item.preco,
            "estoque": new_item.estoque,
            "categoria": new_item.categoria
        }
    }

# ============================================
# HELPER FUNCTIONS FOR DEMO DATA
# ============================================

def generate_demo_user_data(user_type: str) -> dict:
    """Generate demo data for new users"""
    if user_type == "motoboy":
        demo_motos = [
            {"model": "Honda CG 160", "color": "Vermelha", "plate": "SRB-1234"},
            {"model": "Yamaha Factor 125", "color": "Azul", "plate": "SRB-5678"},
            {"model": "Honda Titan 150", "color": "Preta", "plate": "SRB-9012"}
        ]
        selected_moto = random.choice(demo_motos)
        
        return {
            "ranking_score": random.randint(85, 98),
            "total_deliveries": random.randint(150, 500),
            "success_rate": round(random.uniform(0.92, 0.99), 2),
            "is_available": True,
            "base_city": random.choice(CITIES_SERVED),
            "wallet_balance": round(random.uniform(250.0, 800.0), 2),
            "moto_model": selected_moto["model"],
            "moto_color": selected_moto["color"],
            "license_plate": selected_moto["plate"]
        }
    elif user_type == "lojista":
        demo_lojas = [
            {"fantasy": "Farmácia Saúde Total", "category": "Farmácia"},
            {"fantasy": "Pizzaria Bella Vista", "category": "Restaurante"},
            {"fantasy": "Boutique Elegante", "category": "Loja de Roupas"}
        ]
        selected_loja = random.choice(demo_lojas)
        
        return {
            "fantasy_name": selected_loja["fantasy"],
            "category": selected_loja["category"],
            "loja_wallet_balance": round(random.uniform(300.0, 1200.0), 2),
            "total_deliveries": random.randint(50, 200)
        }
    else:  # admin
        return {
            "permissions": ["full_access", "security", "finance", "moderation", "analytics"]
        }

def create_demo_profile(db: Session, user: User):
    """Create demo social profile for new user"""
    try:
        profile = Profile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            bio="Novo usuário do SrBoy! 🚀",
            followers_count=0,
            following_count=0
        )
        
        db.add(profile)
        db.commit()
    except Exception as e:
        logger.error(f"Error creating demo profile: {str(e)}")

def find_best_motoboy(db: Session, pickup_address: dict):
    """Find best available motoboy based on ranking and proximity"""
    pickup_city = pickup_address.get('city', '')
    
    available_motoboys = db.query(User).filter(
        User.user_type == "motoboy",
        User.is_available == True,
        User.base_city == pickup_city
    ).limit(20).all()
    
    if not available_motoboys:
        return None
    
    # For now, return the highest ranked available motoboy
    return max(available_motoboys, key=lambda m: m.ranking_score or 0)

# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.get("/api/admin/dashboard")
async def admin_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin dashboard statistics"""
    if current_user['user_type'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get basic statistics
    total_users = db.query(User).count()
    total_motoboys = db.query(User).filter(User.user_type == "motoboy").count()
    total_lojistas = db.query(User).filter(User.user_type == "lojista").count()
    total_deliveries = db.query(Delivery).count()
    completed_deliveries = db.query(Delivery).filter(Delivery.status == "delivered").count()
    
    # Financial data
    total_revenue = db.query(func.sum(Delivery.total_price)).filter(
        Delivery.status == "delivered"
    ).scalar() or 0
    
    return {
        "overview": {
            "total_users": total_users,
            "total_motoboys": total_motoboys,
            "total_lojistas": total_lojistas,
            "total_deliveries": total_deliveries,
            "completed_deliveries": completed_deliveries,
            "completion_rate": round((completed_deliveries / max(total_deliveries, 1)) * 100, 2)
        },
        "financial": {
            "total_revenue": round(total_revenue, 2),
            "platform_fees": round(total_revenue * 0.2, 2),  # Estimated 20% platform fee
        },
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)