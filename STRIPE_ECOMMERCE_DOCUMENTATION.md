# 🚀 SrBoy - Stripe & E-commerce Integration Documentation

## 📋 **OVERVIEW**

The SrBoy platform has been completely prepared for Stripe payment integration and future e-commerce/fast-food expansion. All code is production-ready but features are disabled by default to maintain current functionality.

## 🔧 **ACTIVATION GUIDE**

### **1. Stripe Integration Activation**

#### **Backend Configuration (.env)**
```bash
# Set your real Stripe credentials
STRIPE_SECRET_KEY=sk_live_...          # Your Stripe secret key
STRIPE_PUBLIC_KEY=pk_live_...          # Your Stripe public key  
STRIPE_CONNECT_CLIENT_ID=ca_...        # Your Stripe Connect client ID
STRIPE_WEBHOOK_SECRET=whsec_...        # Your webhook secret
```

#### **Frontend Configuration (.env)**
```bash
# Enable Stripe features
REACT_APP_STRIPE_ENABLED=true
REACT_APP_STRIPE_PUBLIC_KEY=pk_live_...  # Your Stripe public key
```

#### **Restart Services**
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### **2. E-commerce Module Activation**

#### **Backend Configuration (.env)**
```bash
# Enable e-commerce modules
ECOMMERCE_MODULE_ENABLED=true
MARKETPLACE_MODULE_ENABLED=true
```

#### **Frontend Configuration (.env)**
```bash
# Enable e-commerce UI
REACT_APP_ECOMMERCE_ENABLED=true
REACT_APP_SHOW_PRODUCT_CATALOG=true
REACT_APP_SHOW_SHOPPING_CART=true
```

### **3. Fast-food Module Activation**

#### **Backend Configuration (.env)**
```bash
# Enable fast-food features
FAST_FOOD_MODULE_ENABLED=true
```

#### **Frontend Configuration (.env)**
```bash
# Enable fast-food UI
REACT_APP_FAST_FOOD_ENABLED=true
REACT_APP_SHOW_FAST_FOOD_MENU=true
```

## 🏗️ **TECHNICAL IMPLEMENTATION**

### **Database Structure (MongoDB)**

#### **New Collections (Ready for Use)**
```javascript
// E-commerce Collections
products_collection           // Product catalog
product_categories_collection // Product categories  
shopping_carts_collection     // User shopping carts
cart_items_collection         // Cart items
ecommerce_orders_collection   // E-commerce orders

// Fast-food Collections
fastfood_menus_collection     // Restaurant menus
fastfood_items_collection     // Menu items

// Stripe Collections
stripe_accounts_collection    // Connect accounts for motoboys/lojistas
payment_transactions_collection // Payment records
```

#### **New Data Models**
```python
# E-commerce Models
class Product(BaseModel):
    # Complete product model with inventory, images, SEO
    
class ShoppingCart(BaseModel):
    # Shopping cart with analytics tracking
    
class EcommerceOrder(BaseModel):
    # Full order model with payment integration

# Payment Models
class StripeAccount(BaseModel):
    # Stripe Connect accounts for users
    
class PaymentTransaction(BaseModel):
    # Complete payment transaction tracking
```

### **API Endpoints (Production Ready)**

#### **Stripe Payment Endpoints**
```python
POST   /api/stripe/create-payment-intent     # Create card/PIX payments
POST   /api/stripe/create-pix-payment        # Brazil PIX payments
POST   /api/stripe/create-connect-account    # Create motoboy/lojista accounts
GET    /api/stripe/connect-onboarding-link   # Get onboarding links
POST   /api/stripe/webhook                   # Handle Stripe webhooks
GET    /api/stripe/payment-methods           # Get available payment methods
```

#### **E-commerce Endpoints (Ready for Activation)**
```python
GET    /api/products                         # Product catalog
GET    /api/cart/{user_id}                   # Shopping cart
POST   /api/orders                           # Create orders
GET    /api/ecommerce/status                 # Check module status
```

### **Microservices Architecture**

#### **Catalog Service (Port 8002)**
- **Location**: `/backend/microservices/catalog_service.py`
- **Features**: Product management, categories, inventory
- **Activation**: Set `ECOMMERCE_MODULE_ENABLED=true`

