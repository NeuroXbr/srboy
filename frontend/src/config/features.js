/**
 * SrBoy Feature Configuration
 * ===========================
 * 
 * This file controls which features are enabled in the SrBoy frontend.
 * Update these flags to activate/deactivate functionality without code changes.
 * 
 * USAGE:
 * import { FEATURES } from './config/features';
 * if (FEATURES.ECOMMERCE_ENABLED) { /* show e-commerce UI */ }
 */

// Get environment variables
const getEnvVar = (name, defaultValue = false) => {
  const value = process.env[name];
  if (typeof value === 'string') {
    return value.toLowerCase() === 'true';
  }
  return defaultValue;
};

// Feature flags configuration
export const FEATURES = {
  // Core delivery features (always enabled)
  DELIVERY_ENABLED: true,
  SOCIAL_PROFILES_ENABLED: true,
  PIN_CONFIRMATION_ENABLED: true,
  ADMIN_DASHBOARD_ENABLED: true,

  // Payment features (ready for activation)
  STRIPE_ENABLED: getEnvVar('REACT_APP_STRIPE_ENABLED', false),
  PIX_PAYMENTS_ENABLED: getEnvVar('REACT_APP_STRIPE_ENABLED', false), // Depends on Stripe
  WALLET_PAYMENTS_ENABLED: true, // Legacy wallet always available

  // E-commerce features (future use)
  ECOMMERCE_ENABLED: getEnvVar('REACT_APP_ECOMMERCE_ENABLED', false),
  PRODUCT_CATALOG_ENABLED: getEnvVar('REACT_APP_SHOW_PRODUCT_CATALOG', false),
  SHOPPING_CART_ENABLED: getEnvVar('REACT_APP_SHOW_SHOPPING_CART', false),
  ORDER_MANAGEMENT_ENABLED: getEnvVar('REACT_APP_ECOMMERCE_ENABLED', false),

  // Fast-food features (future use)
  FAST_FOOD_ENABLED: getEnvVar('REACT_APP_FAST_FOOD_ENABLED', false),
  FAST_FOOD_MENU_ENABLED: getEnvVar('REACT_APP_SHOW_FAST_FOOD_MENU', false),
  FOOD_CUSTOMIZATION_ENABLED: getEnvVar('REACT_APP_FAST_FOOD_ENABLED', false),

  // Marketplace features (future use)
  MARKETPLACE_ENABLED: getEnvVar('REACT_APP_MARKETPLACE_ENABLED', false),
  MULTI_VENDOR_ENABLED: getEnvVar('REACT_APP_MARKETPLACE_ENABLED', false),
  VENDOR_DASHBOARD_ENABLED: getEnvVar('REACT_APP_MARKETPLACE_ENABLED', false)
};

// Service URLs configuration
export const SERVICES = {
  BACKEND_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001',
  CATALOG_SERVICE_URL: process.env.REACT_APP_CATALOG_SERVICE_URL || 'http://localhost:8002',
  CART_SERVICE_URL: process.env.REACT_APP_CART_SERVICE_URL || 'http://localhost:8003',
  ORDER_SERVICE_URL: process.env.REACT_APP_ORDER_SERVICE_URL || 'http://localhost:8004'
};

// Stripe configuration
export const STRIPE_CONFIG = {
  PUBLIC_KEY: process.env.REACT_APP_STRIPE_PUBLIC_KEY || import.meta?.env?.REACT_APP_STRIPE_PUBLIC_KEY || '',
  ENABLED: FEATURES.STRIPE_ENABLED && Boolean(process.env.REACT_APP_STRIPE_PUBLIC_KEY || import.meta?.env?.REACT_APP_STRIPE_PUBLIC_KEY)
};

// UI Configuration
export const UI_CONFIG = {
  // Navigation items that should be shown/hidden based on features
  SHOW_ECOMMERCE_TAB: FEATURES.ECOMMERCE_ENABLED,
  SHOW_FAST_FOOD_TAB: FEATURES.FAST_FOOD_ENABLED,
  SHOW_MARKETPLACE_TAB: FEATURES.MARKETPLACE_ENABLED,
  
  // Payment options that should be available
  AVAILABLE_PAYMENT_METHODS: [
    ...(FEATURES.STRIPE_ENABLED ? ['card', 'pix'] : []),
    ...(FEATURES.WALLET_PAYMENTS_ENABLED ? ['wallet'] : [])
  ],
  
  // Feature announcements and badges
  SHOW_NEW_FEATURE_BADGES: {
    ecommerce: FEATURES.ECOMMERCE_ENABLED,
    fast_food: FEATURES.FAST_FOOD_ENABLED,
    marketplace: FEATURES.MARKETPLACE_ENABLED
  }
};

// Debug information (only in development)
if (process.env.NODE_ENV === 'development') {
  console.log('🔧 SrBoy Feature Configuration:', {
    FEATURES,
    SERVICES,
    STRIPE_CONFIG: {
      ...STRIPE_CONFIG,
      PUBLIC_KEY: STRIPE_CONFIG.PUBLIC_KEY ? '***CONFIGURED***' : 'NOT SET'
    },
    UI_CONFIG
  });
}

// Feature validation
export const validateFeatures = () => {
  const warnings = [];
  
  // Check for feature dependencies
  if (FEATURES.ECOMMERCE_ENABLED && !FEATURES.STRIPE_ENABLED) {
    warnings.push('⚠️ E-commerce is enabled but Stripe payments are disabled. Consider enabling STRIPE_ENABLED.');
  }
  
  if (FEATURES.STRIPE_ENABLED && !STRIPE_CONFIG.PUBLIC_KEY) {
    warnings.push('⚠️ Stripe is enabled but PUBLIC_KEY is not configured. Set REACT_APP_STRIPE_PUBLIC_KEY.');
  }
  
  if (FEATURES.FAST_FOOD_ENABLED && !FEATURES.ORDER_MANAGEMENT_ENABLED) {
    warnings.push('⚠️ Fast-food is enabled but order management is disabled. Consider enabling ORDER_MANAGEMENT_ENABLED.');
  }
  
  // Log warnings in development
  if (process.env.NODE_ENV === 'development' && warnings.length > 0) {
    console.warn('🚨 Feature Configuration Warnings:');
    warnings.forEach(warning => console.warn(warning));
  }
  
  return warnings;
};

// Initialize validation
validateFeatures();

// Export utility functions
export const isFeatureEnabled = (featureName) => {
  return FEATURES[featureName] || false;
};

export const getServiceUrl = (serviceName) => {
  return SERVICES[serviceName] || SERVICES.BACKEND_URL;
};

export const getAvailablePaymentMethods = () => {
  return UI_CONFIG.AVAILABLE_PAYMENT_METHODS;
};

// Default export
export default FEATURES;