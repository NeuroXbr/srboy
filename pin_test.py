#!/usr/bin/env python3
"""
SrBoy PIN Confirmation System Tests
Tests the new PIN confirmation system for delivery security.
"""

import requests
import sys
import json
from datetime import datetime

class PINSystemTester:
    def __init__(self, base_url="https://3b17a2db-24f5-40f1-9939-0c2c2ef10d9a.preview.emergentagent.com"):
        self.base_url = base_url
        self.motoboy_token = None
        self.lojista_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.motoboy_user = None
        self.lojista_user = None
        self.test_delivery_id = None
        self.generated_pin = None

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

    def setup_authentication(self):
        """Setup authentication for lojista and motoboy"""
        print("🔐 Setting up authentication...")
        
        # Authenticate lojista
        lojista_auth = {
            "email": "lojista.pin@srboy.com",
            "name": "Lojista PIN Test",
            "user_type": "lojista"
        }
        
        success, status, data = self.make_request('POST', '/api/auth/google', lojista_auth)
        if success and 'token' in data:
            self.lojista_token = data['token']
            self.lojista_user = data['user']
            print(f"   ✅ Lojista authenticated: {data['user']['name']}")
        else:
            print(f"   ❌ Lojista authentication failed: {status} - {data}")
            return False
        
        # Authenticate motoboy
        motoboy_auth = {
            "email": "motoboy.pin@srboy.com",
            "name": "Motoboy PIN Test",
            "user_type": "motoboy"
        }
        
        success, status, data = self.make_request('POST', '/api/auth/google', motoboy_auth)
        if success and 'token' in data:
            self.motoboy_token = data['token']
            self.motoboy_user = data['user']
            print(f"   ✅ Motoboy authenticated: {data['user']['name']}")
        else:
            print(f"   ❌ Motoboy authentication failed: {status} - {data}")
            return False
        
        # Update motoboy location for delivery matching
        location_data = {"lat": -23.5320, "lng": -47.1360}
        success, status, data = self.make_request('PUT', '/api/motoboy/location', location_data, self.motoboy_token)
        if success:
            print(f"   ✅ Motoboy location updated")
        else:
            print(f"   ❌ Failed to update motoboy location: {status} - {data}")
            return False
        
        return True

    def test_create_delivery(self):
        """Step 1: Create delivery as lojista"""
        if not self.lojista_token:
            self.log_test("Create Delivery", False, "No lojista token available")
            return False

        delivery_data = {
            "pickup_address": {
                "lat": -23.5320,
                "lng": -47.1360,
                "address": "Rua das Flores, 123, São Roque",
                "city": "São Roque"
            },
            "delivery_address": {
                "lat": -23.5450,
                "lng": -47.1680,
                "address": "Av. Principal, 456, São Roque",
                "city": "São Roque"
            },
            "recipient_info": {
                "name": "João Silva",
                "rg": "12.345.678-9"
            },
            "description": "Teste de entrega com PIN",
            "product_description": "Produto de teste para validação de PIN"
        }
        
        success, status, data = self.make_request('POST', '/api/deliveries', delivery_data, self.lojista_token)
        
        if success and 'delivery' in data:
            self.test_delivery_id = data['delivery']['id']
            details = f"Delivery created - ID: {self.test_delivery_id}, Status: {data['delivery']['status']}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Create Delivery", success, details)
        return success

    def test_accept_delivery_generates_pin(self):
        """Step 2: Motoboy accepts delivery and PIN is generated"""
        if not self.motoboy_token or not self.test_delivery_id:
            self.log_test("Accept Delivery - PIN Generation", False, "No motoboy token or delivery ID available")
            return False

        success, status, data = self.make_request('POST', f'/api/deliveries/{self.test_delivery_id}/accept', token=self.motoboy_token)
        
        if success and 'pin_confirmacao' in data:
            self.generated_pin = data['pin_confirmacao']
            details = f"Delivery accepted - PIN generated: {self.generated_pin} (4 digits)"
            
            # Verify PIN is 4 characters
            if len(self.generated_pin) == 4:
                details += " ✓ PIN length correct"
            else:
                success = False
                details += f" ✗ PIN length incorrect: {len(self.generated_pin)} chars"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Accept Delivery - PIN Generation", success, details)
        return success

    def test_delivery_finalization_without_pin(self):
        """Step 3: Try to finalize delivery without validating PIN (should fail)"""
        if not self.motoboy_token or not self.test_delivery_id:
            self.log_test("Finalize Without PIN", False, "No motoboy token or delivery ID available")
            return False

        status_data = {"status": "delivered"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{self.test_delivery_id}/status', status_data, self.motoboy_token, expected_status=400)
        
        if status == 400 and "PIN de confirmação deve ser validado" in data.get('detail', ''):
            success = True
            details = "Correctly blocked delivery finalization without PIN validation"
        else:
            success = False
            details = f"Expected 400 with PIN validation error, got {status}: {data}"
        
        self.log_test("Finalize Without PIN", success, details)
        return success

    def test_pin_validation_incorrect_attempts(self):
        """Step 4: Test PIN validation with incorrect attempts"""
        if not self.motoboy_token or not self.test_delivery_id or not self.generated_pin:
            self.log_test("PIN Validation - Incorrect Attempts", False, "Missing required data")
            return False

        # First incorrect attempt
        pin_data = {"pin": "XXXX"}
        success, status, data = self.make_request('POST', f'/api/deliveries/{self.test_delivery_id}/validate-pin', pin_data, self.motoboy_token)
        
        if success and data.get('success') == False and data.get('attempts') == 1:
            details = f"First incorrect attempt handled correctly - Attempts: {data.get('attempts')}, Remaining: {data.get('remaining')}"
        else:
            self.log_test("PIN Validation - Incorrect Attempts", False, f"First attempt failed: {data}")
            return False

        # Second incorrect attempt
        pin_data = {"pin": "YYYY"}
        success, status, data = self.make_request('POST', f'/api/deliveries/{self.test_delivery_id}/validate-pin', pin_data, self.motoboy_token)
        
        if success and data.get('success') == False and data.get('attempts') == 2:
            details += f" | Second attempt: Attempts: {data.get('attempts')}, Remaining: {data.get('remaining')}"
        else:
            self.log_test("PIN Validation - Incorrect Attempts", False, f"Second attempt failed: {data}")
            return False

        self.log_test("PIN Validation - Incorrect Attempts", True, details)
        return True

    def test_pin_validation_correct(self):
        """Step 5: Test PIN validation with correct PIN"""
        if not self.motoboy_token or not self.test_delivery_id or not self.generated_pin:
            self.log_test("PIN Validation - Correct PIN", False, "Missing required data")
            return False

        pin_data = {"pin": self.generated_pin}
        success, status, data = self.make_request('POST', f'/api/deliveries/{self.test_delivery_id}/validate-pin', pin_data, self.motoboy_token)
        
        if success and data.get('success') == True and data.get('can_complete_delivery') == True:
            details = f"PIN validated successfully - Code: {data.get('code')}, Message: {data.get('message')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("PIN Validation - Correct PIN", success, details)
        return success

    def test_delivery_finalization_after_pin(self):
        """Step 6: Finalize delivery after PIN validation (should work)"""
        if not self.motoboy_token or not self.test_delivery_id:
            self.log_test("Finalize After PIN", False, "No motoboy token or delivery ID available")
            return False

        status_data = {"status": "delivered"}
        success, status, data = self.make_request('PUT', f'/api/deliveries/{self.test_delivery_id}/status', status_data, self.motoboy_token)
        
        if success:
            details = f"Delivery finalized successfully after PIN validation - {data.get('message')}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test("Finalize After PIN", success, details)
        return success

    def test_pin_blocking_after_three_attempts(self):
        """Test PIN blocking after 3 incorrect attempts"""
        # Create a new delivery for this test
        if not self.lojista_token or not self.motoboy_token:
            self.log_test("PIN Blocking Test", False, "Missing authentication tokens")
            return False

        # Create new delivery
        delivery_data = {
            "pickup_address": {
                "lat": -23.5320,
                "lng": -47.1360,
                "address": "Rua de Teste, 789, São Roque",
                "city": "São Roque"
            },
            "delivery_address": {
                "lat": -23.5450,
                "lng": -47.1680,
                "address": "Av. de Teste, 101, São Roque",
                "city": "São Roque"
            },
            "recipient_info": {
                "name": "Maria Santos",
                "rg": "98.765.432-1"
            },
            "description": "Teste de bloqueio de PIN"
        }
        
        success, status, data = self.make_request('POST', '/api/deliveries', delivery_data, self.lojista_token)
        if not success:
            self.log_test("PIN Blocking Test", False, f"Failed to create test delivery: {data}")
            return False
        
        test_delivery_id = data['delivery']['id']
        
        # Accept delivery to generate PIN
        success, status, data = self.make_request('POST', f'/api/deliveries/{test_delivery_id}/accept', token=self.motoboy_token)
        if not success:
            self.log_test("PIN Blocking Test", False, f"Failed to accept test delivery: {data}")
            return False
        
        # Make 3 incorrect attempts
        for attempt in range(1, 4):
            pin_data = {"pin": f"ERR{attempt}"}
            success, status, data = self.make_request('POST', f'/api/deliveries/{test_delivery_id}/validate-pin', pin_data, self.motoboy_token)
            
            if attempt < 3:
                if not (success and data.get('success') == False and data.get('attempts') == attempt):
                    self.log_test("PIN Blocking Test", False, f"Attempt {attempt} failed: {data}")
                    return False
            else:
                # Third attempt should block the PIN
                if success and data.get('success') == False and data.get('code') == 'PIN_BLOCKED':
                    details = f"PIN correctly blocked after 3 attempts - Message: {data.get('message')}"
                else:
                    self.log_test("PIN Blocking Test", False, f"PIN not blocked after 3 attempts: {data}")
                    return False
        
        # Try one more attempt - should still be blocked
        pin_data = {"pin": "TEST"}
        success, status, data = self.make_request('POST', f'/api/deliveries/{test_delivery_id}/validate-pin', pin_data, self.motoboy_token)
        
        if success and data.get('success') == False and data.get('code') == 'PIN_BLOCKED':
            details += " | Subsequent attempts correctly blocked"
        else:
            self.log_test("PIN Blocking Test", False, f"PIN not staying blocked: {data}")
            return False
        
        self.log_test("PIN Blocking Test", True, details)
        return True

    def test_pin_data_structure(self):
        """Test PIN data structure in database"""
        if not self.test_delivery_id or not self.motoboy_token:
            self.log_test("PIN Data Structure", False, "Missing delivery ID or token")
            return False

        # Get delivery details to check PIN structure
        success, status, data = self.make_request('GET', '/api/deliveries', token=self.motoboy_token)
        
        if not success:
            self.log_test("PIN Data Structure", False, f"Failed to get deliveries: {data}")
            return False
        
        # Find our test delivery
        test_delivery = None
        for delivery in data.get('deliveries', []):
            if delivery['id'] == self.test_delivery_id:
                test_delivery = delivery
                break
        
        if not test_delivery:
            self.log_test("PIN Data Structure", False, "Test delivery not found")
            return False
        
        # Check PIN fields exist
        required_fields = ['pin_completo', 'pin_confirmacao', 'pin_tentativas', 'pin_bloqueado']
        missing_fields = []
        
        for field in required_fields:
            if field not in test_delivery:
                missing_fields.append(field)
        
        if missing_fields:
            self.log_test("PIN Data Structure", False, f"Missing PIN fields: {missing_fields}")
            return False
        
        # Validate PIN structure
        pin_completo = test_delivery.get('pin_completo', '')
        pin_confirmacao = test_delivery.get('pin_confirmacao', '')
        
        details = f"PIN structure verified - Full PIN: {len(pin_completo)} chars, Confirmation: {len(pin_confirmacao)} chars"
        
        # Check PIN lengths
        if len(pin_completo) != 8:
            self.log_test("PIN Data Structure", False, f"PIN completo should be 8 chars, got {len(pin_completo)}")
            return False
        
        if len(pin_confirmacao) != 4:
            self.log_test("PIN Data Structure", False, f"PIN confirmacao should be 4 chars, got {len(pin_confirmacao)}")
            return False
        
        # Check that confirmation PIN is last 4 digits of full PIN
        if pin_confirmacao != pin_completo[-4:]:
            self.log_test("PIN Data Structure", False, f"PIN confirmacao should be last 4 digits of full PIN")
            return False
        
        details += " | PIN confirmation is last 4 digits of full PIN ✓"
        
        self.log_test("PIN Data Structure", True, details)
        return True

    def run_pin_tests(self):
        """Run all PIN system tests"""
        print("🔐 Starting SrBoy PIN Confirmation System Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        print("\n📋 PIN System Flow Tests")
        print("-" * 30)
        
        # Test the complete PIN flow
        tests = [
            self.test_create_delivery,
            self.test_accept_delivery_generates_pin,
            self.test_delivery_finalization_without_pin,
            self.test_pin_validation_incorrect_attempts,
            self.test_pin_validation_correct,
            self.test_delivery_finalization_after_pin,
            self.test_pin_blocking_after_three_attempts,
            self.test_pin_data_structure
        ]
        
        for test in tests:
            if not test():
                print(f"\n❌ Test failed, stopping PIN system tests")
                break
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 PIN Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All PIN system tests passed! PIN confirmation system is working correctly.")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed. Check the issues above.")
            return False

def main():
    """Main test execution"""
    tester = PINSystemTester()
    success = tester.run_pin_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())