#### **Cart Service (Port 8003)**  
- **Location**: `/backend/microservices/cart_service.py`
- **Features**: Shopping cart, item management, checkout prep
- **Activation**: Set `ECOMMERCE_MODULE_ENABLED=true`

#### **Order Service (Port 8004)**
- **Location**: `/backend/microservices/order_service.py`
- **Features**: Order processing, fast-food integration, analytics
- **Activation**: Set `ECOMMERCE_MODULE_ENABLED=true` or `FAST_FOOD_MODULE_ENABLED=true`

## 💳 **STRIPE INTEGRATION DETAILS**

### **Payment Processing Flow**
1. **Frontend** calls `/api/stripe/create-payment-intent`
2. **Backend** creates Stripe PaymentIntent with platform fee
3. **Frontend** processes payment with Stripe.js
4. **Webhook** confirms payment and triggers business logic
5. **Automatic payouts** to motoboys/lojistas via Stripe Connect

### **Stripe Connect Integration**
```python
# Create Connect account for motoboy/lojista
POST /api/stripe/create-connect-account

# Get onboarding link
GET /api/stripe/connect-onboarding-link

# Automatic transfers after successful delivery
# - Platform keeps 2% fee or R$ 2.00 minimum
# - Remaining amount goes to motoboy/lojista
```

### **PIX Payments (Brazil)**
```python
# Create PIX payment
POST /api/stripe/create-pix-payment
{
  "amount": 25.00,
  "delivery_id": "uuid",
  "customer_email": "user@example.com"
}

# Returns PIX payment intent for frontend processing
```

### **Webhook Security**
```python
# Stripe webhook endpoint with signature verification
POST /api/stripe/webhook
# Headers: stripe-signature

# Handles all Stripe events:
# - payment_intent.succeeded
# - payment_intent.payment_failed  
# - account.updated
# - transfer.created
# - payout.paid
```

## 🛍️ **E-COMMERCE IMPLEMENTATION**

### **Product Management**
```python
class Product(BaseModel):
    name: str = Field(max_length=200)
    description: str = Field(max_length=1000) 
    price: float = Field(gt=0)
    category_id: str
    stock_quantity: int = Field(default=0)
    images: List[str] = Field(max_items=10)  # base64 images
    # ... additional e-commerce fields
```

### **Shopping Cart**
```python
class ShoppingCart(BaseModel):
    user_id: str
    status: str = "active"  # active, abandoned, converted
    # Analytics fields for cart abandonment tracking
```

### **Order Processing**
```python
class EcommerceOrder(BaseModel):
    user_id: str
    lojista_id: str
    status: str  # pending → confirmed → preparing → ready → delivered
    payment_method: str  # stripe_card, stripe_pix, wallet
    payment_status: str  # pending, paid, failed, refunded
    stripe_payment_intent_id: Optional[str]
    # ... complete order workflow
```

## 🍔 **FAST-FOOD IMPLEMENTATION**

### **Menu Management**
```python
class FastFoodMenu(BaseModel):
    restaurant_id: str  # lojista_id
    name: str
    availability_start: str  # "08:00"
    availability_end: str    # "22:00" 
    days_available: List[str]
```

### **Menu Items**
```python
class FastFoodItem(BaseModel):
    name: str
    description: str
    price: float
    preparation_time_minutes: int
    spice_level: int = Field(ge=0, le=5)
    customization_options: List[dict]  # toppings, sizes, etc.
    allergens: List[str]
```

## 🎛️ **FRONTEND FEATURE CONTROL**

### **Feature Configuration File**
```javascript
// /frontend/src/config/features.js
import { FEATURES } from './config/features';

// Check if feature is enabled
if (FEATURES.ECOMMERCE_ENABLED) {
  // Show e-commerce UI components
}

if (FEATURES.STRIPE_ENABLED) {
  // Show Stripe payment options
}
```

### **Dynamic UI Components**
```javascript
// Navigation tabs appear based on feature flags
{FEATURES.ECOMMERCE_ENABLED && (
  <TabsTrigger value="products">Products</TabsTrigger>
)}

{FEATURES.FAST_FOOD_ENABLED && (
  <TabsTrigger value="menu">Menu</TabsTrigger>  
)}
```

