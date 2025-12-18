#!/usr/bin/env python3
"""
Focused Backend Test for Enhanced DACFI-List Feature
Tests core functionality with proper cleanup
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://itemfinder-30.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "test.dac@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_ROLE = "DAC"

class FocusedTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        if details:
            logger.info(f"    Details: {details}")
    
    async def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None):
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if self.auth_token:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if headers:
            request_headers.update(headers)
        
        try:
            async with self.session.request(
                method, url, 
                json=data if data else None,
                headers=request_headers
            ) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                return {
                    "status": response.status,
                    "data": response_data,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            return {
                "status": 0,
                "data": {"error": str(e)},
                "headers": {}
            }
    
    async def authenticate(self):
        """Authenticate with test credentials"""
        logger.info("🔐 Authenticating...")
        
        response = await self.make_request("POST", "/auth/login", {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": TEST_ROLE
        })
        
        if response["status"] == 200:
            self.auth_token = response["data"]["access_token"]
            self.user_data = response["data"]["user"]
            self.log_result("Authentication", True, f"Successfully authenticated as {TEST_EMAIL}")
            return True
        else:
            self.log_result("Authentication", False, f"Failed to authenticate: {response['data']}")
            return False
    
    async def run_focused_tests(self):
        """Run focused tests on key functionality"""
        logger.info("🎯 Starting Focused Enhanced DACFI-List Tests")
        
        # 1. Test Categories Endpoint
        logger.info("📋 Testing categories endpoint...")
        response = await self.make_request("GET", "/categories")
        
        if response["status"] == 200:
            categories = response["data"].get("categories", [])
            if len(categories) == 20 and "Miscellaneous" in categories:
                self.log_result("Categories Endpoint", True, f"✅ Returns 20 categories including 'Miscellaneous'")
            else:
                self.log_result("Categories Endpoint", False, f"❌ Expected 20 categories, got {len(categories)}")
        else:
            self.log_result("Categories Endpoint", False, f"❌ Failed with status {response['status']}")
        
        # 2. Test Add Favorite Item with Categorization
        logger.info("➕ Testing add favorite item with categorization...")
        test_item = "Organic 2% Milk"
        response = await self.make_request("POST", "/favorites/items", {"item_name": test_item})
        
        if response["status"] == 200:
            item = response["data"]["item"]
            category = item.get("category")
            attributes = item.get("attributes", {})
            
            if category == "Dairy & Eggs" and attributes.get("organic", False):
                self.log_result("Add Favorite Item", True, f"✅ Successfully added '{test_item}' to '{category}' with organic attribute")
            else:
                self.log_result("Add Favorite Item", False, f"❌ Wrong categorization: {category}, attributes: {attributes}")
        else:
            self.log_result("Add Favorite Item", False, f"❌ Failed with status {response['status']}: {response['data']}")
        
        # 3. Test Get Favorite Items (Organization by Category)
        logger.info("📖 Testing get favorite items...")
        response = await self.make_request("GET", "/favorites/items")
        
        if response["status"] == 200:
            data = response["data"]
            items_by_category = data.get("items_by_category", {})
            total_items = data.get("total_items", 0)
            
            if "Dairy & Eggs" in items_by_category and total_items > 0:
                self.log_result("Get Favorite Items", True, f"✅ Retrieved {total_items} items organized by category")
            else:
                self.log_result("Get Favorite Items", False, f"❌ Items not properly organized: {items_by_category}")
        else:
            self.log_result("Get Favorite Items", False, f"❌ Failed with status {response['status']}")
        
        # 4. Test Duplicate Item Handling
        logger.info("🔄 Testing duplicate item handling...")
        response = await self.make_request("POST", "/favorites/items", {"item_name": test_item})
        
        if response["status"] == 400:
            self.log_result("Duplicate Item Handling", True, "✅ Correctly rejected duplicate item")
        else:
            self.log_result("Duplicate Item Handling", False, f"❌ Expected 400, got {response['status']}")
        
        # 5. Test Delete Favorite Item
        logger.info("🗑️ Testing delete favorite item...")
        response = await self.make_request("DELETE", "/favorites/items", {"item_name": test_item})
        
        if response["status"] == 200:
            self.log_result("Delete Favorite Item", True, f"✅ Successfully deleted '{test_item}'")
        else:
            self.log_result("Delete Favorite Item", False, f"❌ Failed with status {response['status']}: {response['data']}")
        
        # 6. Test Auto-Add Threshold Settings
        logger.info("⚙️ Testing auto-add threshold settings...")
        for threshold in [0, 3, 6]:
            response = await self.make_request("PUT", "/users/settings/auto-threshold", {
                "auto_favorite_threshold": threshold
            })
            
            if response["status"] == 200:
                self.log_result(f"Auto Threshold {threshold}", True, f"✅ Set threshold to {threshold}")
            else:
                self.log_result(f"Auto Threshold {threshold}", False, f"❌ Failed to set threshold {threshold}")
        
        # 7. Test Invalid Threshold
        logger.info("🚫 Testing invalid threshold...")
        response = await self.make_request("PUT", "/users/settings/auto-threshold", {
            "auto_favorite_threshold": 5  # Invalid
        })
        
        if response["status"] == 400:
            self.log_result("Invalid Threshold", True, "✅ Correctly rejected invalid threshold")
        else:
            self.log_result("Invalid Threshold", False, f"❌ Expected 400, got {response['status']}")
        
        # 8. Test Categorization Accuracy
        logger.info("🏷️ Testing categorization accuracy...")
        test_cases = [
            {"item": "Fresh Spinach", "expected": "Vegetables"},
            {"item": "Gluten-Free Pasta", "expected": "Pasta, Rice & Grains"},
            {"item": "Apple Juice", "expected": "Beverages"}
        ]
        
        for case in test_cases:
            response = await self.make_request("POST", "/favorites/items", {"item_name": case["item"]})
            
            if response["status"] == 200:
                category = response["data"]["item"]["category"]
                if category == case["expected"]:
                    self.log_result(f"Categorization {case['item']}", True, f"✅ Correctly categorized as '{category}'")
                else:
                    self.log_result(f"Categorization {case['item']}", False, f"❌ Expected '{case['expected']}', got '{category}'")
            else:
                self.log_result(f"Categorization {case['item']}", False, f"❌ Failed to add item")
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 FOCUSED TEST SUMMARY")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test']}: {result['message']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "results": self.test_results
        }

async def main():
    """Main test runner"""
    async with FocusedTester() as tester:
        # Authenticate
        if not await tester.authenticate():
            logger.error("❌ Authentication failed - stopping tests")
            return False
        
        # Run tests
        results = await tester.run_focused_tests()
        
        # Save results
        with open("/app/focused_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📁 Test results saved to /app/focused_test_results.json")
        
        return results["failed"] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)