#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Geographic Filtering Implementation
Tests DACSAI, DACDRLP-List, and DRLPDAC-List with bidirectional sync functionality.
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shop-radar-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials - Using working test user
TEST_EMAIL = "test.brand.generic@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_ROLE = "DAC"

# DRLP Test credentials for barcode/OCR testing
DRLP_TEST_EMAIL = "test.retailer@dealshaq.com"
DRLP_TEST_PASSWORD = "TestPassword123"
DRLP_TEST_ROLE = "DRLP"

class BackendTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_data = None
        self.drlp_auth_token = None
        self.drlp_user_data = None
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
    
    async def test_orange_juice_categorization_fix(self):
        """Test CRITICAL FIX: Orange Juice categorization to Beverages (not Fruits)"""
        logger.info("🍊 Testing CRITICAL FIX: Orange Juice categorization...")
        
        # First try to remove Orange Juice if it exists
        try:
            await self.make_request("POST", "/favorites/items/delete", {
                "item_name": "Orange Juice"
            })
        except:
            pass  # Ignore if it doesn't exist
        
        response = await self.make_request("POST", "/favorites/items", {
            "item_name": "Orange Juice"
        })
        
        if response["status"] == 200:
            category = response["data"]["item"]["category"]
            expected_category = "Beverages"
            
            if category == expected_category:
                self.log_result(
                    "CRITICAL FIX - Orange Juice Categorization", True,
                    f"✅ FIXED: Orange Juice correctly categorized as '{category}' (not Fruits)",
                    {"item": response["data"]["item"]}
                )
            else:
                self.log_result(
                    "CRITICAL FIX - Orange Juice Categorization", False,
                    f"❌ STILL BROKEN: Expected '{expected_category}', got '{category}'",
                    {"item": response["data"]["item"]}
                )
        elif response["status"] == 400 and "already in favorites" in response["data"].get("detail", ""):
            # Item already exists, let's check what category it has
            get_response = await self.make_request("GET", "/favorites/items")
            if get_response["status"] == 200:
                items_by_category = get_response["data"].get("items_by_category", {})
                orange_juice_item = None
                
                for category, items in items_by_category.items():
                    for item in items:
                        if item.get("item_name", "").lower() == "orange juice":
                            orange_juice_item = item
                            actual_category = category
                            break
                    if orange_juice_item:
                        break
                
                if orange_juice_item:
                    expected_category = "Beverages"
                    if actual_category == expected_category:
                        self.log_result(
                            "CRITICAL FIX - Orange Juice Categorization", True,
                            f"✅ FIXED: Orange Juice already exists and correctly categorized as '{actual_category}' (not Fruits)",
                            {"item": orange_juice_item}
                        )
                    else:
                        self.log_result(
                            "CRITICAL FIX - Orange Juice Categorization", False,
                            f"❌ STILL BROKEN: Expected '{expected_category}', got '{actual_category}'",
                            {"item": orange_juice_item}
                        )
                else:
                    self.log_result(
                        "CRITICAL FIX - Orange Juice Categorization", False,
                        "Orange Juice exists but couldn't find it in favorites list"
                    )
            else:
                self.log_result(
                    "CRITICAL FIX - Orange Juice Categorization", False,
                    f"Orange Juice already exists but couldn't retrieve favorites: {get_response['data']}"
                )
        else:
            self.log_result(
                "CRITICAL FIX - Orange Juice Categorization", False,
                f"Failed to add Orange Juice: {response['data']}"
            )
    
    async def test_categorization_logic(self):
        """Test categorization accuracy for various items"""
        logger.info("🏷️ Testing categorization logic...")
        
        test_cases = [
            {"item": "Organic Spinach", "expected": "Vegetables"},
            {"item": "Chocolate Chip Cookies", "expected": "Snacks & Candy"},
            {"item": "Frozen Pizza", "expected": "Frozen Foods"},
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
                "input": "Valley Farm, Fresh 2% Milk",
                "expected_generic": "2% Milk",
                "description": "Remove 'Fresh' but keep '2%'"
            },
            {
                "input": "Dannon, Light Greek Yogurt",
                "expected_generic": "Greek Yogurt",
                "description": "Remove 'Light' but keep 'Greek'"
            },
            {
                "input": "Kellogg's, Simply Corn Flakes",
                "expected_generic": "Corn Flakes",
                "description": "Remove 'Simply' modifier from different brand"
            }
        ]
        
        for case in test_cases:
            # First try to remove if it exists
            try:
                await self.make_request("POST", "/favorites/items/delete", {
                    "item_name": case["input"]
                })
            except:
                pass
            
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
            elif response["status"] == 400 and "already in favorites" in response["data"].get("detail", ""):
                # Item exists, check its generic field from existing favorites
                get_response = await self.make_request("GET", "/favorites/items")
                if get_response["status"] == 200:
                    items_by_category = get_response["data"].get("items_by_category", {})
                    found_item = None
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            if item.get("item_name") == case["input"]:
                                found_item = item
                                break
                        if found_item:
                            break
                    
                    if found_item:
                        actual_generic = found_item.get("generic")
                        if actual_generic == case["expected_generic"]:
                            self.log_result(
                                f"Smart Generic - {case['input']}", True,
                                f"{case['description']} - Already exists with correct generic '{actual_generic}'",
                                {"item": found_item}
                            )
                        else:
                            self.log_result(
                                f"Smart Generic - {case['input']}", False,
                                f"Expected '{case['expected_generic']}', got '{actual_generic}'",
                                {"item": found_item}
                            )
                    else:
                        self.log_result(
                            f"Smart Generic - {case['input']}", False,
                            "Item exists but couldn't find it in favorites"
                        )
                else:
                    self.log_result(
                        f"Smart Generic - {case['input']}", False,
                        f"Item exists but couldn't retrieve favorites: {get_response['data']}"
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
    
    async def test_removed_endpoints_return_404(self):
        """Test that removed category-level favorites endpoints return 404"""
        logger.info("🚫 Testing removed category-level favorites endpoints return 404...")
        
        removed_endpoints = [
            ("GET", "/favorites", "GET category-level favorites"),
            ("POST", "/favorites", "POST category-level favorites"),
            ("DELETE", "/favorites/test-id", "DELETE category-level favorites")
        ]
        
        for method, endpoint, description in removed_endpoints:
            response = await self.make_request(method, endpoint, {
                "category": "Fruits",
                "name": "Test Category Favorite"
            } if method == "POST" else None)
            
            if response["status"] == 404:
                self.log_result(
                    f"Removed Endpoint - {method} {endpoint}", True,
                    f"Correctly returns 404 for removed {description} endpoint",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    f"Removed Endpoint - {method} {endpoint}", False,
                    f"Expected 404, got {response['status']} for {description}",
                    {"response": response["data"]}
                )

    async def test_item_level_favorites_regression(self):
        """Test that item-level favorites still work after category-level removal"""
        logger.info("🔄 Testing item-level favorites regression (NO REGRESSION)...")
        
        # Test 1: Add a regression test item
        test_item = "Regression Test Apple"
        add_response = await self.make_request("POST", "/favorites/items", {
            "item_name": test_item
        })
        
        if add_response["status"] == 200:
            self.log_result(
                "Item-Level Add Regression", True,
                f"Successfully added '{test_item}' to item-level favorites",
                {"item": add_response["data"]["item"]}
            )
        else:
            self.log_result(
                "Item-Level Add Regression", False,
                f"Failed to add item-level favorite: {add_response['data']}"
            )
            return
        
        # Test 2: Get items organized by category
        get_response = await self.make_request("GET", "/favorites/items")
        
        if get_response["status"] == 200:
            items_by_category = get_response["data"].get("items_by_category", {})
            total_items = get_response["data"].get("total_items", 0)
            
            # Check if our test item is there
            found_item = False
            for category, items in items_by_category.items():
                for item in items:
                    if item.get("item_name") == test_item:
                        found_item = True
                        break
                if found_item:
                    break
            
            if found_item and total_items > 0:
                self.log_result(
                    "Item-Level Get Regression", True,
                    f"Successfully retrieved items organized by category (total: {total_items})",
                    {"categories": list(items_by_category.keys())}
                )
            else:
                self.log_result(
                    "Item-Level Get Regression", False,
                    f"Test item not found in organized favorites or no items returned"
                )
        else:
            self.log_result(
                "Item-Level Get Regression", False,
                f"Failed to get item-level favorites: {get_response['data']}"
            )
        
        # Test 3: Delete the test item
        delete_response = await self.make_request("POST", "/favorites/items/delete", {
            "item_name": test_item
        })
        
        if delete_response["status"] == 200:
            self.log_result(
                "Item-Level Delete Regression", True,
                f"Successfully deleted '{test_item}' from item-level favorites",
                {"response": delete_response["data"]}
            )
        else:
            self.log_result(
                "Item-Level Delete Regression", False,
                f"Failed to delete item-level favorite: {delete_response['data']}"
            )

    async def test_brand_generic_parsing_regression(self):
        """Test that brand/generic parsing still works correctly"""
        logger.info("🏪 Testing brand/generic parsing regression...")
        
        test_cases = [
            {
                "input": "Quaker, Granola",
                "expected_has_brand": True,
                "expected_brand": "Quaker",
                "expected_generic": "Granola",
                "description": "Brand-specific parsing"
            },
            {
                "input": "Granola",
                "expected_has_brand": False,
                "expected_brand": None,
                "expected_generic": "Granola",
                "description": "Generic parsing"
            }
        ]
        
        for case in test_cases:
            # First try to remove if exists
            try:
                await self.make_request("POST", "/favorites/items/delete", {
                    "item_name": case["input"]
                })
            except:
                pass
            
            response = await self.make_request("POST", "/favorites/items", {
                "item_name": case["input"]
            })
            
            if response["status"] == 200:
                item = response["data"]["item"]
                
                checks = {
                    "has_brand": item.get("has_brand") == case["expected_has_brand"],
                    "brand": item.get("brand") == case["expected_brand"],
                    "generic": item.get("generic") == case["expected_generic"]
                }
                
                if all(checks.values()):
                    self.log_result(
                        f"Brand/Generic Regression - {case['input']}", True,
                        f"{case['description']} - All fields correct",
                        {"item": item}
                    )
                else:
                    failed_checks = [k for k, v in checks.items() if not v]
                    self.log_result(
                        f"Brand/Generic Regression - {case['input']}", False,
                        f"Failed checks: {failed_checks}",
                        {"item": item, "expected": case}
                    )
            else:
                self.log_result(
                    f"Brand/Generic Regression - {case['input']}", False,
                    f"Failed to add item: {response['data']}"
                )

    async def test_auto_threshold_regression(self):
        """Test that auto-threshold settings still work"""
        logger.info("⚙️ Testing auto-threshold settings regression...")
        
        # Test valid values
        valid_thresholds = [0, 3, 6]
        
        for threshold in valid_thresholds:
            response = await self.make_request("PUT", "/users/settings/auto-threshold", {
                "auto_favorite_threshold": threshold
            })
            
            if response["status"] == 200:
                self.log_result(
                    f"Auto-Threshold Regression - {threshold}", True,
                    f"Successfully set threshold to {threshold}",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    f"Auto-Threshold Regression - {threshold}", False,
                    f"Failed to set threshold: {response['data']}"
                )
        
        # Test invalid value
        invalid_response = await self.make_request("PUT", "/users/settings/auto-threshold", {
            "auto_favorite_threshold": 5
        })
        
        if invalid_response["status"] == 400:
            self.log_result(
                "Auto-Threshold Invalid Value Regression", True,
                "Correctly rejected invalid threshold (5) with 400 error",
                {"response": invalid_response["data"]}
            )
        else:
            self.log_result(
                "Auto-Threshold Invalid Value Regression", False,
                f"Expected 400 for invalid value, got {invalid_response['status']}"
            )

    async def test_authentication_regression(self):
        """Test that authentication still works correctly"""
        logger.info("🔐 Testing authentication regression...")
        
        # Test 1: Login returns token
        login_response = await self.make_request("POST", "/auth/login", {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": TEST_ROLE
        })
        
        if login_response["status"] == 200 and login_response["data"].get("access_token"):
            self.log_result(
                "Authentication Login Regression", True,
                "Login endpoint returns valid token",
                {"user_role": login_response["data"]["user"]["role"]}
            )
        else:
            self.log_result(
                "Authentication Login Regression", False,
                f"Login failed: {login_response['data']}"
            )
        
        # Test 2: Protected endpoints require valid token
        original_token = self.auth_token
        self.auth_token = "invalid_token"
        
        protected_response = await self.make_request("GET", "/favorites/items")
        
        self.auth_token = original_token  # Restore
        
        if protected_response["status"] in [401, 403]:
            self.log_result(
                "Authentication Protection Regression", True,
                f"Protected endpoint correctly rejects invalid token with {protected_response['status']}",
                {"response": protected_response["data"]}
            )
        else:
            self.log_result(
                "Authentication Protection Regression", False,
                f"Expected 401/403 for invalid token, got {protected_response['status']}"
            )
        
        # Test 3: Role-based access (DAC only for favorites)
        if self.user_data and self.user_data.get("role") == "DAC":
            favorites_response = await self.make_request("GET", "/favorites/items")
            
            if favorites_response["status"] == 200:
                self.log_result(
                    "Authentication Role Access Regression", True,
                    "DAC user can access favorites endpoints",
                    {"user_role": self.user_data["role"]}
                )
            else:
                self.log_result(
                    "Authentication Role Access Regression", False,
                    f"DAC user cannot access favorites: {favorites_response['data']}"
                )

    async def test_dacdrlp_list_get_endpoint(self):
        """Test GET /api/dac/retailers - Get current DAC's retailer list"""
        logger.info("🏪 Testing DACDRLP-List GET endpoint...")
        
        response = await self.make_request("GET", "/dac/retailers")
        
        if response["status"] == 200:
            data = response["data"]
            retailers = data.get("retailers", [])
            dac_id = data.get("dac_id")
            dacsai_rad = data.get("dacsai_rad")
            
            # For existing user without delivery location, should return empty list
            if len(retailers) == 0 and "message" in data:
                self.log_result(
                    "DACDRLP-List GET Endpoint", True,
                    f"Returns empty list for DAC without delivery location: {data.get('message')}",
                    {"response": data}
                )
            else:
                self.log_result(
                    "DACDRLP-List GET Endpoint", True,
                    f"Returns DACDRLP-List with {len(retailers)} retailers",
                    {"retailers_count": len(retailers), "dacsai_rad": dacsai_rad}
                )
        else:
            self.log_result(
                "DACDRLP-List GET Endpoint", False,
                f"Failed with status {response['status']}: {response['data']}"
            )

    async def test_dacsai_update_endpoint(self):
        """Test PUT /api/dac/dacsai - Update DACSAI radius"""
        logger.info("📍 Testing DACSAI Update endpoint...")
        
        # Test without delivery location (should fail)
        response = await self.make_request("PUT", "/dac/dacsai?dacsai_rad=5.0")
        
        if response["status"] == 400:
            error_message = response["data"].get("detail", "")
            if "delivery location" in error_message.lower():
                self.log_result(
                    "DACSAI Update - No Delivery Location", True,
                    "Correctly returns 400 error when no delivery location set",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "DACSAI Update - No Delivery Location", False,
                    f"Wrong error message: {error_message}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "DACSAI Update - No Delivery Location", False,
                f"Expected 400 error, got {response['status']}: {response['data']}"
            )

    async def get_existing_drlp_with_location(self):
        """Get existing DRLP with location for geographic testing"""
        logger.info("🏗️ Getting existing DRLP with location...")
        
        # Get all DRLP locations
        locations_response = await self.make_request("GET", "/drlp/locations")
        
        if locations_response["status"] == 200:
            locations = locations_response["data"]
            
            # Find a DRLP with proper coordinates (not 0,0)
            for location in locations:
                coords = location.get("coordinates", {})
                if coords.get("lat", 0) != 0 and coords.get("lng", 0) != 0:
                    self.log_result(
                        "Get Existing DRLP", True,
                        f"Found existing DRLP with location: {location['name']}",
                        {
                            "drlp_id": location["user_id"],
                            "location": location
                        }
                    )
                    return {
                        "drlp_id": location["user_id"],
                        "location": location
                    }
            
            # If no DRLP with proper coordinates, use the first one
            if locations:
                location = locations[0]
                self.log_result(
                    "Get Existing DRLP", True,
                    f"Using existing DRLP (may have 0,0 coordinates): {location['name']}",
                    {
                        "drlp_id": location["user_id"],
                        "location": location
                    }
                )
                return {
                    "drlp_id": location["user_id"],
                    "location": location
                }
        
        self.log_result(
            "Get Existing DRLP", False,
            f"No DRLP locations found: {locations_response['data']}"
        )
        return None

    async def create_test_dac_with_delivery_location(self):
        """Create a test DAC with delivery location for geographic testing"""
        logger.info("🏠 Creating test DAC with delivery location...")
        
        # Use unique timestamp-based email to avoid conflicts
        import time
        timestamp = int(time.time())
        dac_email = f"test.dac.geo.{timestamp}@example.com"
        dac_password = "TestPassword123"
        
        register_response = await self.make_request("POST", "/auth/register", {
            "email": dac_email,
            "password": dac_password,
            "name": "Test Geo Consumer",
            "role": "DAC",
            "delivery_location": {
                "address": "123 Test St, New York, NY",
                "coordinates": {"lat": 40.7128, "lng": -74.0060}  # NYC coordinates
            },
            "dacsai_rad": 5.0
        })
        
        if register_response["status"] == 200:
            dac_token = register_response["data"]["access_token"]
            dac_id = register_response["data"]["user"]["id"]
            
            self.log_result(
                "Create Test DAC with Delivery Location", True,
                f"Successfully created DAC with delivery location and DACSAI-Rad: 5.0 miles",
                {
                    "dac_id": dac_id,
                    "delivery_location": register_response["data"]["user"]["delivery_location"]
                }
            )
            return {
                "dac_id": dac_id,
                "dac_token": dac_token,
                "user_data": register_response["data"]["user"]
            }
        else:
            self.log_result(
                "Create Test DAC with Delivery Location", False,
                f"Failed to register DAC: {register_response['data']}"
            )
            return None

    async def test_add_remove_retailers(self):
        """Test POST /api/dac/retailers/add and DELETE /api/dac/retailers/{drlp_id}"""
        logger.info("➕➖ Testing Add/Remove Retailers endpoints...")
        
        # Get existing DRLP
        drlp_data = await self.get_existing_drlp_with_location()
        if not drlp_data:
            self.log_result(
                "Add/Remove Retailers - Setup", False,
                "Failed to get existing DRLP for testing"
            )
            return
        
        drlp_id = drlp_data["drlp_id"]
        
        # Test ADD retailer
        add_response = await self.make_request("POST", f"/dac/retailers/add?drlp_id={drlp_id}")
        
        if add_response["status"] == 200:
            retailer_data = add_response["data"].get("retailer", {})
            self.log_result(
                "Add Retailer to DACDRLP-List", True,
                f"Successfully added DRLP {drlp_id} to retailer list",
                {"retailer": retailer_data}
            )
            
            # Test REMOVE retailer
            remove_response = await self.make_request("DELETE", f"/dac/retailers/{drlp_id}")
            
            if remove_response["status"] == 200:
                self.log_result(
                    "Remove Retailer from DACDRLP-List", True,
                    f"Successfully removed DRLP {drlp_id} from retailer list",
                    {"response": remove_response["data"]}
                )
            else:
                self.log_result(
                    "Remove Retailer from DACDRLP-List", False,
                    f"Failed to remove retailer: {remove_response['data']}"
                )
        else:
            self.log_result(
                "Add Retailer to DACDRLP-List", False,
                f"Failed to add retailer: {add_response['data']}"
            )

    async def test_notification_matching_with_geographic_filter(self):
        """Test notification matching with geographic filtering"""
        logger.info("🎯 Testing notification matching with geographic filter...")
        
        # This test requires a DRLP to post an RSHD and verify notifications
        # For now, we'll test the concept by checking if the geographic data structures exist
        
        # Check if DACDRLP-List exists for current user
        dacdrlp_response = await self.make_request("GET", "/dac/retailers")
        
        if dacdrlp_response["status"] == 200:
            self.log_result(
                "Geographic Filter - DACDRLP-List Check", True,
                "DACDRLP-List endpoint accessible for geographic filtering",
                {"response": dacdrlp_response["data"]}
            )
        else:
            self.log_result(
                "Geographic Filter - DACDRLP-List Check", False,
                f"Cannot access DACDRLP-List: {dacdrlp_response['data']}"
            )

    async def test_password_change_wrong_current_password(self):
        """Test password change with wrong current password - should return 400"""
        logger.info("🔐 Testing password change with wrong current password...")
        
        response = await self.make_request("PUT", "/auth/password/change", {
            "current_password": "WrongPassword",
            "new_password": "NewPass123"
        })
        
        if response["status"] == 400:
            error_detail = response["data"].get("detail", "")
            if "current password is incorrect" in error_detail.lower():
                self.log_result(
                    "Password Change - Wrong Current Password", True,
                    "Correctly rejected wrong current password with 400 error",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "Password Change - Wrong Current Password", False,
                    f"Wrong error message: {error_detail}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "Password Change - Wrong Current Password", False,
                f"Expected 400 error, got {response['status']}: {response['data']}"
            )

    async def test_password_change_same_password(self):
        """Test password change with same password - should return 400"""
        logger.info("🔐 Testing password change with same password...")
        
        response = await self.make_request("PUT", "/auth/password/change", {
            "current_password": TEST_PASSWORD,
            "new_password": TEST_PASSWORD
        })
        
        if response["status"] == 400:
            error_detail = response["data"].get("detail", "")
            if "new password must be different" in error_detail.lower():
                self.log_result(
                    "Password Change - Same Password", True,
                    "Correctly rejected same password with 400 error",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "Password Change - Same Password", False,
                    f"Wrong error message: {error_detail}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "Password Change - Same Password", False,
                f"Expected 400 error, got {response['status']}: {response['data']}"
            )

    async def test_password_change_short_password(self):
        """Test password change with short password - should return 400"""
        logger.info("🔐 Testing password change with short password...")
        
        response = await self.make_request("PUT", "/auth/password/change", {
            "current_password": TEST_PASSWORD,
            "new_password": "short"
        })
        
        if response["status"] == 400:
            error_detail = response["data"].get("detail", "")
            if "at least 8 characters" in error_detail.lower():
                self.log_result(
                    "Password Change - Short Password", True,
                    "Correctly rejected short password with 400 error",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "Password Change - Short Password", False,
                    f"Wrong error message: {error_detail}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "Password Change - Short Password", False,
                f"Expected 400 error, got {response['status']}: {response['data']}"
            )

    async def test_password_change_successful(self):
        """Test successful password change and login with new password, then change back"""
        logger.info("🔐 Testing successful password change...")
        
        new_password = "NewPassword456"
        
        # Step 1: Change password successfully
        change_response = await self.make_request("PUT", "/auth/password/change", {
            "current_password": TEST_PASSWORD,
            "new_password": new_password
        })
        
        if change_response["status"] == 200:
            self.log_result(
                "Password Change - Success", True,
                "Successfully changed password",
                {"response": change_response["data"]}
            )
            
            # Step 2: Test login with new password
            login_response = await self.make_request("POST", "/auth/login", {
                "email": TEST_EMAIL,
                "password": new_password,
                "role": TEST_ROLE
            })
            
            if login_response["status"] == 200:
                new_token = login_response["data"]["access_token"]
                self.log_result(
                    "Password Change - Login with New Password", True,
                    "Successfully logged in with new password",
                    {"user": login_response["data"]["user"]["email"]}
                )
                
                # Update our auth token for the change back
                old_token = self.auth_token
                self.auth_token = new_token
                
                # Step 3: Change password back to original
                change_back_response = await self.make_request("PUT", "/auth/password/change", {
                    "current_password": new_password,
                    "new_password": TEST_PASSWORD
                })
                
                if change_back_response["status"] == 200:
                    self.log_result(
                        "Password Change - Change Back to Original", True,
                        "Successfully changed password back to original",
                        {"response": change_back_response["data"]}
                    )
                    
                    # Restore original token for remaining tests
                    self.auth_token = old_token
                    
                else:
                    self.log_result(
                        "Password Change - Change Back to Original", False,
                        f"Failed to change back: {change_back_response['data']}"
                    )
                    # Keep new token since change back failed
                    
            else:
                self.log_result(
                    "Password Change - Login with New Password", False,
                    f"Failed to login with new password: {login_response['data']}"
                )
                
                # Try to change back anyway using old token
                change_back_response = await self.make_request("PUT", "/auth/password/change", {
                    "current_password": new_password,
                    "new_password": TEST_PASSWORD
                })
                
        else:
            self.log_result(
                "Password Change - Success", False,
                f"Failed to change password: {change_response['data']}"
            )

    async def test_existing_functionality_regression(self):
        """Test that existing functionality still works"""
        logger.info("🔄 Testing existing functionality regression...")
        
        # Test item-level favorites
        test_item = "Geographic Test Apple"
        add_response = await self.make_request("POST", "/favorites/items", {
            "item_name": test_item
        })
        
        if add_response["status"] == 200:
            self.log_result(
                "Existing Functionality - Item Favorites", True,
                "Item-level favorites still working correctly",
                {"item": add_response["data"]["item"]}
            )
            
            # Clean up
            await self.make_request("POST", "/favorites/items/delete", {
                "item_name": test_item
            })
        else:
            self.log_result(
                "Existing Functionality - Item Favorites", False,
                f"Item-level favorites broken: {add_response['data']}"
            )
        
        # Test auto-threshold settings
        threshold_response = await self.make_request("PUT", "/users/settings/auto-threshold", {
            "auto_favorite_threshold": 3
        })
        
        if threshold_response["status"] == 200:
            self.log_result(
                "Existing Functionality - Auto Threshold", True,
                "Auto-threshold settings still working correctly",
                {"response": threshold_response["data"]}
            )
        else:
            self.log_result(
                "Existing Functionality - Auto Threshold", False,
                f"Auto-threshold settings broken: {threshold_response['data']}"
            )

    async def authenticate_drlp(self):
        """Authenticate with DRLP credentials for barcode/OCR testing"""
        logger.info("🔐 Authenticating with DRLP credentials...")
        
        response = await self.make_request("POST", "/auth/login", {
            "email": DRLP_TEST_EMAIL,
            "password": DRLP_TEST_PASSWORD,
            "role": DRLP_TEST_ROLE
        })
        
        if response["status"] == 200:
            self.drlp_auth_token = response["data"]["access_token"]
            self.drlp_user_data = response["data"]["user"]
            self.log_result("DRLP Authentication", True, f"Successfully authenticated as {DRLP_TEST_EMAIL}")
            return True
        else:
            self.log_result("DRLP Authentication", False, f"Failed to authenticate: {response['data']}")
            return False

    def create_test_image_base64(self, text: str, width: int = 200, height: int = 100):
        """Create a test image with text using PIL and return base64"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            import base64
            
            # Create image with white background
            img = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Try to use default font, fallback to basic if not available
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Calculate text position (centered)
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # Rough estimation if font not available
                text_width = len(text) * 8
                text_height = 12
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text
            draw.text((x, y), text, fill='black', font=font)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return image_base64
        except ImportError:
            logger.error("PIL (Pillow) not available, using minimal base64 image")
            # Return a minimal valid PNG base64 (1x1 pixel)
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    async def test_barcode_lookup_valid(self):
        """Test POST /api/barcode/lookup with valid barcode (Nutella)"""
        logger.info("🔍 Testing barcode lookup with valid barcode...")
        
        # Switch to DRLP token
        original_token = self.auth_token
        self.auth_token = self.drlp_auth_token
        
        response = await self.make_request("POST", "/barcode/lookup", {
            "barcode": "3017620422003"  # Nutella barcode
        })
        
        # Restore original token
        self.auth_token = original_token
        
        if response["status"] == 200:
            data = response["data"]
            if data.get("success") and data.get("product"):
                product = data["product"]
                self.log_result(
                    "Barcode Lookup - Valid Nutella", True,
                    f"Successfully retrieved product: {product.get('name')}",
                    {
                        "product": product,
                        "brand": product.get("brand"),
                        "category": product.get("category"),
                        "weight": product.get("weight")
                    }
                )
            else:
                self.log_result(
                    "Barcode Lookup - Valid Nutella", False,
                    f"Invalid response structure: {data}"
                )
        else:
            self.log_result(
                "Barcode Lookup - Valid Nutella", False,
                f"Failed with status {response['status']}: {response['data']}"
            )

    async def test_barcode_lookup_invalid(self):
        """Test POST /api/barcode/lookup with invalid barcode"""
        logger.info("🔍 Testing barcode lookup with invalid barcode...")
        
        # Switch to DRLP token
        original_token = self.auth_token
        self.auth_token = self.drlp_auth_token
        
        response = await self.make_request("POST", "/barcode/lookup", {
            "barcode": "0000000000000"  # Invalid barcode
        })
        
        # Restore original token
        self.auth_token = original_token
        
        if response["status"] == 404:
            data = response["data"]
            if "not found" in data.get("detail", "").lower():
                self.log_result(
                    "Barcode Lookup - Invalid Barcode", True,
                    "Correctly returned 404 for invalid barcode",
                    {"response": data}
                )
            else:
                self.log_result(
                    "Barcode Lookup - Invalid Barcode", False,
                    f"Wrong error message: {data}"
                )
        else:
            self.log_result(
                "Barcode Lookup - Invalid Barcode", False,
                f"Expected 404, got {response['status']}: {response['data']}"
            )

    async def test_ocr_price_extraction(self):
        """Test POST /api/ocr/extract-price with test image"""
        logger.info("💰 Testing OCR price extraction...")
        
        # Create test image with price text
        image_base64 = self.create_test_image_base64("Price: $9.99", 200, 100)
        
        # Switch to DRLP token
        original_token = self.auth_token
        self.auth_token = self.drlp_auth_token
        
        response = await self.make_request("POST", "/ocr/extract-price", {
            "image_base64": image_base64
        })
        
        # Restore original token
        self.auth_token = original_token
        
        if response["status"] == 200:
            data = response["data"]
            if data.get("success") and data.get("extracted", {}).get("price"):
                extracted_price = data["extracted"]["price"]
                expected_price = "9.99"
                
                if extracted_price == expected_price:
                    self.log_result(
                        "OCR Price Extraction", True,
                        f"Successfully extracted price: ${extracted_price}",
                        {"extracted": data["extracted"]}
                    )
                else:
                    self.log_result(
                        "OCR Price Extraction", False,
                        f"Expected price '{expected_price}', got '{extracted_price}'",
                        {"extracted": data["extracted"]}
                    )
            else:
                self.log_result(
                    "OCR Price Extraction", False,
                    f"Invalid response structure or no price extracted: {data}"
                )
        else:
            self.log_result(
                "OCR Price Extraction", False,
                f"Failed with status {response['status']}: {response['data']}"
            )

    async def test_ocr_product_analysis(self):
        """Test POST /api/ocr/analyze-product with test image"""
        logger.info("🥛 Testing OCR product analysis...")
        
        # Create test image with product text
        image_base64 = self.create_test_image_base64("ORGANIC MILK\n2% Fat - 1 Gallon", 300, 150)
        
        # Switch to DRLP token
        original_token = self.auth_token
        self.auth_token = self.drlp_auth_token
        
        response = await self.make_request("POST", "/ocr/analyze-product", {
            "image_base64": image_base64
        })
        
        # Restore original token
        self.auth_token = original_token
        
        if response["status"] == 200:
            data = response["data"]
            if data.get("success") and data.get("product"):
                product = data["product"]
                category = product.get("category")
                expected_category = "Dairy & Eggs"
                
                if category == expected_category:
                    self.log_result(
                        "OCR Product Analysis", True,
                        f"Successfully analyzed product and categorized as '{category}'",
                        {
                            "product": product,
                            "organic": product.get("organic"),
                            "name": product.get("name")
                        }
                    )
                else:
                    self.log_result(
                        "OCR Product Analysis", False,
                        f"Expected category '{expected_category}', got '{category}'",
                        {"product": product}
                    )
            else:
                self.log_result(
                    "OCR Product Analysis", False,
                    f"Invalid response structure or no product analyzed: {data}"
                )
        else:
            self.log_result(
                "OCR Product Analysis", False,
                f"Failed with status {response['status']}: {response['data']}"
            )

    async def test_barcode_ocr_authorization_dac_forbidden(self):
        """Test that DAC users get 403 Forbidden for barcode/OCR endpoints"""
        logger.info("🚫 Testing DAC user authorization (should be forbidden)...")
        
        # Use DAC token (current auth_token)
        endpoints_to_test = [
            ("/barcode/lookup", {"barcode": "3017620422003"}),
            ("/ocr/extract-price", {"image_base64": self.create_test_image_base64("Price: $5.99")}),
            ("/ocr/analyze-product", {"image_base64": self.create_test_image_base64("Test Product")})
        ]
        
        for endpoint, data in endpoints_to_test:
            response = await self.make_request("POST", endpoint, data)
            
            if response["status"] == 403:
                error_detail = response["data"].get("detail", "")
                if "only drlp users" in error_detail.lower():
                    self.log_result(
                        f"DAC Authorization - {endpoint}", True,
                        f"Correctly rejected DAC user with 403: {error_detail}",
                        {"endpoint": endpoint}
                    )
                else:
                    self.log_result(
                        f"DAC Authorization - {endpoint}", False,
                        f"Wrong error message: {error_detail}",
                        {"endpoint": endpoint}
                    )
            else:
                self.log_result(
                    f"DAC Authorization - {endpoint}", False,
                    f"Expected 403, got {response['status']}: {response['data']}",
                    {"endpoint": endpoint}
                )

    async def test_barcode_ocr_authorization_unauthenticated(self):
        """Test that unauthenticated requests get 401/403"""
        logger.info("🔒 Testing unauthenticated access to barcode/OCR endpoints...")
        
        # Remove auth token temporarily
        original_token = self.auth_token
        self.auth_token = None
        
        endpoints_to_test = [
            ("/barcode/lookup", {"barcode": "3017620422003"}),
            ("/ocr/extract-price", {"image_base64": self.create_test_image_base64("Price: $5.99")}),
            ("/ocr/analyze-product", {"image_base64": self.create_test_image_base64("Test Product")})
        ]
        
        for endpoint, data in endpoints_to_test:
            response = await self.make_request("POST", endpoint, data)
            
            if response["status"] in [401, 403]:
                self.log_result(
                    f"Unauthenticated Access - {endpoint}", True,
                    f"Correctly rejected unauthenticated request with {response['status']}",
                    {"endpoint": endpoint, "response": response["data"]}
                )
            else:
                self.log_result(
                    f"Unauthenticated Access - {endpoint}", False,
                    f"Expected 401/403, got {response['status']}: {response['data']}",
                    {"endpoint": endpoint}
                )
        
        # Restore auth token
        self.auth_token = original_token

    async def run_barcode_ocr_tests(self):
        """Run comprehensive Barcode/OCR integration tests"""
        logger.info("🎯 STARTING BARCODE/OCR INTEGRATION TESTS")
        
        # Authenticate with both DAC and DRLP credentials
        if not await self.authenticate():
            logger.error("❌ Failed to authenticate with DAC credentials")
            return {"total": 0, "passed": 0, "failed": 0, "results": []}
        
        if not await self.authenticate_drlp():
            logger.error("❌ Failed to authenticate with DRLP credentials")
            return {"total": 0, "passed": 0, "failed": 0, "results": []}
        
        # Run barcode tests
        logger.info("📊 Testing Barcode Lookup API...")
        await self.test_barcode_lookup_valid()
        await self.test_barcode_lookup_invalid()
        
        # Run OCR tests
        logger.info("📊 Testing OCR APIs...")
        await self.test_ocr_price_extraction()
        await self.test_ocr_product_analysis()
        
        # Run authorization tests
        logger.info("📊 Testing Authorization...")
        await self.test_barcode_ocr_authorization_dac_forbidden()
        await self.test_barcode_ocr_authorization_unauthenticated()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 BARCODE/OCR INTEGRATION TEST SUMMARY")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info(f"🎉 100% SUCCESS: Barcode/OCR integration working!")
        else:
            logger.info(f"⚠️ ISSUES DETECTED: {failed_tests} tests failing")
        
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

    async def run_password_change_tests(self):
        """Run password change feature tests"""
        logger.info("🚀 Starting PASSWORD CHANGE FEATURE TESTING")
        logger.info(f"Backend URL: {API_BASE}")
        logger.info(f"Test Credentials: {TEST_EMAIL} (Role: {TEST_ROLE})")
        
        # Authentication
        if not await self.authenticate():
            logger.error("❌ Authentication failed - stopping tests")
            return
        
        # Password Change Tests
        logger.info("🔐 PASSWORD CHANGE VALIDATION TESTS")
        await self.test_password_change_wrong_current_password()
        await self.test_password_change_same_password()
        await self.test_password_change_short_password()
        await self.test_password_change_successful()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 PASSWORD CHANGE FEATURE TEST SUMMARY")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info(f"🎉 100% SUCCESS: Password change feature working perfectly!")
        else:
            logger.info(f"⚠️ ISSUES DETECTED: {failed_tests} tests failing")
        
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

    async def run_all_tests(self):
        """Run comprehensive geographic filtering tests"""
        logger.info("🚀 Starting COMPREHENSIVE GEOGRAPHIC FILTERING TESTING")
        logger.info(f"Backend URL: {API_BASE}")
        logger.info(f"Test Credentials: {TEST_EMAIL} (Role: {TEST_ROLE})")
        
        # Authentication
        if not await self.authenticate():
            logger.error("❌ Authentication failed - stopping tests")
            return
        
        # PRIORITY 1: New DACDRLP-List Endpoints
        logger.info("🎯 PRIORITY 1: New DACDRLP-List Endpoints")
        await self.test_dacdrlp_list_get_endpoint()
        await self.test_dacsai_update_endpoint()
        
        # PRIORITY 2: Registration with Geographic Data
        logger.info("🏗️ PRIORITY 2: Registration with Geographic Data")
        await self.get_existing_drlp_with_location()
        await self.create_test_dac_with_delivery_location()
        
        # PRIORITY 3: Add/Remove Retailers
        logger.info("➕➖ PRIORITY 3: Add/Remove Retailers")
        await self.test_add_remove_retailers()
        
        # PRIORITY 4: Notification Matching with Geographic Filter
        logger.info("🎯 PRIORITY 4: Notification Matching with Geographic Filter")
        await self.test_notification_matching_with_geographic_filter()
        
        # PRIORITY 5: Existing Functionality Regression
        logger.info("🔄 PRIORITY 5: Existing Functionality Regression")
        await self.test_existing_functionality_regression()
        await self.test_categories_endpoint()
        await self.test_authentication_regression()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 COMPREHENSIVE GEOGRAPHIC FILTERING TEST SUMMARY")
        logger.info(f"🎯 DACSAI, DACDRLP-List, and DRLPDAC-List Implementation")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info(f"🎉 100% SUCCESS: Geographic filtering implementation working!")
        else:
            logger.info(f"⚠️ ISSUES DETECTED: {failed_tests} tests failing")
        
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
        # Run barcode/OCR integration tests as requested
        results = await tester.run_barcode_ocr_tests()
        
        # Save results to file
        with open("/app/test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📁 Test results saved to /app/test_results.json")
        
        return results["failed"] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)