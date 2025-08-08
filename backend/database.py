"""
Database connection module for PostgreSQL on Google Cloud Platform
Migrated from MongoDB to PostgreSQL for production scalability
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

# Setup logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/srboy_db')

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# PostgreSQL TABLE MODELS
# ============================================

class User(Base):
    """User table for motoboys, lojistas, and admins"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False, index=True)  # motoboy, lojista, admin
    photo_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Google OAuth integration
    google_id = Column(String(255), unique=True, nullable=True)
    google_picture = Column(Text, nullable=True)
    
    # Motoboy specific fields
    cnh = Column(String(50), nullable=True)
    moto_photo_url = Column(Text, nullable=True)
    moto_model = Column(String(100), nullable=True)
    moto_color = Column(String(50), nullable=True)
    license_plate = Column(String(20), nullable=True)
    base_city = Column(String(100), nullable=True, index=True)
    bank_details = Column(JSON, nullable=True)
    device_info = Column(JSON, nullable=True)
    ranking_score = Column(Integer, default=100)
    total_deliveries = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    is_available = Column(Boolean, default=True)
    current_location = Column(JSON, nullable=True)
    wallet_balance = Column(Float, default=0.0)
    
    # Lojista specific fields
    fantasy_name = Column(String(255), nullable=True)
    cnpj = Column(String(20), nullable=True)
    address = Column(JSON, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    business_hours = Column(JSON, nullable=True)
    loja_wallet_balance = Column(Float, default=150.0)
    
    # Admin specific fields
    permissions = Column(JSON, nullable=True)
    
    # Social features
    is_suspended = Column(Boolean, default=False)
    suspended_until = Column(DateTime, nullable=True)
    flagged_for_review = Column(Boolean, default=False)

class Delivery(Base):
    """Delivery orders table"""
    __tablename__ = "deliveries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lojista_id = Column(String, nullable=False, index=True)
    motoboy_id = Column(String, nullable=True, index=True)
    
    pickup_address = Column(JSON, nullable=False)
    delivery_address = Column(JSON, nullable=False)
    recipient_info = Column(JSON, nullable=False)
    
    distance_km = Column(Float, nullable=False)
    base_price = Column(Float, default=10.00)
    additional_price = Column(Float, default=0.0)
    platform_fee = Column(Float, default=2.00)
    waiting_fee = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    motoboy_earnings = Column(Float, default=0.0)
    
    status = Column(String(50), default="pending", index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    matched_at = Column(DateTime, nullable=True)
    pickup_confirmed_at = Column(DateTime, nullable=True)
    delivery_started_at = Column(DateTime, nullable=True)
    waiting_started_at = Column(DateTime, nullable=True)
    waiting_minutes = Column(Integer, default=0)
    delivered_at = Column(DateTime, nullable=True)
    
    description = Column(Text, nullable=True)
    priority_score = Column(Integer, default=0)
    product_description = Column(Text, nullable=True)
    
    # PIN Security System
    pin_completo = Column(String(8), nullable=True)
    pin_confirmacao = Column(String(4), nullable=True)
    pin_tentativas = Column(Integer, default=0)
    pin_bloqueado = Column(Boolean, default=False)
    pin_validado_com_sucesso = Column(Boolean, default=False)
    pin_validado_em = Column(DateTime, nullable=True)

class DeliveryReceipt(Base):
    """Digital delivery receipts"""
    __tablename__ = "delivery_receipts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    delivery_id = Column(String, nullable=False, index=True)
    loja_id = Column(String, nullable=False)
    motoboy_id = Column(String, nullable=False)
    
    loja_name = Column(String(255), nullable=False)
    motoboy_name = Column(String(255), nullable=False)
    motoboy_info = Column(JSON, nullable=False)
    recipient_info = Column(JSON, nullable=False)
    product_description = Column(Text, nullable=False)
    
    pickup_confirmed_at = Column(DateTime, nullable=False)
    delivered_at = Column(DateTime, nullable=False)
    pickup_address = Column(JSON, nullable=False)
    delivery_address = Column(JSON, nullable=False)
    
    distance_km = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    additional_price = Column(Float, nullable=False)
    waiting_fee = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    motoboy_earnings = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class Profile(Base):
    """Social profiles table"""
    __tablename__ = "profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True, index=True)
    bio = Column(String(300), default="")
    profile_photo = Column(Text, nullable=True)
    cover_photo = Column(Text, nullable=True)
    gallery_photos = Column(JSON, default=list)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

class Post(Base):
    """Social media posts table"""
    __tablename__ = "posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    content = Column(String(500), nullable=False)
    image = Column(Text, nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class Story(Base):
    """Social media stories table"""
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    content = Column(String(200), nullable=True)
    image = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=False)

class Follow(Base):
    """Social follows table"""
    __tablename__ = "follows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id = Column(String, nullable=False, index=True)
    followed_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class InventoryItem(Base):
    """Inventory management table"""
    __tablename__ = "inventory_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lojista_id = Column(String, nullable=False, index=True)
    
    nome = Column(String(200), nullable=False)
    descricao = Column(String(1000), nullable=True)
    preco = Column(Float, nullable=False)
    codigo_interno = Column(String(50), nullable=True, index=True)
    
    estoque = Column(Integer, default=0)
    estoque_minimo = Column(Integer, default=5)
    categoria = Column(String(100), nullable=True, index=True)
    unidade_medida = Column(String(10), default="un")
    
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)
    
    import_batch_id = Column(String, nullable=True)
    import_source = Column(String(20), nullable=True)

class InventoryBatch(Base):
    """Bulk inventory upload tracking"""
    __tablename__ = "inventory_batches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lojista_id = Column(String, nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)
    total_rows = Column(Integer, nullable=False)
    
    status = Column(String(50), default="pending", index=True)
    processed_rows = Column(Integer, default=0)
    successful_imports = Column(Integer, default=0)
    failed_imports = Column(Integer, default=0)
    
    field_mapping = Column(JSON, default=dict)
    validation_errors = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class StripeAccount(Base):
    """Stripe Connect accounts for payments"""
    __tablename__ = "stripe_accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    user_type = Column(String(20), nullable=False)
    
    stripe_account_id = Column(String(255), nullable=True)
    stripe_person_id = Column(String(255), nullable=True)
    account_status = Column(String(50), default="pending")
    
    bank_account_verified = Column(Boolean, default=False)
    payout_schedule = Column(String(20), default="daily")
    
    verification_status = Column(JSON, default=dict)
    required_documents = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

class PaymentTransaction(Base):
    """Payment transactions table"""
    __tablename__ = "payment_transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    transaction_type = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="BRL")
    status = Column(String(50), default="pending", index=True)
    
    user_id = Column(String, nullable=False, index=True)
    recipient_id = Column(String, nullable=True)
    delivery_id = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    stripe_transfer_id = Column(String(255), nullable=True)
    payment_method_type = Column(String(20), nullable=False)
    
    platform_fee = Column(Float, default=0)
    stripe_fee = Column(Float, default=0)
    net_amount = Column(Float, nullable=False)
    
    metadata = Column(JSON, default=dict)
    failure_reason = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    processed_at = Column(DateTime, nullable=True)

# ============================================
# DATABASE FUNCTIONS
# ============================================

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables"""
    try:
        create_tables()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test connection and create tables
    if test_connection():
        print("✅ Database connection successful")
        if init_database():
            print("✅ Database tables created successfully")
        else:
            print("❌ Failed to create database tables")
    else:
        print("❌ Database connection failed")