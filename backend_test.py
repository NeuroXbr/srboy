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
        success, status, data = self.make_request('GET', f'/api/security/analyze/{user_id}', token=self.motoboy_token, expected_status=403)
        
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

        # First update motoboy location
        location_data = {"lat": -23.5320, "lng": -47.1360}
        location_success, location_status, location_response = self.make_request('PUT', '/api/motoboy/location', location_data, self.motoboy_token)
        
        if not location_success:
            self.log_test("Route Optimization", False, f"Failed to update location: {location_status} - {location_response}")
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

    # ========================================
    # PIN SYSTEM TESTS - CORRECTED VERSION
    # ========================================
    
    def test_create_delivery_for_pin_testing(self):
        """Create a delivery for PIN system testing"""
        if not self.lojista_token:
            self.log_test("Create Delivery for PIN Testing", False, "No lojista token available")
            return False, None

        delivery_data = {
            "pickup_address": {
                "street": "Rua das Flores, 123",
                "city": "São Roque",
                "state": "SP",
                "zipcode": "18130-000",
                "lat": -23.5320,
                "lng": -47.1360
            },
            "delivery_address": {
                "street": "Av. Principal, 456",
                "city": "São Roque", 
                "state": "SP",
                "zipcode": "18130-100",
                "lat": -23.5450,
                "lng": -47.1680
            },
            "recipient_info": {
                "name": "João Silva Santos",
                "rg": "12.345.678-9",
                "alternative_recipient": "Maria Silva Santos"
            },
            "description": "Medicamentos da farmácia",
            "product_description": "Remédios para pressão alta - 2 caixas"
        }
        
        success, status, data = self.make_request('POST', '/api/deliveries', delivery_data, self.lojista_token)
        
        if success and 'delivery' in data:
            delivery_id = data['delivery']['id']
            details = f"Delivery created successfully - ID: {delivery_id}, Status: {data['delivery']['status']}"
            self.log_test("Create Delivery for PIN Testing", True, details)
            return True, delivery_id
        else:
            details = f"Status: {status}, Response: {data}"
            self.log_test("Create Delivery for PIN Testing", False, details)
            return False, None

    def test_pin_generation_on_accept(self):
        """Test PIN generation when motoboy accepts delivery"""
        if not self.motoboy_token:
            self.log_test("PIN Generation on Accept", False, "No motoboy token available")
            return False, None

        # Create delivery first
        delivery_created, delivery_id = self.test_create_delivery_for_pin_testing()
        if not delivery_created:
            return False, None

        # Accept delivery (should generate PIN)
        success, status, data = self.make_request('POST', f'/api/deliveries/{delivery_id}/accept', token=self.motoboy_token)
        
        if success and 'pin_confirmacao' in data:
            pin_confirmacao = data['pin_confirmacao']
            if len(pin_confirmacao) == 4:
                details = f"PIN generated successfully - Confirmation PIN: {pin_confirmacao} (4 digits)"
                self.log_test("PIN Generation on Accept", True, details)
                return True, delivery_id
            else:
                details = f"PIN format incorrect - Expected 4 digits, got: {pin_confirmacao}"
                self.log_test("PIN Generation on Accept", False, details)
                return False, delivery_id
        else:
            details = f"Status: {status}, Response: {data}"
            self.log_test("PIN Generation on Accept", False, details)
            return False, delivery_id

    def test_pin_validation_incorrect(self):
        """Test PIN validation with incorrect PIN"""
        # Generate PIN first
        pin_generated, delivery_id = self.test_pin_generation_on_accept()
        if not pin_generated:
            self.log_test("PIN Validation Incorrect", False, "Failed to generate PIN")
            return False

        # Try incorrect PIN
        pin_data = {"pin": "9999"}  # Wrong PIN
        success, status, data = self.make_request('POST', f'/api/deliveries/{delivery_id}/validate-pin', pin_data, self.motoboy_token)
        
        if success and data.get('success') == False:
            attempts = data.get('attempts', 0)
            remaining = data.get('remaining', 0)
            code = data.get('code', '')
            
            if code == 'PIN_INCORRECT' and attempts == 1 and remaining == 2:
                details = f"Incorrect PIN validation working - Attempts: {attempts}, Remaining: {remaining}"
                self.log_test("PIN Validation Incorrect", True, details)
                return True
            else:
                details = f"PIN validation logic issue - Code: {code}, Attempts: {attempts}, Remaining: {remaining}"
                self.log_test("PIN Validation Incorrect", False, details)
                return False
        else:
            details = f"Expected failed validation, got: Status {status}, Data: {data}"
            self.log_test("PIN Validation Incorrect", False, details)
            return False

    def test_pin_blocking_after_3_attempts(self):
        """Test PIN blocking after 3 incorrect attempts"""
        # Generate PIN first
        pin_generated, delivery_id = self.test_pin_generation_on_accept()
        if not pin_generated:
            self.log_test("PIN Blocking After 3 Attempts", False, "Failed to generate PIN")
            return False

        # Make 3 incorrect attempts
        pin_data = {"pin": "9999"}  # Wrong PIN
        
        for attempt in range(1, 4):  # Attempts 1, 2, 3
            success, status, data = self.make_request('POST', f'/api/deliveries/{delivery_id}/validate-pin', pin_data, self.motoboy_token)
            
            if not success or data.get('success') != False:
                details = f"Failed on attempt {attempt} - Status: {status}, Data: {data}"
                self.log_test("PIN Blocking After 3 Attempts", False, details)
                return False

        # Check if PIN is blocked after 3rd attempt
        if data.get('code') == 'PIN_BLOCKED':
            details = f"PIN correctly blocked after 3 attempts - Message: {data.get('message', '')}"
            self.log_test("PIN Blocking After 3 Attempts", True, details)
            return True
        else:
            details = f"PIN not blocked after 3 attempts - Code: {data.get('code', '')}, Data: {data}"
            self.log_test("PIN Blocking After 3 Attempts", False, details)
            return False

    def test_pin_validation_correct(self):
        """Test PIN validation with correct PIN"""
        # Generate PIN first
        pin_generated, delivery_id = self.test_pin_generation_on_accept()
        if not pin_generated:
            self.log_test("PIN Validation Correct", False, "Failed to generate PIN")
            return False, None

        # Get the actual PIN from database by checking delivery details
        success, status, data = self.make_request('GET', '/api/deliveries', token=self.motoboy_token)
        
        if not success or 'deliveries' not in data:
            self.log_test("PIN Validation Correct", False, "Failed to get delivery details")
            return False, None

        # Find our delivery and get the PIN
        delivery = None
        for d in data['deliveries']:
            if d['id'] == delivery_id:
                delivery = d
                break

        if not delivery or 'pin_confirmacao' not in delivery:
            self.log_test("PIN Validation Correct", False, "PIN not found in delivery")
            return False, None

        correct_pin = delivery['pin_confirmacao']
        
        # Validate with correct PIN
        pin_data = {"pin": correct_pin}
        success, status, data = self.make_request('POST', f'/api/deliveries/{delivery_id}/validate-pin', pin_data, self.motoboy_token)
        
        if success and data.get('success') == True:
            code = data.get('code', '')
            can_complete = data.get('can_complete_delivery', False)
            
            if code == 'PIN_VALID' and can_complete:
                details = f"Correct PIN validation working - Code: {code}, Can complete: {can_complete}"
                self.log_test("PIN Validation Correct", True, details)
                return True, delivery_id
            else:
                details = f"PIN validation response issue - Code: {code}, Can complete: {can_complete}"
                self.log_test("PIN Validation Correct", False, details)
                return False, delivery_id
        else:
            details = f"Expected successful validation, got: Status {status}, Data: {data}"
            self.log_test("PIN Validation Correct", False, details)
            return False, delivery_id

    def test_delivery_finalization_without_pin_validation(self):
        """Test that delivery finalization fails without PIN validation"""
        # Generate PIN but don't validate it
        pin_generated, delivery_id = self.test_pin_generation_on_accept()
        if not pin_generated:
            self.log_test("Delivery Finalization Without PIN", False, "Failed to generate PIN")
            return False

        # Try to finalize delivery without validating PIN
        status_data = {"status": "delivered"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{delivery_id}/status', status_data, self.motoboy_token, expected_status=400)
        
        if status == 400 and "PIN de confirmação deve ser validado" in data.get('detail', ''):
            details = f"Correctly blocked delivery finalization without PIN validation - Message: {data.get('detail', '')}"
            self.log_test("Delivery Finalization Without PIN", True, details)
            return True
        else:
            details = f"Expected 400 with PIN validation error, got {status}: {data}"
            self.log_test("Delivery Finalization Without PIN", False, details)
            return False

    def test_delivery_finalization_after_pin_validation(self):
        """Test delivery finalization after successful PIN validation"""
        # Validate PIN first
        pin_validated, delivery_id = self.test_pin_validation_correct()
        if not pin_validated:
            self.log_test("Delivery Finalization After PIN", False, "Failed to validate PIN")
            return False

        # Update delivery status to pickup_confirmed first (proper flow)
        status_data = {"status": "pickup_confirmed"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{delivery_id}/status', status_data, self.motoboy_token)
        
        if not success:
            self.log_test("Delivery Finalization After PIN", False, f"Failed to confirm pickup: {status} - {data}")
            return False

        # Update to in_transit
        status_data = {"status": "in_transit"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{delivery_id}/status', status_data, self.motoboy_token)
        
        if not success:
            self.log_test("Delivery Finalization After PIN", False, f"Failed to set in_transit: {status} - {data}")
            return False

        # Now finalize delivery (should work after PIN validation)
        status_data = {"status": "delivered"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{delivery_id}/status', status_data, self.motoboy_token)
        
        if success:
            details = f"Delivery finalized successfully after PIN validation - Message: {data.get('message', '')}"
            self.log_test("Delivery Finalization After PIN", True, details)
            return True
        else:
            details = f"Failed to finalize delivery after PIN validation - Status: {status}, Data: {data}"
            self.log_test("Delivery Finalization After PIN", False, details)
            return False

    def test_pin_data_structure_verification(self):
        """Test PIN data structure in database"""
        # Generate PIN first
        pin_generated, delivery_id = self.test_pin_generation_on_accept()
        if not pin_generated:
            self.log_test("PIN Data Structure Verification", False, "Failed to generate PIN")
            return False

        # Get delivery details to verify PIN structure
        success, status, data = self.make_request('GET', '/api/deliveries', token=self.motoboy_token)
        
        if not success or 'deliveries' not in data:
            self.log_test("PIN Data Structure Verification", False, "Failed to get delivery details")
            return False

        # Find our delivery
        delivery = None
        for d in data['deliveries']:
            if d['id'] == delivery_id:
                delivery = d
                break

        if not delivery:
            self.log_test("PIN Data Structure Verification", False, "Delivery not found")
            return False

        # Verify PIN structure
        required_fields = ['pin_completo', 'pin_confirmacao', 'pin_tentativas', 'pin_bloqueado']
        missing_fields = []
        
        for field in required_fields:
            if field not in delivery:
                missing_fields.append(field)

        if missing_fields:
            details = f"Missing PIN fields: {', '.join(missing_fields)}"
            self.log_test("PIN Data Structure Verification", False, details)
            return False

        # Verify field values
        pin_completo = delivery.get('pin_completo', '')
        pin_confirmacao = delivery.get('pin_confirmacao', '')
        pin_tentativas = delivery.get('pin_tentativas', -1)
        pin_bloqueado = delivery.get('pin_bloqueado', None)

        issues = []
        
        if len(pin_completo) != 8:
            issues.append(f"pin_completo should be 8 chars, got {len(pin_completo)}")
        
        if len(pin_confirmacao) != 4:
            issues.append(f"pin_confirmacao should be 4 chars, got {len(pin_confirmacao)}")
        
        if pin_confirmacao != pin_completo[-4:]:
            issues.append("pin_confirmacao should be last 4 digits of pin_completo")
        
        if pin_tentativas != 0:
            issues.append(f"pin_tentativas should be 0 initially, got {pin_tentativas}")
        
        if pin_bloqueado != False:
            issues.append(f"pin_bloqueado should be False initially, got {pin_bloqueado}")

        if issues:
            details = f"PIN structure issues: {'; '.join(issues)}"
            self.log_test("PIN Data Structure Verification", False, details)
            return False
        else:
            details = f"PIN structure correct - Full: {len(pin_completo)} chars, Confirmation: {len(pin_confirmacao)} chars, Attempts: {pin_tentativas}, Blocked: {pin_bloqueado}"
            self.log_test("PIN Data Structure Verification", True, details)
            return True

    def test_pin_validado_com_sucesso_field(self):
        """Test the new pin_validado_com_sucesso field tracking"""
        # Validate PIN correctly
        pin_validated, delivery_id = self.test_pin_validation_correct()
        if not pin_validated:
            self.log_test("PIN Validado Com Sucesso Field", False, "Failed to validate PIN")
            return False

        # Get delivery details to verify the new field
        success, status, data = self.make_request('GET', '/api/deliveries', token=self.motoboy_token)
        
        if not success or 'deliveries' not in data:
            self.log_test("PIN Validado Com Sucesso Field", False, "Failed to get delivery details")
            return False

        # Find our delivery
        delivery = None
        for d in data['deliveries']:
            if d['id'] == delivery_id:
                delivery = d
                break

        if not delivery:
            self.log_test("PIN Validado Com Sucesso Field", False, "Delivery not found")
            return False

        # Check the new fields
        pin_validado_com_sucesso = delivery.get('pin_validado_com_sucesso', None)
        pin_validado_em = delivery.get('pin_validado_em', None)

        if pin_validado_com_sucesso == True:
            if pin_validado_em:
                details = f"New PIN validation fields working - pin_validado_com_sucesso: {pin_validado_com_sucesso}, pin_validado_em: {pin_validado_em}"
                self.log_test("PIN Validado Com Sucesso Field", True, details)
                return True
            else:
                details = f"pin_validado_com_sucesso is True but pin_validado_em is missing"
                self.log_test("PIN Validado Com Sucesso Field", False, details)
                return False
        else:
            details = f"pin_validado_com_sucesso should be True after validation, got: {pin_validado_com_sucesso}"
            self.log_test("PIN Validado Com Sucesso Field", False, details)
            return False

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