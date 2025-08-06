/**
 * SrBoy Feature Configuration
 * Ready for E-commerce/Fast-food/Stripe activation
 */

// Get environment variable as boolean
const getEnvBool = (name, defaultValue = false) => {
  const value = process.env[name];
  return value ? value.toLowerCase() === 'true' : defaultValue;
};

// Feature flags configuration
export const FEATURES = {
  // Core delivery features (always enabled)
  DELIVERY_ENABLED: true,
  SOCIAL_PROFILES_ENABLED: true,
  PIN_CONFIRMATION_ENABLED: true,
  ADMIN_DASHBOARD_ENABLED: true,

  // Payment features (ready for activation)
  STRIPE_ENABLED: getEnvBool('REACT_APP_STRIPE_ENABLED', false),
  PIX_PAYMENTS_ENABLED: getEnvBool('REACT_APP_STRIPE_ENABLED', false),
  WALLET_PAYMENTS_ENABLED: true,

  // E-commerce features (future use)
  ECOMMERCE_ENABLED: getEnvBool('REACT_APP_ECOMMERCE_ENABLED', false),
  PRODUCT_CATALOG_ENABLED: getEnvBool('REACT_APP_SHOW_PRODUCT_CATALOG', false),
  SHOPPING_CART_ENABLED: getEnvBool('REACT_APP_SHOW_SHOPPING_CART', false),

  // Fast-food features (future use)
  FAST_FOOD_ENABLED: getEnvBool('REACT_APP_FAST_FOOD_ENABLED', false),
  FAST_FOOD_MENU_ENABLED: getEnvBool('REACT_APP_SHOW_FAST_FOOD_MENU', false),

  // Marketplace features (future use)
  MARKETPLACE_ENABLED: getEnvBool('REACT_APP_MARKETPLACE_ENABLED', false)
};

// Service URLs
export const SERVICES = {
  BACKEND_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001',
  CATALOG_SERVICE_URL: process.env.REACT_APP_CATALOG_SERVICE_URL || 'http://localhost:8002',
  CART_SERVICE_URL: process.env.REACT_APP_CART_SERVICE_URL || 'http://localhost:8003',
  ORDER_SERVICE_URL: process.env.REACT_APP_ORDER_SERVICE_URL || 'http://localhost:8004'
};

// Stripe configuration
export const STRIPE_CONFIG = {
  PUBLIC_KEY: process.env.REACT_APP_STRIPE_PUBLIC_KEY || '',
  ENABLED: FEATURES.STRIPE_ENABLED && Boolean(process.env.REACT_APP_STRIPE_PUBLIC_KEY)
};

// Available payment methods based on enabled features
export const getAvailablePaymentMethods = () => {
  const methods = [];
  
  if (FEATURES.STRIPE_ENABLED && STRIPE_CONFIG.PUBLIC_KEY) {
    methods.push('card', 'pix');
  }
  
  if (FEATURES.WALLET_PAYMENTS_ENABLED) {
    methods.push('wallet');
  }
  
  return methods;
};

// Check if feature is enabled
export const isFeatureEnabled = (featureName) => {
  return FEATURES[featureName] || false;
};

export default FEATURES;