### **Payment Method Selection**
```javascript
// Available payment methods based on configuration
const paymentMethods = getAvailablePaymentMethods();
// Returns: ['card', 'pix', 'wallet'] when Stripe is enabled
// Returns: ['wallet'] when only legacy wallet is enabled
```

## 🔐 **SECURITY CONSIDERATIONS**

### **Environment Variables**
- **Never commit real API keys to version control**
- **Use different keys for development/production**
- **Stripe webhook secrets must match your Stripe dashboard**

### **Payment Security**
- **All payment processing handled by Stripe**
- **No sensitive payment data stored locally**
- **PCI compliance handled by Stripe**
- **Webhook signature verification implemented**

### **API Security**
- **All payment endpoints require JWT authentication**
- **User authorization checks for Connect accounts**
- **Request validation and sanitization**
- **Rate limiting recommended for production**

## 📊 **MONITORING & ANALYTICS**

### **Payment Transaction Tracking**
```python
class PaymentTransaction(BaseModel):
    transaction_type: str  # delivery_payment, ecommerce_payment
    amount: float
    platform_fee: float
    stripe_payment_intent_id: str
    status: str  # pending, succeeded, failed
    # Complete audit trail
```

### **Business Intelligence Ready**
- **All transactions logged with metadata**
- **Cart abandonment tracking**
- **Popular product analytics**
- **Revenue breakdown by city/category**
- **Motoboy/lojista performance metrics**

## 🚀 **DEPLOYMENT CHECKLIST**

### **Before Enabling Stripe**
- [ ] Obtain real Stripe API keys from dashboard
- [ ] Set up Stripe Connect application
- [ ] Configure webhook endpoints in Stripe dashboard  
- [ ] Update environment variables
- [ ] Test with Stripe's test cards
- [ ] Verify webhook signature verification

### **Before Enabling E-commerce**
- [ ] Plan product catalog structure
- [ ] Design product categories
- [ ] Prepare initial product data
- [ ] Test shopping cart flow
- [ ] Configure order processing workflow
- [ ] Set up inventory management

### **Before Enabling Fast-food**
- [ ] Design restaurant menu structure
- [ ] Plan customization options
- [ ] Set up preparation time estimates
- [ ] Configure allergen information
- [ ] Test order customization flow

## 🛠️ **DEVELOPMENT COMMANDS**

### **Start Microservices (When Enabled)**
```bash
# Catalog Service
cd /backend/microservices
python catalog_service.py

# Cart Service  
python cart_service.py

# Order Service
python order_service.py
```

### **Test Stripe Integration**
```bash
# Test webhook locally (use Stripe CLI)
stripe listen --forward-to localhost:8001/api/stripe/webhook

# Test payments
curl -X POST http://localhost:8001/api/stripe/create-payment-intent \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 25.00, "delivery_id": "test_delivery"}'
```

## 📞 **SUPPORT & MAINTENANCE**

### **Logs & Debugging**
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.*.log

# Check specific service logs (when microservices are enabled)
tail -f /var/log/supervisor/catalog_service.*.log
tail -f /var/log/supervisor/cart_service.*.log
tail -f /var/log/supervisor/order_service.*.log
```

### **Common Issues**
1. **Stripe webhook verification fails**
   - Check webhook secret in environment variables
   - Verify endpoint URL in Stripe dashboard

2. **Payment intents fail**
   - Verify Stripe API keys are correct
   - Check Connect account status

3. **E-commerce features not showing**
   - Verify environment variables are set
   - Restart services after configuration changes

## 🎯 **CONCLUSION**

The SrBoy platform is now **100% ready** for:
- ✅ **Stripe Payment Processing** (card + PIX)
- ✅ **E-commerce Marketplace**
- ✅ **Fast-food Ordering**
- ✅ **Microservices Architecture**
- ✅ **Production Deployment**

**Simply update environment variables and restart services to activate any feature!**

---
*Generated on: December 2024*  
*Version: 2.0 - Production Ready*