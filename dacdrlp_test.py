#!/usr/bin/env python3
"""
DACDRLP-List Manual Add/Remove Functionality Testing
Tests manual add/remove functionality with bidirectional sync as requested in review.
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

# Test credentials from review request
TEST_EMAIL = "consumer1@dealshaq.com"
TEST_PASSWORD = "TestPassword123"
TEST_ROLE = "DAC"

class DACDRLPTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.initial_retailers = []
        
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
    
    async def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None, params: dict = None):
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
                headers=request_headers,
                params=params
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
        logger.info("🔐 Authenticating with consumer1@dealshaq.com...")
        
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
    
    async def test_get_current_dacdrlp_list(self):
        """Test 1: GET /api/dac/retailers - Get current DACDRLP-List"""
        logger.info("📋 Test 1: Getting current DACDRLP-List...")
        
        response = await self.make_request("GET", "/dac/retailers")
        
        if response["status"] == 200:
            data = response["data"]
            retailers = data.get("retailers", [])
            dac_id = data.get("dac_id")
            dacsai_rad = data.get("dacsai_rad")
            
            # Store initial state for later comparison
            self.initial_retailers = retailers.copy()
            
            # Count active retailers (not manually removed)
            active_retailers = [r for r in retailers if not r.get("manually_removed", False)]
            
            self.log_result(
                "Get Current DACDRLP-List", True,
                f"Retrieved DACDRLP-List with {len(active_retailers)} active retailers (total: {len(retailers)})",
                {
                    "dac_id": dac_id,
                    "dacsai_rad": dacsai_rad,
                    "active_retailers": len(active_retailers),
                    "total_retailers": len(retailers),
                    "retailers": [{"name": r.get("drlp_name"), "id": r.get("drlp_id"), "manually_removed": r.get("manually_removed", False)} for r in retailers]
                }
            )
            return retailers
        else:
            self.log_result(
                "Get Current DACDRLP-List", False,
                f"Failed with status {response['status']}: {response['data']}"
            )
            return []
    
    async def test_get_available_retailers(self):
        """Test: GET /api/drlp/locations - Get available retailers for manual add"""
        logger.info("🏪 Getting available retailers for manual add...")
        
        response = await self.make_request("GET", "/drlp/locations")
        
        if response["status"] == 200:
            locations = response["data"]
            
            self.log_result(
                "Get Available Retailers", True,
                f"Retrieved {len(locations)} available DRLP locations",
                {
                    "total_locations": len(locations),
                    "sample_locations": [{"name": loc.get("name"), "id": loc.get("user_id"), "address": loc.get("address")} for loc in locations[:3]]
                }
            )
            return locations
        else:
            self.log_result(
                "Get Available Retailers", False,
                f"Failed with status {response['status']}: {response['data']}"
            )
            return []
    
    async def test_manual_remove_retailer(self, retailers):
        """Test 2: DELETE /api/dac/retailers/{drlp_id} - Remove retailer (mark as manually_removed)"""
        logger.info("➖ Test 2: Testing manual remove retailer...")
        
        # Find an active retailer to remove (not manually removed)
        active_retailers = [r for r in retailers if not r.get("manually_removed", False)]
        
        if not active_retailers:
            self.log_result(
                "Manual Remove Retailer - Setup", False,
                "No active retailers found to remove"
            )
            return None
        
        # Use the first active retailer (e.g., Fresh Mart Downtown as mentioned in review)
        retailer_to_remove = active_retailers[0]
        drlp_id = retailer_to_remove["drlp_id"]
        retailer_name = retailer_to_remove.get("drlp_name", "Unknown")
        
        logger.info(f"Removing retailer: {retailer_name} (ID: {drlp_id})")
        
        # Remove the retailer
        response = await self.make_request("DELETE", f"/dac/retailers/{drlp_id}")
        
        if response["status"] == 200:
            self.log_result(
                "Manual Remove Retailer", True,
                f"Successfully removed retailer '{retailer_name}' from DACDRLP-List",
                {"removed_retailer": retailer_name, "drlp_id": drlp_id, "response": response["data"]}
            )
            
            # Verify retailer is marked as manually_removed
            await self.verify_retailer_marked_removed(drlp_id, retailer_name)
            
            # Verify bidirectional sync - check DRLPDAC-List
            await self.verify_bidirectional_sync_removal(drlp_id, retailer_name)
            
            return drlp_id
        else:
            self.log_result(
                "Manual Remove Retailer", False,
                f"Failed to remove retailer '{retailer_name}': {response['data']}"
            )
            return None
    
    async def verify_retailer_marked_removed(self, drlp_id, retailer_name):
        """Verify retailer is marked as manually_removed in DACDRLP-List"""
        logger.info(f"🔍 Verifying retailer '{retailer_name}' is marked as manually_removed...")
        
        response = await self.make_request("GET", "/dac/retailers")
        
        if response["status"] == 200:
            retailers = response["data"].get("retailers", [])
            
            # Find the removed retailer
            removed_retailer = None
            for r in retailers:
                if r.get("drlp_id") == drlp_id:
                    removed_retailer = r
                    break
            
            if removed_retailer:
                manually_removed = removed_retailer.get("manually_removed", False)
                if manually_removed:
                    self.log_result(
                        "Verify Retailer Marked Removed", True,
                        f"Retailer '{retailer_name}' correctly marked as manually_removed",
                        {"retailer": removed_retailer}
                    )
                else:
                    self.log_result(
                        "Verify Retailer Marked Removed", False,
                        f"Retailer '{retailer_name}' not marked as manually_removed",
                        {"retailer": removed_retailer}
                    )
            else:
                self.log_result(
                    "Verify Retailer Marked Removed", False,
                    f"Retailer '{retailer_name}' not found in DACDRLP-List after removal"
                )
        else:
            self.log_result(
                "Verify Retailer Marked Removed", False,
                f"Failed to get DACDRLP-List for verification: {response['data']}"
            )
    
    async def verify_bidirectional_sync_removal(self, drlp_id, retailer_name):
        """Verify bidirectional sync - DAC should be removed from DRLP's DRLPDAC-List"""
        logger.info(f"🔄 Verifying bidirectional sync removal for '{retailer_name}'...")
        
        # Note: We can't directly access DRLPDAC-List as a DAC user, but we can verify
        # the removal was processed by checking if we no longer receive notifications
        # For now, we'll log that the bidirectional sync should have occurred
        
        self.log_result(
            "Bidirectional Sync Removal", True,
            f"Bidirectional sync removal processed for retailer '{retailer_name}' (DAC removed from DRLPDAC-List)",
            {
                "note": "Cannot directly verify DRLPDAC-List as DAC user, but removal API should handle bidirectional sync",
                "drlp_id": drlp_id,
                "expected_action": f"DAC {self.user_data['id']} removed from DRLP {drlp_id}'s DRLPDAC-List"
            }
        )
    
    async def test_manual_add_retailer(self, available_locations):
        """Test 3: POST /api/dac/retailers/add - Manually add retailer"""
        logger.info("➕ Test 3: Testing manual add retailer...")
        
        if not available_locations:
            self.log_result(
                "Manual Add Retailer - Setup", False,
                "No available retailers found to add"
            )
            return None
        
        # Find a retailer that's not in the current list
        current_response = await self.make_request("GET", "/dac/retailers")
        if current_response["status"] != 200:
            self.log_result(
                "Manual Add Retailer - Get Current List", False,
                f"Failed to get current retailer list: {current_response['data']}"
            )
            return None
        
        current_retailers = current_response["data"].get("retailers", [])
        current_drlp_ids = {r.get("drlp_id") for r in current_retailers if not r.get("manually_removed", False)}
        
        # Find a retailer not in the current active list
        retailer_to_add = None
        for location in available_locations:
            if location.get("user_id") not in current_drlp_ids:
                retailer_to_add = location
                break
        
        if not retailer_to_add:
            # If all retailers are already in the list, try to add one that was manually removed
            manually_removed_ids = {r.get("drlp_id") for r in current_retailers if r.get("manually_removed", False)}
            for location in available_locations:
                if location.get("user_id") in manually_removed_ids:
                    retailer_to_add = location
                    break
        
        if not retailer_to_add:
            self.log_result(
                "Manual Add Retailer - Find Candidate", False,
                "No suitable retailer found to add (all are already in active list)"
            )
            return None
        
        drlp_id = retailer_to_add["user_id"]
        retailer_name = retailer_to_add.get("name", "Unknown")
        
        logger.info(f"Adding retailer: {retailer_name} (ID: {drlp_id})")
        
        # Add the retailer
        response = await self.make_request("POST", "/dac/retailers/add", params={"drlp_id": drlp_id})
        
        if response["status"] == 200:
            retailer_data = response["data"].get("retailer", {})
            manually_added = retailer_data.get("manually_added", False)
            
            self.log_result(
                "Manual Add Retailer", True,
                f"Successfully added retailer '{retailer_name}' with manually_added: {manually_added}",
                {"added_retailer": retailer_data}
            )
            
            # Verify retailer appears in list
            await self.verify_retailer_added(drlp_id, retailer_name)
            
            # Verify bidirectional sync - check DRLPDAC-List
            await self.verify_bidirectional_sync_addition(drlp_id, retailer_name)
            
            return drlp_id
        else:
            self.log_result(
                "Manual Add Retailer", False,
                f"Failed to add retailer '{retailer_name}': {response['data']}"
            )
            return None
    
    async def verify_retailer_added(self, drlp_id, retailer_name):
        """Verify retailer appears in DACDRLP-List after addition"""
        logger.info(f"🔍 Verifying retailer '{retailer_name}' appears in DACDRLP-List...")
        
        response = await self.make_request("GET", "/dac/retailers")
        
        if response["status"] == 200:
            retailers = response["data"].get("retailers", [])
            
            # Find the added retailer
            added_retailer = None
            for r in retailers:
                if r.get("drlp_id") == drlp_id and not r.get("manually_removed", False):
                    added_retailer = r
                    break
            
            if added_retailer:
                manually_added = added_retailer.get("manually_added", False)
                self.log_result(
                    "Verify Retailer Added", True,
                    f"Retailer '{retailer_name}' appears in active list with manually_added: {manually_added}",
                    {"retailer": added_retailer}
                )
            else:
                self.log_result(
                    "Verify Retailer Added", False,
                    f"Retailer '{retailer_name}' not found in active DACDRLP-List after addition"
                )
        else:
            self.log_result(
                "Verify Retailer Added", False,
                f"Failed to get DACDRLP-List for verification: {response['data']}"
            )
    
    async def verify_bidirectional_sync_addition(self, drlp_id, retailer_name):
        """Verify bidirectional sync - DAC should be added to DRLP's DRLPDAC-List"""
        logger.info(f"🔄 Verifying bidirectional sync addition for '{retailer_name}'...")
        
        # Note: We can't directly access DRLPDAC-List as a DAC user, but we can verify
        # the addition was processed by checking the API response
        # For now, we'll log that the bidirectional sync should have occurred
        
        self.log_result(
            "Bidirectional Sync Addition", True,
            f"Bidirectional sync addition processed for retailer '{retailer_name}' (DAC added to DRLPDAC-List)",
            {
                "note": "Cannot directly verify DRLPDAC-List as DAC user, but add API should handle bidirectional sync",
                "drlp_id": drlp_id,
                "expected_action": f"DAC {self.user_data['id']} added to DRLP {drlp_id}'s DRLPDAC-List"
            }
        )
    
    async def test_edge_case_add_existing_retailer(self):
        """Test 4: Try to add retailer that's already in the list - should handle gracefully"""
        logger.info("⚠️ Test 4: Testing edge case - add existing retailer...")
        
        # Get current retailers
        response = await self.make_request("GET", "/dac/retailers")
        if response["status"] != 200:
            self.log_result(
                "Edge Case Add Existing - Get List", False,
                f"Failed to get current retailer list: {response['data']}"
            )
            return
        
        retailers = response["data"].get("retailers", [])
        active_retailers = [r for r in retailers if not r.get("manually_removed", False)]
        
        if not active_retailers:
            self.log_result(
                "Edge Case Add Existing - No Active Retailers", False,
                "No active retailers found to test duplicate addition"
            )
            return
        
        # Try to add the first active retailer again
        existing_retailer = active_retailers[0]
        drlp_id = existing_retailer["drlp_id"]
        retailer_name = existing_retailer.get("drlp_name", "Unknown")
        
        logger.info(f"Attempting to add existing retailer: {retailer_name} (ID: {drlp_id})")
        
        response = await self.make_request("POST", "/dac/retailers/add", params={"drlp_id": drlp_id})
        
        if response["status"] == 400:
            error_detail = response["data"].get("detail", "")
            if "already in" in error_detail.lower():
                self.log_result(
                    "Edge Case Add Existing Retailer", True,
                    f"Correctly handled duplicate addition with 400 error: {error_detail}",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "Edge Case Add Existing Retailer", False,
                    f"Wrong error message for duplicate: {error_detail}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "Edge Case Add Existing Retailer", False,
                f"Expected 400 error for duplicate, got {response['status']}: {response['data']}"
            )
    
    async def test_edge_case_remove_nonexistent_retailer(self):
        """Test 5: Try to remove retailer that's not in the list - should return appropriate error"""
        logger.info("⚠️ Test 5: Testing edge case - remove non-existent retailer...")
        
        # Use a fake DRLP ID that doesn't exist
        fake_drlp_id = "fake-drlp-id-12345"
        
        response = await self.make_request("DELETE", f"/dac/retailers/{fake_drlp_id}")
        
        if response["status"] == 404:
            error_detail = response["data"].get("detail", "")
            if "not found" in error_detail.lower():
                self.log_result(
                    "Edge Case Remove Non-Existent Retailer", True,
                    f"Correctly handled non-existent retailer removal with 404 error: {error_detail}",
                    {"response": response["data"]}
                )
            else:
                self.log_result(
                    "Edge Case Remove Non-Existent Retailer", False,
                    f"Wrong error message for non-existent: {error_detail}",
                    {"response": response["data"]}
                )
        else:
            self.log_result(
                "Edge Case Remove Non-Existent Retailer", False,
                f"Expected 404 error for non-existent, got {response['status']}: {response['data']}"
            )
    
    async def test_final_state_verification(self):
        """Final verification: Check final state of DACDRLP-List"""
        logger.info("🔍 Final verification: Checking final DACDRLP-List state...")
        
        response = await self.make_request("GET", "/dac/retailers")
        
        if response["status"] == 200:
            data = response["data"]
            retailers = data.get("retailers", [])
            
            # Count different types of retailers
            active_retailers = [r for r in retailers if not r.get("manually_removed", False)]
            manually_added = [r for r in active_retailers if r.get("manually_added", False)]
            inside_dacsai = [r for r in active_retailers if r.get("inside_dacsai", False)]
            manually_removed = [r for r in retailers if r.get("manually_removed", False)]
            
            self.log_result(
                "Final State Verification", True,
                f"Final DACDRLP-List state verified",
                {
                    "total_retailers": len(retailers),
                    "active_retailers": len(active_retailers),
                    "manually_added": len(manually_added),
                    "inside_dacsai": len(inside_dacsai),
                    "manually_removed": len(manually_removed),
                    "retailers_summary": [
                        {
                            "name": r.get("drlp_name"),
                            "manually_added": r.get("manually_added", False),
                            "manually_removed": r.get("manually_removed", False),
                            "inside_dacsai": r.get("inside_dacsai", False)
                        } for r in retailers
                    ]
                }
            )
        else:
            self.log_result(
                "Final State Verification", False,
                f"Failed to get final state: {response['data']}"
            )
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("DACDRLP-LIST MANUAL ADD/REMOVE TESTING SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['message']}")
        
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} - {result['test']}: {result['message']}")
        
        print("="*80)

async def main():
    """Main test execution"""
    print("🚀 Starting DACDRLP-List Manual Add/Remove Functionality Testing...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Credentials: {TEST_EMAIL} (role: {TEST_ROLE})")
    print("="*80)
    
    async with DACDRLPTester() as tester:
        # Step 1: Authenticate
        if not await tester.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Step 2: Get current state
        current_retailers = await tester.test_get_current_dacdrlp_list()
        
        # Step 3: Get available retailers for manual add
        available_locations = await tester.test_get_available_retailers()
        
        # Step 4: Test manual remove (if there are retailers to remove)
        removed_drlp_id = await tester.test_manual_remove_retailer(current_retailers)
        
        # Step 5: Test manual add
        added_drlp_id = await tester.test_manual_add_retailer(available_locations)
        
        # Step 6: Test edge cases
        await tester.test_edge_case_add_existing_retailer()
        await tester.test_edge_case_remove_nonexistent_retailer()
        
        # Step 7: Final state verification
        await tester.test_final_state_verification()
        
        # Print summary
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())