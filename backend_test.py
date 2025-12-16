#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Enhanced DACFI-List Feature
Tests item-level favorites system with auto-categorization and implicit auto-add functionality.
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://surplus-shop-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials - Using provided credentials from review request
TEST_EMAIL = "alfred.toussaint@gmail.com"
TEST_PASSWORD = "TestPassword123"
TEST_ROLE = "DAC"

class BackendTester:
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
        logger.info("🔐 Authenticating with test credentials...")
        
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
    
    async def test_categories_endpoint(self):
        """Test /api/categories endpoint returns 20 categories"""
        logger.info("📋 Testing categories endpoint...")
        
        response = await self.make_request("GET", "/categories")
        
        if response["status"] == 200:
            categories = response["data"].get("categories", [])
            expected_count = 20
            
            if len(categories) == expected_count and "Miscellaneous" in categories:
                self.log_result(
                    "Categories Endpoint", True, 
                    f"Returns {len(categories)} categories including 'Miscellaneous'",
                    {"categories": categories}
                )
            else:
                self.log_result(
                    "Categories Endpoint", False,
                    f"Expected {expected_count} categories with 'Miscellaneous', got {len(categories)}",
                    {"categories": categories}
                )
        else:
            self.log_result("Categories Endpoint", False, f"Failed with status {response['status']}")
    
    async def test_add_favorite_items(self):
        """Test POST /api/favorites/items - Add explicit favorite items"""
        logger.info("➕ Testing add favorite items...")
        
        test_items = [
            {"item_name": "Organic 2% Milk", "expected_category": "Dairy & Eggs"},
            {"item_name": "Granola", "expected_category": "Breakfast & Cereal"},
            {"item_name": "Honeycrisp Apples", "expected_category": "Fruits"},
            {"item_name": "Gluten-Free Bread", "expected_category": "Bakery & Bread"}
        ]
        
        for item in test_items:
            response = await self.make_request("POST", "/favorites/items", {
                "item_name": item["item_name"]
            })
            
            if response["status"] == 200:
                returned_item = response["data"]["item"]
                category = returned_item.get("category")
                attributes = returned_item.get("attributes", {})
                
                # Check categorization
                category_correct = category == item["expected_category"]
                
                # Check attribute detection
                organic_detected = "organic" in item["item_name"].lower() and attributes.get("organic", False)
                gluten_free_detected = "gluten-free" in item["item_name"].lower() and attributes.get("gluten_free", False)
                
                if category_correct:
                    self.log_result(
                        f"Add Favorite Item - {item['item_name']}", True,
                        f"Successfully added and categorized as '{category}'",
                        {
                            "item": returned_item,
                            "organic_detected": organic_detected,
                            "gluten_free_detected": gluten_free_detected
                        }
                    )
                else:
                    self.log_result(
                        f"Add Favorite Item - {item['item_name']}", False,
                        f"Wrong category: expected '{item['expected_category']}', got '{category}'",
                        {"item": returned_item}
                    )
            else:
                self.log_result(
                    f"Add Favorite Item - {item['item_name']}", False,
                    f"Failed with status {response['status']}: {response['data']}"
                )
    
    async def test_duplicate_favorite_item(self):
        """Test adding duplicate item returns 400 error"""
        logger.info("🔄 Testing duplicate favorite item handling...")
        
        # Try to add "Organic 2% Milk" again
        response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Organic 2% Milk"
        })
        
        if response["status"] == 400:
            self.log_result(
                "Duplicate Favorite Item", True,
                "Correctly rejected duplicate item with 400 error",
                {"response": response["data"]}
            )
        else:
            self.log_result(
                "Duplicate Favorite Item", False,
                f"Expected 400 error, got {response['status']}: {response['data']}"
            )
    
    async def test_get_favorite_items(self):
        """Test GET /api/favorites/items - Get organized favorite items"""
        logger.info("📖 Testing get favorite items...")
        
        response = await self.make_request("GET", "/favorites/items")
        
        if response["status"] == 200:
            data = response["data"]
            items_by_category = data.get("items_by_category", {})
            total_items = data.get("total_items", 0)
            
            # Check organization by category
            has_dairy = "Dairy & Eggs" in items_by_category
            has_breakfast = "Breakfast & Cereal" in items_by_category
            has_fruits = "Fruits" in items_by_category
            
            # Check explicit vs implicit distinction
            explicit_items = []
            implicit_items = []
            
            for category, items in items_by_category.items():
                for item in items:
                    if item.get("auto_added_date") is None:
                        explicit_items.append(item)
                    else:
                        implicit_items.append(item)
            
            self.log_result(
                "Get Favorite Items", True,
                f"Retrieved {total_items} items organized by category",
                {
                    "categories": list(items_by_category.keys()),
                    "explicit_items": len(explicit_items),
                    "implicit_items": len(implicit_items),
                    "sample_items": {k: v[:2] for k, v in items_by_category.items()}  # First 2 items per category
                }
            )
        else:
            self.log_result(
                "Get Favorite Items", False,
                f"Failed with status {response['status']}: {response['data']}"
            )
    
    async def test_delete_favorite_item(self):
        """Test DELETE /api/favorites/items - Remove favorite item"""
        logger.info("🗑️ Testing delete favorite item...")
        
        # Delete "Organic 2% Milk"
        response = await self.make_request("DELETE", "/favorites/items", {
            "item_name": "Organic 2% Milk"
        })
        
        if response["status"] == 200:
            self.log_result(
                "Delete Favorite Item", True,
                "Successfully deleted 'Organic 2% Milk'",
                {"response": response["data"]}
            )
        else:
            self.log_result(
                "Delete Favorite Item", False,
                f"Failed with status {response['status']}: {response['data']}"
            )
    
    async def test_delete_nonexistent_item(self):
        """Test deleting non-existent item returns 404"""
        logger.info("❌ Testing delete non-existent item...")
        
        response = await self.make_request("DELETE", "/favorites/items", {
            "item_name": "Non-Existent Item"
        })
        
        if response["status"] == 404:
            self.log_result(
                "Delete Non-Existent Item", True,
                "Correctly returned 404 for non-existent item",
                {"response": response["data"]}
            )
        else:
            self.log_result(
                "Delete Non-Existent Item", False,
                f"Expected 404, got {response['status']}: {response['data']}"
            )
    
    async def test_auto_threshold_settings(self):
        """Test PUT /api/users/settings/auto-threshold - Update auto-add threshold"""
        logger.info("⚙️ Testing auto-add threshold settings...")
        
        valid_thresholds = [0, 3, 6]
        
        for threshold in valid_thresholds:
            response = await self.make_request("PUT", "/users/settings/auto-threshold", {
                "auto_favorite_threshold": threshold
            })
            
            if response["status"] == 200:
                self.log_result(
                    f"Auto Threshold - {threshold}", True,
                    f"Successfully set threshold to {threshold}",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    f"Auto Threshold - {threshold}", False,
                    f"Failed with status {response['status']}: {response['data']}"
                )
    
    async def test_invalid_auto_threshold(self):
        """Test invalid auto-add threshold returns 400"""
        logger.info("🚫 Testing invalid auto-add threshold...")
        
        response = await self.make_request("PUT", "/users/settings/auto-threshold", {
            "auto_favorite_threshold": 5  # Invalid value
        })
        
        if response["status"] == 400:
            self.log_result(
                "Invalid Auto Threshold", True,
                "Correctly rejected invalid threshold with 400 error",
                {"response": response["data"]}
            )
        else:
            self.log_result(
                "Invalid Auto Threshold", False,
                f"Expected 400 error, got {response['status']}: {response['data']}"
            )
    
    async def test_unauthenticated_access(self):
        """Test endpoints without authentication return 401/403"""
        logger.info("🔒 Testing unauthenticated access...")
        
        # Temporarily remove auth token
        original_token = self.auth_token
        self.auth_token = None
        
        response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Test Item"
        })
        
        # Restore auth token
        self.auth_token = original_token
        
        if response["status"] in [401, 403]:
            self.log_result(
                "Unauthenticated Access", True,
                f"Correctly rejected unauthenticated request with {response['status']}",
                {"response": response["data"]}
            )
        else:
            self.log_result(
                "Unauthenticated Access", False,
                f"Expected 401/403, got {response['status']}: {response['data']}"
            )
    
    async def test_categorization_logic(self):
        """Test categorization accuracy for various items"""
        logger.info("🏷️ Testing categorization logic...")
        
        test_cases = [
            {"item": "Organic Spinach", "expected": "Vegetables"},
            {"item": "Chocolate Chip Cookies", "expected": "Snacks & Candy"},
            {"item": "Frozen Pizza", "expected": "Frozen Foods"},
            {"item": "Orange Juice", "expected": "Beverages"},
            {"item": "Olive Oil", "expected": "Oils, Sauces & Spices"}
        ]
        
        for case in test_cases:
            response = await self.make_request("POST", "/favorites/items", {
                "item_name": case["item"]
            })
            
            if response["status"] == 200:
                category = response["data"]["item"]["category"]
                if category == case["expected"]:
                    self.log_result(
                        f"Categorization - {case['item']}", True,
                        f"Correctly categorized as '{category}'",
                        {"item": response["data"]["item"]}
                    )
                else:
                    self.log_result(
                        f"Categorization - {case['item']}", False,
                        f"Expected '{case['expected']}', got '{category}'",
                        {"item": response["data"]["item"]}
                    )
            else:
                self.log_result(
                    f"Categorization - {case['item']}", False,
                    f"Failed to add item: {response['data']}"
                )
    
    async def run_all_tests(self):
        """Run all backend tests"""
        logger.info("🚀 Starting Enhanced DACFI-List Backend Tests")
        logger.info(f"Backend URL: {API_BASE}")
        
        # Authentication
        if not await self.authenticate():
            logger.error("❌ Authentication failed - stopping tests")
            return
        
        # Run all tests
        await self.test_categories_endpoint()
        await self.test_add_favorite_items()
        await self.test_duplicate_favorite_item()
        await self.test_get_favorite_items()
        await self.test_delete_favorite_item()
        await self.test_delete_nonexistent_item()
        await self.test_auto_threshold_settings()
        await self.test_invalid_auto_threshold()
        await self.test_unauthenticated_access()
        await self.test_categorization_logic()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 TEST SUMMARY")
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
    async with BackendTester() as tester:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("/app/test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📁 Test results saved to /app/test_results.json")
        
        return results["failed"] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)