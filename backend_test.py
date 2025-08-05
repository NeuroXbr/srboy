#!/usr/bin/env python3
"""
Super Boy Delivery System - Backend API Tests
Tests all core functionality including authentication, delivery creation, matching, and rankings.
"""

import requests
import sys
import json
from datetime import datetime

class SuperBoyAPITester:
    def __init__(self, base_url="https://3b17a2db-24f5-40f1-9939-0c2c2ef10d9a.preview.emergentagent.com"):
        self.base_url = base_url
        self.motoboy_token = None
        self.lojista_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.motoboy_user = None
        self.lojista_user = None

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

    def test_motoboy_authentication(self):
        """Test motoboy authentication"""
        auth_data = {
            "email": "demo.motoboy@superboy.com",
            "name": "Demo Motoboy",
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
            "email": "demo.lojista@superboy.com", 
            "name": "Demo Lojista",
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

    def test_user_profiles(self):
        """Test user profile retrieval"""
        # Test motoboy profile
        if self.motoboy_token:
            success, status, data = self.make_request('GET', '/api/users/profile', token=self.motoboy_token)
            details = f"Motoboy profile - Ranking: {data.get('ranking_score', 'N/A')}, Deliveries: {data.get('total_deliveries', 0)}"
            self.log_test("Motoboy Profile Retrieval", success, details)
        
        # Test lojista profile  
        if self.lojista_token:
            success, status, data = self.make_request('GET', '/api/users/profile', token=self.lojista_token)
            details = f"Lojista profile - Wallet: R$ {data.get('wallet_balance', 0):.2f}"
            self.log_test("Lojista Profile Retrieval", success, details)

    def test_cities_endpoint(self):
        """Test cities served endpoint"""
        success, status, data = self.make_request('GET', '/api/cities')
        
        if success and 'cities' in data:
            cities = data['cities']
            expected_cities = ["Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"]
            cities_match = all(city in cities for city in expected_cities)
            details = f"Cities: {', '.join(cities)}, All expected cities present: {cities_match}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Cities Endpoint", success, details)
        return success

    def test_pricing_calculation(self):
        """Test pricing calculation endpoint"""
        test_distances = [2.0, 5.0, 10.0]  # Test different distances
        
        for distance in test_distances:
            success, status, data = self.make_request('GET', f'/api/pricing/calculate?distance={distance}')
            
            if success:
                expected_base = 9.00
                expected_additional = max(0, (distance - 4) * 2.50) if distance > 4 else 0
                expected_total = expected_base + expected_additional
                
                actual_total = data.get('total_price', 0)
                pricing_correct = abs(actual_total - expected_total) < 0.01
                
                details = f"{distance}km - Expected: R$ {expected_total:.2f}, Got: R$ {actual_total:.2f}, Correct: {pricing_correct}"
            else:
                details = f"Status: {status}, Response: {data}"
            
            self.log_test(f"Pricing Calculation ({distance}km)", success and pricing_correct, details)

    def test_delivery_creation(self):
        """Test delivery creation by lojista"""
        if not self.lojista_token:
            self.log_test("Delivery Creation", False, "No lojista token available")
            return False

        delivery_data = {
            "pickup_address": {
                "city": "São Roque",
                "address": "Rua das Flores, 123",
                "lat": -23.5320,
                "lng": -47.1360
            },
            "delivery_address": {
                "city": "Mairinque", 
                "address": "Av. Principal, 456",
                "lat": -23.5450,
                "lng": -47.1680
            },
            "description": "Teste de entrega - produto frágil"
        }
        
        success, status, data = self.make_request('POST', '/api/deliveries', delivery_data, self.lojista_token, 200)
        
        if success and 'delivery' in data:
            delivery = data['delivery']
            pricing = data.get('pricing', {})
            matched_motoboy = data.get('matched_motoboy')
            
            details = f"Delivery ID: {delivery['id']}, Price: R$ {delivery['total_price']:.2f}, Distance: {delivery['distance_km']}km"
            if matched_motoboy:
                details += f", Matched with: {matched_motoboy['name']} (Ranking: {matched_motoboy['ranking_score']})"
            else:
                details += ", No motoboy matched"
                
            self.delivery_id = delivery['id']  # Store for status update test
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Delivery Creation", success, details)
        return success

    def test_delivery_listing(self):
        """Test delivery listing for both user types"""
        # Test lojista deliveries
        if self.lojista_token:
            success, status, data = self.make_request('GET', '/api/deliveries', token=self.lojista_token)
            if success and 'deliveries' in data:
                deliveries = data['deliveries']
                details = f"Lojista deliveries: {len(deliveries)} found"
            else:
                details = f"Status: {status}, Response: {data}"
            self.log_test("Lojista Delivery Listing", success, details)
        
        # Test motoboy deliveries
        if self.motoboy_token:
            success, status, data = self.make_request('GET', '/api/deliveries', token=self.motoboy_token)
            if success and 'deliveries' in data:
                deliveries = data['deliveries']
                details = f"Motoboy deliveries: {len(deliveries)} found"
            else:
                details = f"Status: {status}, Response: {data}"
            self.log_test("Motoboy Delivery Listing", success, details)

    def test_rankings(self):
        """Test rankings endpoint"""
        success, status, data = self.make_request('GET', '/api/rankings')
        
        if success and 'rankings' in data:
            rankings = data['rankings']
            details = f"Found {len(rankings)} motoboys in ranking"
            if rankings:
                top_motoboy = rankings[0]
                details += f", Top: {top_motoboy['name']} (Score: {top_motoboy['ranking_score']})"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Rankings Endpoint", success, details)
        return success

    def test_motoboy_location_update(self):
        """Test motoboy location update"""
        if not self.motoboy_token:
            self.log_test("Motoboy Location Update", False, "No motoboy token available")
            return False

        location_data = {
            "lat": -23.5320,
            "lng": -47.1360
        }
        
        success, status, data = self.make_request('PUT', '/api/motoboy/location', location_data, self.motoboy_token)
        details = f"Status: {status}, Response: {data.get('message', 'No message')}"
        self.log_test("Motoboy Location Update", success, details)
        return success

    def test_delivery_status_update(self):
        """Test delivery status update"""
        if not hasattr(self, 'delivery_id') or not self.motoboy_token:
            self.log_test("Delivery Status Update", False, "No delivery ID or motoboy token available")
            return False

        # Try to update delivery status to in_progress
        status_data = {"status": "in_progress"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{self.delivery_id}/status', 
                                                status_data, self.motoboy_token)
        
        details = f"Status: {status}, Response: {data.get('message', 'No message')}"
        self.log_test("Delivery Status Update", success, details)
        return success

    def test_insufficient_wallet_balance(self):
        """Test delivery creation with insufficient wallet balance"""
        if not self.lojista_token:
            self.log_test("Insufficient Wallet Balance Test", False, "No lojista token available")
            return False

        # Create a very long distance delivery to exceed wallet balance
        delivery_data = {
            "pickup_address": {
                "city": "Araçariguama",
                "address": "Rua A, 1",
                "lat": -23.4400,
                "lng": -47.0600
            },
            "delivery_address": {
                "city": "Ibiúna",
                "address": "Rua B, 1000",
                "lat": -23.6560,
                "lng": -47.2230  # Very far to make expensive delivery
            },
            "description": "Teste de saldo insuficiente"
        }
        
        success, status, data = self.make_request('POST', '/api/deliveries', delivery_data, 
                                                self.lojista_token, 400)  # Expect 400 error
        
        if status == 400 and 'Insufficient wallet balance' in data.get('detail', ''):
            success = True
            details = "Correctly rejected delivery due to insufficient balance"
        else:
            success = False
            details = f"Expected 400 with insufficient balance error, got {status}: {data}"
        
        self.log_test("Insufficient Wallet Balance Test", success, details)
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Super Boy Delivery System API Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Authentication tests
        self.test_motoboy_authentication()
        self.test_lojista_authentication()
        
        # Profile tests
        self.test_user_profiles()
        
        # Basic endpoint tests
        self.test_cities_endpoint()
        self.test_pricing_calculation()
        self.test_rankings()
        
        # Location update test
        self.test_motoboy_location_update()
        
        # Core business logic tests
        self.test_delivery_creation()
        self.test_delivery_listing()
        self.test_delivery_status_update()
        
        # Edge case tests
        self.test_insufficient_wallet_balance()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend is working correctly.")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed. Check the issues above.")
            return False

def main():
    """Main test execution"""
    tester = SuperBoyAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())