#!/usr/bin/env python3
"""
Quick Social Profile Endpoints Test
"""

import requests
import json

def test_social_endpoints():
    base_url = "https://3b17a2db-24f5-40f1-9939-0c2c2ef10d9a.preview.emergentagent.com"
    
    # Authenticate as motoboy
    motoboy_auth = {
        "email": "carlos.motoboy@srboy.com",
        "name": "Carlos Silva",
        "user_type": "motoboy"
    }
    
    print("🏍️ Authenticating as motoboy...")
    motoboy_response = requests.post(f"{base_url}/api/auth/google", json=motoboy_auth)
    
    if motoboy_response.status_code != 200:
        print(f"❌ Authentication failed: {motoboy_response.status_code}")
        return False
    
    motoboy_token = motoboy_response.json()['token']
    motoboy_id = motoboy_response.json()['user']['id']
    print(f"✅ Authentication successful - ID: {motoboy_id}")
    
    headers = {'Authorization': f'Bearer {motoboy_token}'}
    
    # Test GET profile
    print(f"\n👤 Testing GET /api/profile/{motoboy_id}...")
    profile_response = requests.get(f"{base_url}/api/profile/{motoboy_id}", headers=headers)
    
    if profile_response.status_code == 200:
        print("✅ GET profile endpoint working!")
        data = profile_response.json()
        user_data = data.get('user', {})
        profile_data = data.get('profile', {})
        print(f"  • Star rating: {user_data.get('star_rating', 'N/A')}/5")
        print(f"  • Followers: {profile_data.get('followers_count', 0)}")
        print(f"  • Following: {profile_data.get('following_count', 0)}")
        print(f"  • Recent posts: {len(data.get('recent_posts', []))}")
        print(f"  • Active stories: {len(data.get('active_stories', []))}")
    else:
        print(f"❌ GET profile failed: {profile_response.status_code}")
        return False
    
    # Test PUT profile
    print(f"\n✏️ Testing PUT /api/profile...")
    profile_update = {
        "bio": "Motoboy experiente em São Roque! Sempre pontual e cuidadoso.",
        "gallery_photos": []
    }
    
    update_response = requests.put(f"{base_url}/api/profile", json=profile_update, headers=headers)
    
    if update_response.status_code == 200:
        print("✅ PUT profile endpoint working!")
        print("  • Profile updated successfully")
    else:
        print(f"❌ PUT profile failed: {update_response.status_code}")
        return False
    
    # Test GET feed endpoints
    print(f"\n📰 Testing GET /api/feed/posts...")
    posts_response = requests.get(f"{base_url}/api/feed/posts", headers=headers)
    
    if posts_response.status_code == 200:
        print("✅ Posts feed endpoint working!")
        posts_data = posts_response.json()
        print(f"  • Posts found: {len(posts_data.get('posts', []))}")
    else:
        print(f"❌ Posts feed failed: {posts_response.status_code}")
        return False
    
    print(f"\n📖 Testing GET /api/feed/stories...")
    stories_response = requests.get(f"{base_url}/api/feed/stories", headers=headers)
    
    if stories_response.status_code == 200:
        print("✅ Stories feed endpoint working!")
        stories_data = stories_response.json()
        print(f"  • Stories found: {len(stories_data.get('stories', []))}")
    else:
        print(f"❌ Stories feed failed: {stories_response.status_code}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_social_endpoints()
    if success:
        print("\n🎉 All social profile endpoints are working correctly!")
    else:
        print("\n💥 Some social profile endpoints have issues!")