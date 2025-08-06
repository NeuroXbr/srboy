#!/usr/bin/env python3
"""
Debug Security Analysis Response Structure
"""

import requests
import json

def debug_security_response():
    base_url = "https://d5522c0e-4488-4e1e-8d01-1376cee7c946.preview.emergentagent.com"
    
    # Authenticate as admin
    auth_data = {
        "email": "admin@srboy.com",
        "name": "Admin User",
        "user_type": "admin"
    }
    
    auth_response = requests.post(f"{base_url}/api/auth/google", json=auth_data)
    admin_token = auth_response.json()['token']
    
    # Authenticate as motoboy
    motoboy_auth = {
        "email": "carlos.motoboy@srboy.com",
        "name": "Carlos Silva",
        "user_type": "motoboy"
    }
    
    motoboy_response = requests.post(f"{base_url}/api/auth/google", json=motoboy_auth)
    motoboy_id = motoboy_response.json()['user']['id']
    
    # Get security analysis
    headers = {'Authorization': f'Bearer {admin_token}'}
    analysis_response = requests.get(f"{base_url}/api/security/analyze/{motoboy_id}", headers=headers)
    
    print("Full Security Analysis Response:")
    print("=" * 50)
    print(json.dumps(analysis_response.json(), indent=2))

if __name__ == "__main__":
    debug_security_response()