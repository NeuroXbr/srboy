"""
Google OAuth 2.0 Authentication Module for SrBoy
Production-ready integration with Google Cloud Platform
"""

import os
import logging
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'srboy-gcp-production-secret-2024')

class GoogleAuthenticator:
    """
    Google OAuth 2.0 authentication handler for SrBoy application.
    Validates Google ID tokens and creates/updates users in PostgreSQL.
    """
    
    def __init__(self):
        self.google_client_id = GOOGLE_CLIENT_ID
        self.google_client_secret = GOOGLE_CLIENT_SECRET
        self.jwt_secret = JWT_SECRET
        
        if not self.google_client_id:
            logger.error("GOOGLE_CLIENT_ID not found in environment variables")
        if not self.google_client_secret:
            logger.error("GOOGLE_CLIENT_SECRET not found in environment variables")
    
    def verify_google_token(self, id_token_str: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            id_token_str: Google ID token string
            
        Returns:
            Dict with user information or None if invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.google_client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error(f"Invalid token issuer: {idinfo['iss']}")
                return None
            
            # Extract user information
            user_info = {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo['name'],
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False),
                'locale': idinfo.get('locale', 'pt-BR')
            }
            
            logger.info(f"Successfully verified Google token for user: {user_info['email']}")
            return user_info
            
        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Google token: {str(e)}")
            return None
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create JWT token for authenticated user.
        
        Args:
            user_data: User information dictionary
            
        Returns:
            JWT token string
        """
        try:
            # Create token payload
            payload = {
                'user_id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'user_type': user_data['user_type'],
                'google_id': user_data.get('google_id'),
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(days=7)  # Token valid for 7 days
            }
            
            # Create JWT token
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            
            logger.info(f"Created JWT token for user: {user_data['email']}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT token: {str(e)}")
            raise
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating JWT token: {str(e)}")
            return None
    
    def determine_user_type(self, email: str, google_info: Dict[str, Any]) -> str:
        """
        Determine user type based on email domain and other factors.
        
        Args:
            email: User email address
            google_info: Google user information
            
        Returns:
            User type string (motoboy, lojista, admin)
        """
        # Admin users (srboy.com domain OR specific admin emails)
        admin_emails = [
            'admin@srboy.com',
            'naldino@srboy.com',
            'junior.lima@srdeliveri.com',  # ADMIN PRINCIPAL - SrBoy
        ]
        
        if email.endswith('@srboy.com') or email.lower() in admin_emails:
            return 'admin'
        
        # Business accounts (common business domains)
        business_domains = [
            'gmail.com', 'hotmail.com', 'outlook.com', 
            'yahoo.com', 'uol.com.br', 'bol.com.br'
        ]
        
        domain = email.split('@')[1].lower()
        
        # Default new users to lojista for business setup
        # They can change to motoboy during registration process
        return 'lojista'
    
    def get_profile_photo_url(self, google_picture: str) -> str:
        """
        Process Google profile picture URL for storage.
        
        Args:
            google_picture: Google profile picture URL
            
        Returns:
            Processed picture URL or empty string
        """
        if not google_picture:
            return ''
        
        # For production, you might want to download and store the image
        # in Google Cloud Storage instead of using external URLs
        return google_picture


# Global authenticator instance
google_auth = GoogleAuthenticator()

def verify_google_auth_token(id_token_str: str) -> Optional[Dict[str, Any]]:
    """
    Global function to verify Google authentication token.
    
    Args:
        id_token_str: Google ID token string
        
    Returns:
        User information dictionary or None
    """
    return google_auth.verify_google_token(id_token_str)

def create_user_jwt_token(user_data: Dict[str, Any]) -> str:
    """
    Global function to create JWT token for user.
    
    Args:
        user_data: User information dictionary
        
    Returns:
        JWT token string
    """
    return google_auth.create_jwt_token(user_data)

def validate_user_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Global function to validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload or None if invalid
    """
    return google_auth.validate_jwt_token(token)

def get_user_type_from_email(email: str, google_info: Dict[str, Any] = {}) -> str:
    """
    Global function to determine user type from email.
    
    Args:
        email: User email address
        google_info: Google user information
        
    Returns:
        User type string
    """
    return google_auth.determine_user_type(email, google_info)


if __name__ == "__main__":
    # Test Google authentication setup
    authenticator = GoogleAuthenticator()
    
    if authenticator.google_client_id:
        print("✅ Google Client ID configured")
    else:
        print("❌ Google Client ID missing")
    
    if authenticator.google_client_secret:
        print("✅ Google Client Secret configured")
    else:
        print("❌ Google Client Secret missing")
    
    print(f"JWT Secret: {'✅ Configured' if authenticator.jwt_secret else '❌ Missing'}")
    
    # Test JWT token creation (without real user data)
    test_user = {
        'id': 'test-user-id',
        'email': 'test@example.com',
        'name': 'Test User',
        'user_type': 'lojista',
        'google_id': '123456789'
    }
    
    try:
        token = authenticator.create_jwt_token(test_user)
        print("✅ JWT token creation successful")
        
        # Test token validation
        payload = authenticator.validate_jwt_token(token)
        if payload and payload['email'] == test_user['email']:
            print("✅ JWT token validation successful")
        else:
            print("❌ JWT token validation failed")
            
    except Exception as e:
        print(f"❌ JWT token test failed: {str(e)}")