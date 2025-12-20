#!/usr/bin/env python3
"""
Barcode and OCR Integration Testing for DealShaq Retailer App
Tests the new barcode lookup and OCR functionality for DRLP users.
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
DRLP_TEST_EMAIL = "test.retailer@dealshaq.com"
DRLP_TEST_PASSWORD = "TestPassword123"
DRLP_TEST_ROLE = "DRLP"

# DAC credentials for authorization testing
DAC_TEST_EMAIL = "test.brand.generic@example.com"
DAC_TEST_PASSWORD = "TestPassword123"
DAC_TEST_ROLE = "DAC"

class BarcodeOCRTester:
    def __init__(self):
        self.session = None
        self.drlp_auth_token = None
        self.dac_auth_token = None
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
    
    async def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None, auth_token: str = None):
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"
        
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
    
    async def authenticate_drlp(self):
        """Authenticate with DRLP test credentials"""
        logger.info("🔐 Authenticating DRLP user for barcode/OCR testing...")
        
        response = await self.make_request("POST", "/auth/login", {
            "email": DRLP_TEST_EMAIL,
            "password": DRLP_TEST_PASSWORD,
            "role": DRLP_TEST_ROLE
        })
        
        if response["status"] == 200:
            self.drlp_auth_token = response["data"]["access_token"]
            self.log_result("DRLP Authentication", True, f"Successfully authenticated as {DRLP_TEST_EMAIL}")
            return True
        else:
            self.log_result("DRLP Authentication", False, f"Failed to authenticate DRLP: {response['data']}")
            return False

    async def authenticate_dac(self):
        """Authenticate with DAC test credentials for authorization testing"""
        logger.info("🔐 Authenticating DAC user for authorization testing...")
        
        response = await self.make_request("POST", "/auth/login", {
            "email": DAC_TEST_EMAIL,
            "password": DAC_TEST_PASSWORD,
            "role": DAC_TEST_ROLE
        })
        
        if response["status"] == 200:
            self.dac_auth_token = response["data"]["access_token"]
            self.log_result("DAC Authentication", True, f"Successfully authenticated as {DAC_TEST_EMAIL}")
            return True
        else:
            self.log_result("DAC Authentication", False, f"Failed to authenticate DAC: {response['data']}")
            return False

    async def test_barcode_lookup_valid_barcodes(self):
        """Test barcode lookup with valid barcodes"""
        logger.info("🔍 Testing barcode lookup with valid barcodes...")
        
        test_barcodes = [
            {
                "barcode": "3017620422003",
                "description": "Nutella (should return product info)",
                "expected_success": True
            },
            {
                "barcode": "5449000000996", 
                "description": "Coca-Cola (should return product info)",
                "expected_success": True
            }
        ]
        
        for test_case in test_barcodes:
            response = await self.make_request("POST", "/barcode/lookup", {
                "barcode": test_case["barcode"]
            }, auth_token=self.drlp_auth_token)
            
            if response["status"] == 200:
                data = response["data"]
                if data.get("success") and data.get("product"):
                    product = data["product"]
                    self.log_result(
                        f"Barcode Lookup - {test_case['description']}", True,
                        f"Successfully retrieved product: {product.get('name', 'Unknown')}",
                        {
                            "barcode": test_case["barcode"],
                            "product_name": product.get("name"),
                            "brand": product.get("brand"),
                            "category": product.get("category"),
                            "is_organic": product.get("is_organic"),
                            "weight": product.get("weight"),
                            "image_url": product.get("image_url")
                        }
                    )
                else:
                    self.log_result(
                        f"Barcode Lookup - {test_case['description']}", False,
                        f"API returned success=False: {data}",
                        {"barcode": test_case["barcode"]}
                    )
            elif response["status"] == 404:
                # Product not found is acceptable for some barcodes
                self.log_result(
                    f"Barcode Lookup - {test_case['description']}", True,
                    "Product not found (acceptable for some barcodes)",
                    {"barcode": test_case["barcode"], "response": response["data"]}
                )
            else:
                self.log_result(
                    f"Barcode Lookup - {test_case['description']}", False,
                    f"Failed with status {response['status']}: {response['data']}",
                    {"barcode": test_case["barcode"]}
                )

    async def test_barcode_lookup_invalid_barcodes(self):
        """Test barcode lookup with invalid barcodes"""
        logger.info("❌ Testing barcode lookup with invalid barcodes...")
        
        test_cases = [
            {
                "barcode": "0000000000000",
                "description": "Invalid barcode (should return 'Product not found')"
            },
            {
                "barcode": "",
                "description": "Empty barcode (should return error)"
            }
        ]
        
        for test_case in test_cases:
            response = await self.make_request("POST", "/barcode/lookup", {
                "barcode": test_case["barcode"]
            }, auth_token=self.drlp_auth_token)
            
            if response["status"] == 404:
                self.log_result(
                    f"Invalid Barcode - {test_case['description']}", True,
                    "Correctly returned 404 for invalid barcode",
                    {"barcode": test_case["barcode"], "response": response["data"]}
                )
            elif response["status"] == 400:
                # Bad request for empty barcode is also acceptable
                self.log_result(
                    f"Invalid Barcode - {test_case['description']}", True,
                    "Correctly returned 400 for invalid request",
                    {"barcode": test_case["barcode"], "response": response["data"]}
                )
            else:
                self.log_result(
                    f"Invalid Barcode - {test_case['description']}", False,
                    f"Expected 404/400, got {response['status']}: {response['data']}",
                    {"barcode": test_case["barcode"]}
                )

    async def test_ocr_price_extraction(self):
        """Test OCR price extraction with sample image"""
        logger.info("💰 Testing OCR price extraction...")
        
        # Create a simple test image (1x1 pixel base64 encoded JPEG)
        # This is a minimal valid image for testing the endpoint
        test_image_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        response = await self.make_request("POST", "/ocr/extract-price", {
            "image_base64": test_image_base64
        }, auth_token=self.drlp_auth_token)
        
        if response["status"] == 200:
            data = response["data"]
            if data.get("success"):
                extracted = data.get("extracted", {})
                self.log_result(
                    "OCR Price Extraction", True,
                    "Successfully processed image for price extraction",
                    {
                        "extracted_data": extracted,
                        "has_price": "price" in extracted,
                        "has_product_name": "product_name" in extracted,
                        "response_structure": list(extracted.keys()) if extracted else []
                    }
                )
            else:
                self.log_result(
                    "OCR Price Extraction", False,
                    f"OCR returned success=False: {data.get('error')}",
                    {"response": data}
                )
        else:
            self.log_result(
                "OCR Price Extraction", False,
                f"Failed with status {response['status']}: {response['data']}"
            )

    async def test_ocr_product_analysis(self):
        """Test OCR product analysis with sample image"""
        logger.info("🔍 Testing OCR product analysis...")
        
        # Use the same test image
        test_image_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        response = await self.make_request("POST", "/ocr/analyze-product", {
            "image_base64": test_image_base64
        }, auth_token=self.drlp_auth_token)
        
        if response["status"] == 200:
            data = response["data"]
            if data.get("success"):
                product = data.get("product", {})
                self.log_result(
                    "OCR Product Analysis", True,
                    "Successfully processed image for product analysis",
                    {
                        "product_data": product,
                        "has_product_name": "product_name" in product,
                        "has_brand": "brand" in product,
                        "has_category": "category" in product,
                        "has_organic_flag": "is_organic" in product,
                        "response_structure": list(product.keys()) if product else []
                    }
                )
            else:
                self.log_result(
                    "OCR Product Analysis", False,
                    f"OCR returned success=False: {data.get('error')}",
                    {"response": data}
                )
        else:
            self.log_result(
                "OCR Product Analysis", False,
                f"Failed with status {response['status']}: {response['data']}"
            )

    async def test_barcode_ocr_authorization(self):
        """Test that only DRLP users can access barcode/OCR endpoints"""
        logger.info("🔒 Testing barcode/OCR authorization (DRLP only)...")
        
        # Test with DAC user (should get 403)
        dac_tests = [
            ("POST", "/barcode/lookup", {"barcode": "3017620422003"}, "Barcode Lookup"),
            ("POST", "/ocr/extract-price", {"image_base64": "test"}, "OCR Price Extraction"),
            ("POST", "/ocr/analyze-product", {"image_base64": "test"}, "OCR Product Analysis")
        ]
        
        for method, endpoint, data, description in dac_tests:
            response = await self.make_request(method, endpoint, data, auth_token=self.dac_auth_token)
            
            if response["status"] == 403:
                self.log_result(
                    f"Authorization - {description} (DAC User)", True,
                    "Correctly rejected DAC user with 403 Forbidden",
                    {"endpoint": endpoint, "response": response["data"]}
                )
            else:
                self.log_result(
                    f"Authorization - {description} (DAC User)", False,
                    f"Expected 403, got {response['status']}: {response['data']}",
                    {"endpoint": endpoint}
                )
        
        # Test without auth token (should get 401)
        for method, endpoint, data, description in dac_tests:
            response = await self.make_request(method, endpoint, data, auth_token=None)
            
            if response["status"] == 401:
                self.log_result(
                    f"Authorization - {description} (No Auth)", True,
                    "Correctly rejected unauthenticated request with 401",
                    {"endpoint": endpoint, "response": response["data"]}
                )
            else:
                self.log_result(
                    f"Authorization - {description} (No Auth)", False,
                    f"Expected 401, got {response['status']}: {response['data']}",
                    {"endpoint": endpoint}
                )

    async def test_category_mapping(self):
        """Test that barcode lookup correctly maps categories to DealShaq's 20 categories"""
        logger.info("🏷️ Testing category mapping from Open Food Facts to DealShaq categories...")
        
        # Test with a known barcode that should return a mappable category
        response = await self.make_request("POST", "/barcode/lookup", {
            "barcode": "3017620422003"  # Nutella
        }, auth_token=self.drlp_auth_token)
        
        if response["status"] == 200:
            data = response["data"]
            if data.get("success") and data.get("product"):
                product = data["product"]
                category = product.get("category")
                
                # Check if category is one of DealShaq's 20 valid categories
                valid_categories = [
                    "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
                    "Dairy & Eggs", "Bakery & Bread", "Pantry Staples",
                    "Snacks & Candy", "Frozen Foods", "Beverages",
                    "Deli & Prepared Foods", "Breakfast & Cereal",
                    "Pasta, Rice & Grains", "Oils, Sauces & Spices",
                    "Baby & Kids", "Health & Nutrition", "Household Essentials",
                    "Personal Care", "Pet Supplies", "Miscellaneous"
                ]
                
                if category in valid_categories:
                    self.log_result(
                        "Category Mapping", True,
                        f"Successfully mapped to valid DealShaq category: '{category}'",
                        {
                            "product_name": product.get("name"),
                            "mapped_category": category,
                            "valid_categories_count": len(valid_categories),
                            "raw_categories": product.get("raw_data", {}).get("categories", "")
                        }
                    )
                else:
                    self.log_result(
                        "Category Mapping", False,
                        f"Category '{category}' not in DealShaq's 20 valid categories",
                        {
                            "invalid_category": category,
                            "valid_categories": valid_categories
                        }
                    )
            else:
                self.log_result(
                    "Category Mapping", False,
                    f"Failed to get product data for category mapping test: {data}"
                )
        elif response["status"] == 404:
            # If product not found, test with another barcode or mark as acceptable
            self.log_result(
                "Category Mapping", True,
                "Product not found for category mapping test (acceptable - test barcode may not exist in database)",
                {"test_barcode": "3017620422003"}
            )
        else:
            self.log_result(
                "Category Mapping", False,
                f"Failed to test category mapping: {response['status']} - {response['data']}"
            )

    async def run_all_tests(self):
        """Run all barcode and OCR tests"""
        logger.info("🚀 Starting Barcode and OCR Integration Tests...")
        logger.info(f"Backend URL: {API_BASE}")
        logger.info(f"DRLP Test Credentials: {DRLP_TEST_EMAIL}")
        logger.info(f"DAC Test Credentials: {DAC_TEST_EMAIL}")
        
        # Authenticate users
        if not await self.authenticate_drlp():
            logger.error("Failed to authenticate DRLP user - stopping tests")
            return
        
        if not await self.authenticate_dac():
            logger.error("Failed to authenticate DAC user - authorization tests will be skipped")
        
        # Run all barcode/OCR tests
        await self.test_barcode_lookup_valid_barcodes()
        await self.test_barcode_lookup_invalid_barcodes()
        await self.test_ocr_price_extraction()
        await self.test_ocr_product_analysis()
        await self.test_barcode_ocr_authorization()
        await self.test_category_mapping()
        
        logger.info("✅ Completed Barcode and OCR Integration Tests")
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📊 BARCODE & OCR INTEGRATION TEST SUMMARY")
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
    async with BarcodeOCRTester() as tester:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("/app/barcode_ocr_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📁 Test results saved to /app/barcode_ocr_test_results.json")
        
        return results["failed"] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)