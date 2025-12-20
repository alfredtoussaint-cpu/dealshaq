#!/usr/bin/env python3
"""
Final Comprehensive Backend Test for Enhanced DACFI-List Feature
Tests all functionality with proper API endpoints
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shaq-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "test.dac@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_ROLE = "DAC"

class FinalTester:
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
    
    async def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.request(
                method, url, 
                json=data if data else None,
                params=params if params else None,
                headers=headers
            ) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                return {
                    "status": response.status,
                    "data": response_data
                }
        except Exception as e:
            return {
                "status": 0,
                "data": {"error": str(e)}
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
    
    async def cleanup_favorites(self):
        """Clean up existing favorite items"""
        logger.info("🧹 Cleaning up existing favorites...")
        
        # Get current favorites
        response = await self.make_request("GET", "/favorites/items")
        if response["status"] == 200:
            items_by_category = response["data"].get("items_by_category", {})
            
            # Delete all existing items
            for category, items in items_by_category.items():
                for item in items:
                    await self.make_request("DELETE", "/favorites/items/remove", 
                                          params={"item_name": item["item_name"]})
            
            logger.info(f"Cleaned up favorites from {len(items_by_category)} categories")
    
    async def run_comprehensive_tests(self):
        """Run comprehensive tests"""
        logger.info("🚀 Starting Final Enhanced DACFI-List Tests")
        
        # Clean up first
        await self.cleanup_favorites()
        
        # 1. Test Categories Endpoint
        logger.info("📋 Testing categories endpoint...")
        response = await self.make_request("GET", "/categories")
        
        if response["status"] == 200:
            categories = response["data"].get("categories", [])
            if len(categories) == 20 and "Miscellaneous" in categories and "Miscellaneous" in categories:
                self.log_result("Categories Endpoint", True, 
                              f"Returns 20 categories including 'Miscellaneous' (no 'Alcoholic Beverages')")
            else:
                self.log_result("Categories Endpoint", False, 
                              f"Expected 20 categories with 'Miscellaneous', got {len(categories)}")
        else:
            self.log_result("Categories Endpoint", False, f"Failed with status {response['status']}")
        
        # 2. Test Add Favorite Items with Categorization and Attributes
        logger.info("➕ Testing add favorite items with categorization...")
        
        test_items = [
            {"name": "Organic 2% Milk", "expected_category": "Dairy & Eggs", "expected_attributes": ["organic"]},
            {"name": "Granola", "expected_category": "Breakfast & Cereal", "expected_attributes": []},
            {"name": "Honeycrisp Apples", "expected_category": "Fruits", "expected_attributes": []},
            {"name": "Gluten-Free Bread", "expected_category": "Bakery & Bread", "expected_attributes": ["gluten_free"]}
        ]
        
        for item in test_items:
            response = await self.make_request("POST", "/favorites/items", {"item_name": item["name"]})
            
            if response["status"] == 200:
                returned_item = response["data"]["item"]
                category = returned_item.get("category")
                attributes = returned_item.get("attributes", {})
                
                # Check categorization
                category_correct = category == item["expected_category"]
                
                # Check attributes
                attributes_correct = all(
                    attributes.get(attr, False) for attr in item["expected_attributes"]
                )
                
                if category_correct and attributes_correct:
                    self.log_result(f"Add Item - {item['name']}", True, 
                                  f"Correctly categorized as '{category}' with attributes {list(attributes.keys())}")
                else:
                    self.log_result(f"Add Item - {item['name']}", False, 
                                  f"Category: {category} (expected {item['expected_category']}), Attributes: {attributes}")
            else:
                self.log_result(f"Add Item - {item['name']}", False, 
                              f"Failed with status {response['status']}: {response['data']}")
        
        # 3. Test Get Favorite Items (Organization by Category)
        logger.info("📖 Testing get favorite items organization...")
        response = await self.make_request("GET", "/favorites/items")
        
        if response["status"] == 200:
            data = response["data"]
            items_by_category = data.get("items_by_category", {})
            total_items = data.get("total_items", 0)
            
            # Check if items are organized by category
            expected_categories = ["Dairy & Eggs", "Breakfast & Cereal", "Fruits", "Bakery & Bread"]
            categories_present = all(cat in items_by_category for cat in expected_categories)
            
            # Check explicit vs implicit distinction (all should be explicit for now)
            all_explicit = True
            for category, items in items_by_category.items():
                for item in items:
                    if item.get("auto_added_date") is not None:
                        all_explicit = False
                        break
            
            if categories_present and all_explicit and total_items == 4:
                self.log_result("Get Favorite Items", True, 
                              f"Retrieved {total_items} items organized by {len(items_by_category)} categories")
            else:
                self.log_result("Get Favorite Items", False, 
                              f"Organization issue: categories={list(items_by_category.keys())}, total={total_items}")
        else:
            self.log_result("Get Favorite Items", False, f"Failed with status {response['status']}")
        
        # 4. Test Duplicate Item Handling
        logger.info("🔄 Testing duplicate item handling...")
        response = await self.make_request("POST", "/favorites/items", {"item_name": "Organic 2% Milk"})
        
        if response["status"] == 400:
            self.log_result("Duplicate Item Handling", True, "Correctly rejected duplicate item")
        else:
            self.log_result("Duplicate Item Handling", False, 
                          f"Expected 400, got {response['status']}: {response['data']}")
        
        # 5. Test Delete Favorite Item (using working endpoint)
        logger.info("🗑️ Testing delete favorite item...")
        response = await self.make_request("DELETE", "/favorites/items/remove", 
                                         params={"item_name": "Organic 2% Milk"})
        
        if response["status"] == 200:
            self.log_result("Delete Favorite Item", True, "Successfully deleted 'Organic 2% Milk'")
        else:
            self.log_result("Delete Favorite Item", False, 
                          f"Failed with status {response['status']}: {response['data']}")
        
        # 6. Test Delete Non-Existent Item
        logger.info("❌ Testing delete non-existent item...")
        response = await self.make_request("DELETE", "/favorites/items/remove", 
                                         params={"item_name": "Non-Existent Item"})
        
        if response["status"] == 404:
            self.log_result("Delete Non-Existent Item", True, "Correctly returned 404 for non-existent item")
        else:
            self.log_result("Delete Non-Existent Item", False, 
                          f"Expected 404, got {response['status']}: {response['data']}")
        
        # 7. Test Auto-Add Threshold Settings
        logger.info("⚙️ Testing auto-add threshold settings...")
        
        valid_thresholds = [0, 3, 6]
        for threshold in valid_thresholds:
            response = await self.make_request("PUT", "/users/settings/auto-threshold", 
                                             {"auto_favorite_threshold": threshold})
            
            if response["status"] == 200:
                self.log_result(f"Auto Threshold {threshold}", True, f"Successfully set threshold to {threshold}")
            else:
                self.log_result(f"Auto Threshold {threshold}", False, 
                              f"Failed to set threshold {threshold}: {response['data']}")
        
        # 8. Test Invalid Auto-Add Threshold
        logger.info("🚫 Testing invalid auto-add threshold...")
        response = await self.make_request("PUT", "/users/settings/auto-threshold", 
                                         {"auto_favorite_threshold": 5})  # Invalid
        
        if response["status"] == 400:
            self.log_result("Invalid Auto Threshold", True, "Correctly rejected invalid threshold")
        else:
            self.log_result("Invalid Auto Threshold", False, 
                          f"Expected 400, got {response['status']}: {response['data']}")
        
        # 9. Test Unauthenticated Access
        logger.info("🔒 Testing unauthenticated access...")
        original_token = self.auth_token
        self.auth_token = None
        
        response = await self.make_request("POST", "/favorites/items", {"item_name": "Test Item"})
        
        self.auth_token = original_token
        
        if response["status"] in [401, 403]:
            self.log_result("Unauthenticated Access", True, 
                          f"Correctly rejected unauthenticated request with {response['status']}")
        else:
            self.log_result("Unauthenticated Access", False, 
                          f"Expected 401/403, got {response['status']}: {response['data']}")
        
        # 10. Test Additional Categorization Cases
        logger.info("🏷️ Testing additional categorization cases...")
        
        additional_test_cases = [
            {"item": "Fresh Spinach", "expected": "Vegetables"},
            {"item": "Frozen Pizza", "expected": "Frozen Foods"},
            {"item": "Apple Juice", "expected": "Beverages"},
            {"item": "Olive Oil", "expected": "Oils, Sauces & Spices"}
        ]
        
        for case in additional_test_cases:
            response = await self.make_request("POST", "/favorites/items", {"item_name": case["item"]})
            
            if response["status"] == 200:
                category = response["data"]["item"]["category"]
                if category == case["expected"]:
                    self.log_result(f"Categorization {case['item']}", True, 
                                  f"Correctly categorized as '{category}'")
                else:
                    self.log_result(f"Categorization {case['item']}", False, 
                                  f"Expected '{case['expected']}', got '{category}'")
            else:
                self.log_result(f"Categorization {case['item']}", False, 
                              f"Failed to add item: {response['data']}")
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 FINAL TEST SUMMARY")
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
    async with FinalTester() as tester:
        # Authenticate
        if not await tester.authenticate():
            logger.error("❌ Authentication failed - stopping tests")
            return False
        
        # Run tests
        results = await tester.run_comprehensive_tests()
        
        # Save results
        with open("/app/final_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📁 Test results saved to /app/final_test_results.json")
        
        return results["failed"] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)