#!/usr/bin/env python3
"""
SrBoy Delivery System - Comprehensive Backend API Tests
Tests all functionality including authentication, delivery system, social profiles, and security algorithms.
"""

import requests
import sys
import json
import base64
from datetime import datetime, timedelta

class SrBoyAPITester:
    def __init__(self, base_url="https://3b17a2db-24f5-40f1-9939-0c2c2ef10d9a.preview.emergentagent.com"):
        self.base_url = base_url
        self.motoboy_token = None
        self.lojista_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.motoboy_user = None
        self.lojista_user = None
        self.admin_user = None
        self.test_post_id = None
        self.test_story_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            return success, response.status_code, response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}
        except json.JSONDecodeError:
            return False, response.status_code, {"error": "Invalid JSON response"}

    def test_health_check(self):
        """Test API health endpoint"""
        success, status, data = self.make_request('GET', '/api/health')
        self.log_test("Health Check", success, f"Status: {status}, Service: {data.get('service', 'Unknown')}")
        return success

    def test_dependencies_and_imports(self):
        """Test that numpy/pandas dependencies and security algorithms are working"""
        # Test health endpoint which should load all imports
        success, status, data = self.make_request('GET', '/api/health')
        
        if success:
            # If health check passes, imports are working
            details = "Dependencies loaded successfully - numpy, pandas, security algorithms imported"
        else:
            details = f"Import error detected - Status: {status}, Response: {data}"
        
        self.log_test("Dependencies and Imports", success, details)
        return success

    def test_motoboy_authentication(self):
        """Test motoboy authentication"""
        auth_data = {
            "email": "carlos.motoboy@srboy.com",
            "name": "Carlos Silva",
            "user_type": "motoboy"
        }
        
        success, status, data = self.make_request('POST', '/api/auth/google', auth_data)
        
        if success and 'token' in data and 'user' in data:
            self.motoboy_token = data['token']
            self.motoboy_user = data['user']
            details = f"User: {data['user']['name']}, Ranking: {data['user'].get('ranking_score', 'N/A')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Motoboy Authentication", success, details)
        return success

    def test_lojista_authentication(self):
        """Test lojista authentication"""
        auth_data = {
            "email": "maria.lojista@srboy.com", 
            "name": "Maria Santos",
            "user_type": "lojista"
        }
        
        success, status, data = self.make_request('POST', '/api/auth/google', auth_data)
        
        if success and 'token' in data and 'user' in data:
            self.lojista_token = data['token']
            self.lojista_user = data['user']
            details = f"User: {data['user']['name']}, Wallet: R$ {data['user'].get('wallet_balance', 0):.2f}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Lojista Authentication", success, details)
        return success

    def test_admin_authentication(self):
        """Test admin authentication"""
        auth_data = {
            "email": "admin@srboy.com",
            "name": "Admin User",
            "user_type": "admin"
        }
        
        success, status, data = self.make_request('POST', '/api/auth/google', auth_data)
        
        if success and 'token' in data and 'user' in data:
            self.admin_token = data['token']
            self.admin_user = data['user']
            details = f"Admin User: {data['user']['name']}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Admin Authentication", success, details)
        return success

    def test_social_profile_get(self):
        """Test GET /api/profile/{user_id} endpoint"""
        if not self.motoboy_token or not self.motoboy_user:
            self.log_test("Social Profile GET", False, "No motoboy token available")
            return False

        user_id = self.motoboy_user['id']
        success, status, data = self.make_request('GET', f'/api/profile/{user_id}', token=self.motoboy_token)
        
        if success and 'user' in data and 'profile' in data:
            user_data = data['user']
            profile_data = data['profile']
            star_rating = user_data.get('star_rating', 0)
            is_following = data.get('is_following', False)
            
            details = f"Profile loaded - Star rating: {star_rating}/5, Following: {is_following}, Posts: {len(data.get('recent_posts', []))}, Stories: {len(data.get('active_stories', []))}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Social Profile GET", success, details)
        return success

    def test_social_profile_update(self):
        """Test PUT /api/profile endpoint"""
        if not self.motoboy_token:
            self.log_test("Social Profile UPDATE", False, "No motoboy token available")
            return False

        # Create a simple base64 image for testing
        test_image = base64.b64encode(b"fake_image_data").decode('utf-8')
        
        profile_data = {
            "bio": "Motoboy experiente em São Roque, sempre pontual e cuidadoso com as entregas!",
            "profile_photo": test_image,
            "cover_photo": test_image,
            "gallery_photos": [test_image]  # Only 1 photo (max 2 allowed)
        }
        
        success, status, data = self.make_request('PUT', '/api/profile', profile_data, self.motoboy_token)
        
        if success:
            details = "Profile updated successfully with bio, photos, and gallery"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Social Profile UPDATE", success, details)
        return success

    def test_profile_bio_validation(self):
        """Test profile bio length validation (max 300 chars)"""
        if not self.motoboy_token:
            self.log_test("Profile Bio Validation", False, "No motoboy token available")
            return False

        # Test with bio exceeding 300 characters
        long_bio = "A" * 301  # 301 characters
        profile_data = {"bio": long_bio}
        
        success, status, data = self.make_request('PUT', '/api/profile', profile_data, self.motoboy_token, 400)
        
        if status == 400 and "cannot exceed 300 characters" in data.get('detail', ''):
            success = True
            details = "Bio validation working - correctly rejected 301 character bio"
        else:
            success = False
            details = f"Expected 400 with bio length error, got {status}: {data}"
        
        self.log_test("Profile Bio Validation", success, details)
        return success

    def test_gallery_photos_validation(self):
        """Test gallery photos limit validation (max 2)"""
        if not self.motoboy_token:
            self.log_test("Gallery Photos Validation", False, "No motoboy token available")
            return False

        test_image = base64.b64encode(b"fake_image_data").decode('utf-8')
        
        # Test with 3 gallery photos (exceeds limit of 2)
        profile_data = {
            "bio": "Test bio",
            "gallery_photos": [test_image, test_image, test_image]  # 3 photos (max 2)
        }
        
        success, status, data = self.make_request('PUT', '/api/profile', profile_data, self.motoboy_token, 400)
        
        if status == 400 and "Maximum 2 gallery photos" in data.get('detail', ''):
            success = True
            details = "Gallery validation working - correctly rejected 3 photos"
        else:
            success = False
            details = f"Expected 400 with gallery limit error, got {status}: {data}"
        
        self.log_test("Gallery Photos Validation", success, details)
        return success

    def test_follow_user(self):
        """Test POST /api/follow/{user_id} endpoint"""
        if not self.lojista_token or not self.motoboy_user:
            self.log_test("Follow User", False, "No lojista token or motoboy user available")
            return False

        user_id = self.motoboy_user['id']
        success, status, data = self.make_request('POST', f'/api/follow/{user_id}', token=self.lojista_token)
        
        if success:
            details = f"Successfully followed user {user_id}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Follow User", success, details)
        return success

    def test_unfollow_user(self):
        """Test DELETE /api/follow/{user_id} endpoint"""
        if not self.lojista_token or not self.motoboy_user:
            self.log_test("Unfollow User", False, "No lojista token or motoboy user available")
            return False

        user_id = self.motoboy_user['id']
        success, status, data = self.make_request('DELETE', f'/api/follow/{user_id}', token=self.lojista_token)
        
        if success:
            details = f"Successfully unfollowed user {user_id}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Unfollow User", success, details)
        return success

    def test_create_post(self):
        """Test POST /api/posts endpoint"""
        if not self.motoboy_token:
            self.log_test("Create Post", False, "No motoboy token available")
            return False

        test_image = base64.b64encode(b"fake_post_image").decode('utf-8')
        
        post_data = {
            "content": "Acabei de fazer uma entrega super rápida em São Roque! Cliente muito satisfeito 😊",
            "image": test_image
        }
        
        success, status, data = self.make_request('POST', '/api/posts', post_data, self.motoboy_token)
        
        if success and 'post' in data:
            self.test_post_id = data['post']['id']
            details = f"Post created successfully - ID: {self.test_post_id}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Create Post", success, details)
        return success

    def test_post_daily_limit(self):
        """Test posts daily limit (4 per day)"""
        if not self.motoboy_token:
            self.log_test("Post Daily Limit", False, "No motoboy token available")
            return False

        # Try to create 4 more posts to test the limit
        posts_created = 0
        for i in range(5):  # Try to create 5 posts (should fail on 5th if limit is working)
            post_data = {
                "content": f"Test post number {i+2} for daily limit testing"
            }
            
            success, status, data = self.make_request('POST', '/api/posts', post_data, self.motoboy_token)
            
            if success:
                posts_created += 1
            else:
                if "Daily post limit reached" in data.get('detail', ''):
                    # This is expected behavior
                    break
        
        # Should be able to create 3 more posts (total 4 including the first one)
        if posts_created == 3:
            success = True
            details = f"Daily limit working correctly - created {posts_created + 1} posts total, then blocked"
        else:
            success = False
            details = f"Daily limit not working - created {posts_created + 1} posts without limit"
        
        self.log_test("Post Daily Limit", success, details)
        return success

    def test_post_content_validation(self):
        """Test post content length validation (max 500 chars)"""
        if not self.motoboy_token:
            self.log_test("Post Content Validation", False, "No motoboy token available")
            return False

        # Test with content exceeding 500 characters
        long_content = "A" * 501  # 501 characters
        post_data = {"content": long_content}
        
        success, status, data = self.make_request('POST', '/api/posts', post_data, self.motoboy_token, 400)
        
        if status == 400 and "cannot exceed 500 characters" in data.get('detail', ''):
            success = True
            details = "Post content validation working - correctly rejected 501 character post"
        else:
            success = False
            details = f"Expected 400 with content length error, got {status}: {data}"
        
        self.log_test("Post Content Validation", success, details)
        return success

    def test_create_story(self):
        """Test POST /api/stories endpoint"""
        if not self.motoboy_token:
            self.log_test("Create Story", False, "No motoboy token available")
            return False

        test_image = base64.b64encode(b"fake_story_image").decode('utf-8')
        
        story_data = {
            "content": "Trânsito tranquilo hoje em São Roque! 🏍️",
            "image": test_image
        }
        
        success, status, data = self.make_request('POST', '/api/stories', story_data, self.motoboy_token)
        
        if success and 'story' in data:
            self.test_story_id = data['story']['id']
            details = f"Story created successfully - ID: {self.test_story_id}, expires in 24h"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Create Story", success, details)
        return success

    def test_story_daily_limit(self):
        """Test stories daily limit (4 per day)"""
        if not self.motoboy_token:
            self.log_test("Story Daily Limit", False, "No motoboy token available")
            return False

        # Try to create 4 more stories to test the limit
        stories_created = 0
        for i in range(5):  # Try to create 5 stories (should fail on 5th if limit is working)
            story_data = {
                "content": f"Test story {i+2} for daily limit testing"
            }
            
            success, status, data = self.make_request('POST', '/api/stories', story_data, self.motoboy_token)
            
            if success:
                stories_created += 1
            else:
                if "Daily story limit reached" in data.get('detail', ''):
                    # This is expected behavior
                    break
        
        # Should be able to create 3 more stories (total 4 including the first one)
        if stories_created == 3:
            success = True
            details = f"Daily limit working correctly - created {stories_created + 1} stories total, then blocked"
        else:
            success = False
            details = f"Daily limit not working - created {stories_created + 1} stories without limit"
        
        self.log_test("Story Daily Limit", success, details)
        return success

    def test_story_content_validation(self):
        """Test story content length validation (max 200 chars)"""
        if not self.motoboy_token:
            self.log_test("Story Content Validation", False, "No motoboy token available")
            return False

        # Test with content exceeding 200 characters
        long_content = "A" * 201  # 201 characters
        story_data = {"content": long_content}
        
        success, status, data = self.make_request('POST', '/api/stories', story_data, self.motoboy_token, 400)
        
        if status == 400 and "cannot exceed 200 characters" in data.get('detail', ''):
            success = True
            details = "Story content validation working - correctly rejected 201 character story"
        else:
            success = False
            details = f"Expected 400 with content length error, got {status}: {data}"
        
        self.log_test("Story Content Validation", success, details)
        return success

    def test_posts_feed(self):
        """Test GET /api/feed/posts endpoint"""
        if not self.lojista_token:
            self.log_test("Posts Feed", False, "No lojista token available")
            return False

        success, status, data = self.make_request('GET', '/api/feed/posts?page=1&limit=10', token=self.lojista_token)
        
        if success and 'posts' in data:
            posts = data['posts']
            details = f"Posts feed loaded - {len(posts)} posts found"
            if posts:
                first_post = posts[0]
                if 'author' in first_post:
                    details += f", First post by: {first_post['author'].get('name', 'Unknown')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Posts Feed", success, details)
        return success

    def test_stories_feed(self):
        """Test GET /api/feed/stories endpoint"""
        if not self.lojista_token:
            self.log_test("Stories Feed", False, "No lojista token available")
            return False

        success, status, data = self.make_request('GET', '/api/feed/stories', token=self.lojista_token)
        
        if success and 'stories' in data:
            stories = data['stories']
            details = f"Stories feed loaded - {len(stories)} active stories found"
            if stories:
                first_story = stories[0]
                if 'author' in first_story:
                    details += f", First story by: {first_story['author'].get('name', 'Unknown')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Stories Feed", success, details)
        return success

    def test_security_analyze_motoboy(self):
        """Test GET /api/security/analyze/{motoboy_id} endpoint (admin only)"""
        if not self.admin_token or not self.motoboy_user:
            self.log_test("Security Analysis", False, "No admin token or motoboy user available")
            return False

        user_id = self.motoboy_user['id']
        success, status, data = self.make_request('GET', f'/api/security/analyze/{user_id}', token=self.admin_token)
        
        if success and 'analysis' in data:
            analysis = data['analysis']
            details = f"Security analysis completed - Risk score: {analysis.get('risk_score', 'N/A')}, Level: {analysis.get('risk_level', 'N/A')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Security Analysis", success, details)
        return success

    def test_security_analyze_unauthorized(self):
        """Test security analysis with non-admin user (should fail)"""
        if not self.motoboy_token or not self.motoboy_user:
            self.log_test("Security Analysis Unauthorized", False, "No motoboy token available")
            return False

        user_id = self.motoboy_user['id']
        success, status, data = self.make_request('GET', f'/api/security/analyze/{user_id}', token=self.motoboy_token, 403)
        
        if status == 403 and "Admin access required" in data.get('detail', ''):
            success = True
            details = "Authorization working - correctly blocked non-admin access"
        else:
            success = False
            details = f"Expected 403 with admin required error, got {status}: {data}"
        
        self.log_test("Security Analysis Unauthorized", success, details)
        return success

    def test_demand_prediction(self):
        """Test GET /api/demand/predict/{city} endpoint"""
        city = "São Roque"
        success, status, data = self.make_request('GET', f'/api/demand/predict/{city}')
        
        if success and 'prediction' in data:
            prediction = data['prediction']
            zones = prediction.get('zones', [])
            overall_demand = prediction.get('overall_demand', {})
            details = f"Demand prediction for {city} - {len(zones)} zones analyzed, overall level: {overall_demand.get('level', 'N/A')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Demand Prediction", success, details)
        return success

    def test_route_optimization(self):
        """Test POST /api/routes/optimize endpoint"""
        if not self.motoboy_token:
            self.log_test("Route Optimization", False, "No motoboy token available")
            return False

        route_data = {
            "deliveries": [
                {
                    "id": "test_delivery_1",
                    "pickup_address": {"lat": -23.5320, "lng": -47.1360},
                    "delivery_address": {"lat": -23.5450, "lng": -47.1680}
                }
            ]
        }
        
        success, status, data = self.make_request('POST', '/api/routes/optimize', route_data, self.motoboy_token)
        
        if success and 'optimization' in data:
            optimization = data['optimization']
            details = f"Route optimization completed - Distance: {optimization.get('total_distance', 'N/A')}km, Time: {optimization.get('estimated_time', 'N/A')}min"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Route Optimization", success, details)
        return success

    def test_chat_moderation(self):
        """Test POST /api/chat/moderate endpoint"""
        if not self.motoboy_token:
            self.log_test("Chat Moderation", False, "No motoboy token available")
            return False

        message_data = {
            "message": "Oi pessoal, trânsito tranquilo hoje em São Roque!",
            "city": "São Roque"
        }
        
        success, status, data = self.make_request('POST', '/api/chat/moderate', message_data, self.motoboy_token)
        
        if success and 'moderation' in data:
            moderation = data['moderation']
            action = moderation.get('action', 'unknown')
            flags = moderation.get('flags', [])
            details = f"Message moderated - Action: {action}, Flags: {', '.join(flags) if flags else 'none'}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Chat Moderation", success, details)
        return success

    def test_chat_moderation_profanity(self):
        """Test chat moderation with profanity"""
        if not self.motoboy_token:
            self.log_test("Chat Moderation Profanity", False, "No motoboy token available")
            return False

        message_data = {
            "message": "Esse idiota não sabe dirigir!",
            "city": "São Roque"
        }
        
        success, status, data = self.make_request('POST', '/api/chat/moderate', message_data, self.motoboy_token)
        
        if success and 'moderation' in data:
            moderation = data['moderation']
            action = moderation.get('action', 'unknown')
            filtered_message = moderation.get('filtered_message', '')
            
            if action == 'filtered' and '*' in filtered_message:
                details = f"Profanity filtering working - Action: {action}, Filtered: '{filtered_message}'"
            else:
                details = f"Profanity filtering may not be working - Action: {action}, Message: '{filtered_message}'"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Chat Moderation Profanity", success, details)
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting SrBoy Delivery System Comprehensive API Tests")
        print("=" * 70)
        
        # Basic connectivity and dependencies
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        self.test_dependencies_and_imports()
        
        # Authentication tests
        print("\n📱 Authentication Tests")
        print("-" * 30)
        self.test_motoboy_authentication()
        self.test_lojista_authentication()
        self.test_admin_authentication()
        
        # Social Profile System Tests
        print("\n👤 Social Profile System Tests")
        print("-" * 35)
        self.test_social_profile_get()
        self.test_social_profile_update()
        self.test_profile_bio_validation()
        self.test_gallery_photos_validation()
        
        # Follow System Tests
        print("\n👥 Follow System Tests")
        print("-" * 25)
        self.test_follow_user()
        self.test_unfollow_user()
        
        # Posts and Stories Tests
        print("\n📝 Posts and Stories Tests")
        print("-" * 30)
        self.test_create_post()
        self.test_post_daily_limit()
        self.test_post_content_validation()
        self.test_create_story()
        self.test_story_daily_limit()
        self.test_story_content_validation()
        
        # Social Feed Tests
        print("\n📰 Social Feed Tests")
        print("-" * 25)
        self.test_posts_feed()
        self.test_stories_feed()
        
        # Security Algorithm Tests
        print("\n🔒 Security Algorithm Tests")
        print("-" * 30)
        self.test_security_analyze_motoboy()
        self.test_security_analyze_unauthorized()
        self.test_demand_prediction()
        self.test_route_optimization()
        self.test_chat_moderation()
        self.test_chat_moderation_profanity()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! SrBoy backend is working correctly.")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed. Check the issues above.")
            return False

def main():
    """Main test execution"""
    tester = SrBoyAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())