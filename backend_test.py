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

# Test credentials - Using working test user
TEST_EMAIL = "test.brand.generic@example.com"
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
    
    async def test_delete_favorite_item_new_endpoint(self):
        """Test NEW POST /api/favorites/items/delete - Remove favorite item (FIXED ENDPOINT)"""
        logger.info("🗑️ Testing NEW delete favorite item endpoint (POST-based)...")
        
        # First add a test item to delete
        add_response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Test Granola"
        })
        
        if add_response["status"] != 200:
            self.log_result(
                "Delete Favorite Item (NEW) - Setup", False,
                f"Failed to add test item: {add_response['data']}"
            )
            return
        
        # Now delete using the NEW POST endpoint
        response = await self.make_request("POST", "/favorites/items/delete", {
            "item_name": "Test Granola"
        })
        
        if response["status"] == 200:
            expected_message = "Favorite item removed"
            actual_message = response["data"].get("message", "")
            
            if expected_message in actual_message:
                self.log_result(
                    "Delete Favorite Item (NEW POST Endpoint)", True,
                    f"Successfully deleted 'Test Granola' using POST /api/favorites/items/delete",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "Delete Favorite Item (NEW POST Endpoint)", False,
                    f"Unexpected response message: {actual_message}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "Delete Favorite Item (NEW POST Endpoint)", False,
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
    
    async def test_brand_generic_parsing(self):
        """Test brand/generic parsing and storage - Core Feature"""
        logger.info("🏪 Testing brand/generic parsing and storage...")
        
        # Clear existing favorites first
        await self.clear_all_favorites()
        
        test_cases = [
            # Brand-specific items (with comma)
            {
                "input": "Quaker, Simply Granola",
                "expected_brand": "Quaker",
                "expected_generic": "Granola",
                "expected_has_brand": True,
                "expected_category": "Breakfast & Cereal",
                "description": "Brand-specific with modifier word removal"
            },
            {
                "input": "Valley Farm, 2% Milk",
                "expected_brand": "Valley Farm",
                "expected_generic": "2% Milk",
                "expected_has_brand": True,
                "expected_category": "Dairy & Eggs",
                "description": "Brand-specific with percentage"
            },
            {
                "input": "Quaker Simply, Granola",
                "expected_brand": "Quaker Simply",
                "expected_generic": "Granola",
                "expected_has_brand": True,
                "expected_category": "Breakfast & Cereal",
                "description": "Multi-word brand name"
            },
            # Generic items (no comma)
            {
                "input": "Granola",
                "expected_brand": None,
                "expected_generic": "Granola",
                "expected_has_brand": False,
                "expected_category": "Breakfast & Cereal",
                "description": "Generic item - any brand matches"
            },
            {
                "input": "Organic 2% Milk",
                "expected_brand": None,
                "expected_generic": "Organic 2% Milk",
                "expected_has_brand": False,
                "expected_category": "Dairy & Eggs",
                "description": "Generic with organic attribute"
            }
        ]
        
        for case in test_cases:
            response = await self.make_request("POST", "/favorites/items", {
                "item_name": case["input"]
            })
            
            if response["status"] == 200:
                item = response["data"]["item"]
                
                # Check all expected fields
                checks = {
                    "brand": item.get("brand") == case["expected_brand"],
                    "generic": item.get("generic") == case["expected_generic"],
                    "has_brand": item.get("has_brand") == case["expected_has_brand"],
                    "category": item.get("category") == case["expected_category"]
                }
                
                all_correct = all(checks.values())
                
                if all_correct:
                    self.log_result(
                        f"Brand/Generic Parsing - {case['input']}", True,
                        f"{case['description']} - All fields correct",
                        {
                            "item": item,
                            "expected": case,
                            "brand_keywords": item.get("brand_keywords", []),
                            "generic_keywords": item.get("generic_keywords", [])
                        }
                    )
                else:
                    failed_checks = [k for k, v in checks.items() if not v]
                    self.log_result(
                        f"Brand/Generic Parsing - {case['input']}", False,
                        f"Failed checks: {failed_checks}",
                        {
                            "item": item,
                            "expected": case,
                            "failed_checks": failed_checks
                        }
                    )
            else:
                self.log_result(
                    f"Brand/Generic Parsing - {case['input']}", False,
                    f"Failed to add item: {response['data']}"
                )
    
    async def test_smart_generic_extraction(self):
        """Test smart generic extraction removes modifier words correctly"""
        logger.info("🧠 Testing smart generic extraction...")
        
        test_cases = [
            {
                "input": "Quaker, Simply Granola",
                "expected_generic": "Granola",
                "description": "Remove 'Simply' modifier"
            },
            {
                "input": "Valley Farm, Fresh 2% Milk",
                "expected_generic": "2% Milk",
                "description": "Remove 'Fresh' but keep '2%'"
            },
            {
                "input": "Dannon, Light Greek Yogurt",
                "expected_generic": "Greek Yogurt",
                "description": "Remove 'Light' but keep 'Greek'"
            }
        ]
        
        for case in test_cases:
            response = await self.make_request("POST", "/favorites/items", {
                "item_name": case["input"]
            })
            
            if response["status"] == 200:
                item = response["data"]["item"]
                actual_generic = item.get("generic")
                
                if actual_generic == case["expected_generic"]:
                    self.log_result(
                        f"Smart Generic - {case['input']}", True,
                        f"{case['description']} - Got '{actual_generic}'",
                        {"item": item}
                    )
                else:
                    self.log_result(
                        f"Smart Generic - {case['input']}", False,
                        f"Expected '{case['expected_generic']}', got '{actual_generic}'",
                        {"item": item}
                    )
            else:
                self.log_result(
                    f"Smart Generic - {case['input']}", False,
                    f"Failed to add item: {response['data']}"
                )
    
    async def test_edge_cases(self):
        """Test edge cases in brand/generic parsing"""
        logger.info("⚠️ Testing edge cases...")
        
        test_cases = [
            {
                "input": "Quaker, Simply, Granola",
                "expected_brand": "Quaker",
                "expected_generic": "Simply, Granola",
                "description": "Multiple commas - split on first only"
            },
            {
                "input": "Quaker , Granola",
                "expected_brand": "Quaker",
                "expected_generic": "Granola",
                "description": "Spaces around comma should be trimmed"
            }
        ]
        
        for case in test_cases:
            response = await self.make_request("POST", "/favorites/items", {
                "item_name": case["input"]
            })
            
            if response["status"] == 200:
                item = response["data"]["item"]
                brand_correct = item.get("brand") == case["expected_brand"]
                generic_correct = item.get("generic") == case["expected_generic"]
                
                if brand_correct and generic_correct:
                    self.log_result(
                        f"Edge Case - {case['input']}", True,
                        f"{case['description']} - Parsed correctly",
                        {"item": item}
                    )
                else:
                    self.log_result(
                        f"Edge Case - {case['input']}", False,
                        f"Parsing failed - brand: {item.get('brand')}, generic: {item.get('generic')}",
                        {"item": item, "expected": case}
                    )
            else:
                self.log_result(
                    f"Edge Case - {case['input']}", False,
                    f"Failed to add item: {response['data']}"
                )
    
    async def test_organic_attribute_with_brand_matching(self):
        """Test organic attribute detection with brand matching"""
        logger.info("🌱 Testing organic attribute with brand matching...")
        
        # Add organic brand-specific favorite
        response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Quaker, Organic Granola"
        })
        
        if response["status"] == 200:
            item = response["data"]["item"]
            organic_detected = item.get("attributes", {}).get("organic", False)
            has_brand = item.get("has_brand", False)
            
            if organic_detected and has_brand:
                self.log_result(
                    "Organic Brand Favorite", True,
                    "Successfully added 'Quaker, Organic Granola' with organic=True and has_brand=True",
                    {"item": item}
                )
            else:
                self.log_result(
                    "Organic Brand Favorite", False,
                    f"Organic: {organic_detected}, Has Brand: {has_brand}",
                    {"item": item}
                )
        else:
            self.log_result(
                "Organic Brand Favorite", False,
                f"Failed to add organic brand favorite: {response['data']}"
            )
    
    async def clear_all_favorites(self):
        """Helper method to clear all favorites for clean testing"""
        logger.info("🧹 Clearing all existing favorites...")
        
        # Get current favorites
        response = await self.make_request("GET", "/favorites/items")
        if response["status"] == 200:
            items_by_category = response["data"].get("items_by_category", {})
            
            # Delete each item
            for category, items in items_by_category.items():
                for item in items:
                    item_name = item.get("item_name")
                    if item_name:
                        delete_response = await self.make_request(
                            "DELETE", "/favorites/items/remove", 
                            headers={}, 
                            data=None
                        )
                        # Use query parameter instead
                        delete_url = f"{API_BASE}/favorites/items/remove?item_name={item_name}"
                        async with self.session.delete(
                            delete_url,
                            headers={"Authorization": f"Bearer {self.auth_token}"}
                        ) as delete_resp:
                            pass  # Just clear it, don't check result
    
    async def simulate_rshd_matching_test(self):
        """Test the matching logic by simulating RSHD posts (conceptual test)"""
        logger.info("🎯 Testing matching logic concepts...")
        
        # This is a conceptual test since we can't easily simulate RSHD posts
        # We'll test the data structure and verify favorites are stored correctly for matching
        
        # Clear and add test favorites
        await self.clear_all_favorites()
        
        # Add brand-specific favorite
        brand_response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Quaker, Granola"
        })
        
        # Add generic favorite  
        generic_response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Yogurt"
        })
        
        if brand_response["status"] == 200 and generic_response["status"] == 200:
            brand_item = brand_response["data"]["item"]
            generic_item = generic_response["data"]["item"]
            
            # Verify brand-specific has correct structure for strict matching
            brand_has_keywords = bool(brand_item.get("brand_keywords"))
            brand_has_generic_keywords = bool(brand_item.get("generic_keywords"))
            brand_has_brand_flag = brand_item.get("has_brand") == True
            
            # Verify generic has correct structure for flexible matching
            generic_has_keywords = bool(generic_item.get("generic_keywords"))
            generic_no_brand_flag = generic_item.get("has_brand") == False
            
            if all([brand_has_keywords, brand_has_generic_keywords, brand_has_brand_flag, 
                   generic_has_keywords, generic_no_brand_flag]):
                self.log_result(
                    "Matching Logic Structure", True,
                    "Both brand-specific and generic favorites have correct structure for matching",
                    {
                        "brand_item": brand_item,
                        "generic_item": generic_item
                    }
                )
            else:
                self.log_result(
                    "Matching Logic Structure", False,
                    "Favorites missing required fields for matching logic",
                    {
                        "brand_checks": [brand_has_keywords, brand_has_generic_keywords, brand_has_brand_flag],
                        "generic_checks": [generic_has_keywords, generic_no_brand_flag]
                    }
                )
        else:
            self.log_result(
                "Matching Logic Structure", False,
                "Failed to add test favorites for matching logic test"
            )
    
    async def run_all_tests(self):
        """Run all backend tests"""
        logger.info("🚀 Starting Brand/Generic Name Feature Backend Tests (V1.0)")
        logger.info(f"Backend URL: {API_BASE}")
        
        # Authentication
        if not await self.authenticate():
            logger.error("❌ Authentication failed - stopping tests")
            return
        
        # Run all tests - focusing on brand/generic feature
        await self.test_categories_endpoint()
        
        # Core Brand/Generic Feature Tests
        await self.test_brand_generic_parsing()
        await self.test_smart_generic_extraction()
        await self.test_edge_cases()
        await self.test_organic_attribute_with_brand_matching()
        await self.simulate_rshd_matching_test()
        
        # Basic functionality tests
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
        
        logger.info(f"\n📊 BRAND/GENERIC FEATURE TEST SUMMARY")
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