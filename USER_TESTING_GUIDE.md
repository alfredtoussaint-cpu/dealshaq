# DealShaq User Testing Guide
## Complete Step-by-Step Testing Procedures

**Version:** 1.0  
**Date:** December 2025  
**Purpose:** Comprehensive user acceptance testing for all three DealShaq applications

---

## Table of Contents
1. [Testing Overview](#testing-overview)
2. [Test Credentials](#test-credentials)
3. [Consumer App Testing](#consumer-app-testing)
4. [Retailer App Testing](#retailer-app-testing)
5. [Admin App Testing](#admin-app-testing)
6. [Issue Reporting Template](#issue-reporting-template)

---

## Testing Overview

### What Has Been Tested by Emergent

**Backend Testing (100% Success):**
- ✅ Authentication & Authorization
- ✅ Enhanced DACFI-List (Item-level favorites)
- ✅ Brand/Generic name distinction
- ✅ Auto-categorization (20 categories)
- ✅ Organic/Gluten-free attribute detection
- ✅ Smart Favorites auto-add scheduler
- ✅ API endpoints (Add/Get/Delete favorites, Update settings)
- ✅ Database operations
- ✅ Error handling
- ✅ **Geographic Filtering (DACSAI)** - NEW
- ✅ **DACDRLP-List Management** - NEW
- ✅ **Bidirectional Sync (DACDRLP ↔ DRLPDAC)** - NEW
- ✅ **Radar View API** - NEW
- ✅ **Password Change** - NEW

**Frontend Testing (100% Success):**
- ✅ Consumer Settings page (Smart Favorites + DACSAI configuration)
- ✅ Enhanced Favorites page (Add/remove items, brand indicators)
- ✅ **"My Retailers" page** - NEW (DACDRLP-List management)
- ✅ **"Radar View" page** - NEW (Local RSHD feed)
- ✅ Logo integration (all apps)
- ✅ Navigation (updated with Retailers and Radar links)
- ✅ Form validation
- ✅ Toast notifications
- ✅ **Registration with mandatory delivery location** - NEW

**Full Test Documentation:** `/app/test_result.md`

### What Needs User Testing

**User Acceptance Testing (UAT):**
- Real-world usage scenarios
- User experience (UX) flow
- Visual design and layout
- Cross-browser compatibility
- Mobile responsiveness
- End-to-end workflows
- Edge cases in actual use

---

## Test Credentials

### Consumer (DAC) Accounts

**Test Account 1:**
- Email: `alfred.toussaint@gmail.com`
- Password: `TestPassword123`
- Role: Consumer

**Test Account 2:**
- Email: `test.brand.generic@example.com`
- Password: `TestPassword123`
- Role: Consumer

### Retailer (DRLP) Account

**Test Retailer:**
- Email: `alfred.toussaint@gmail.com`
- Password: `TestPassword123`
- Role: Retailer
- Note: Same email can have multiple roles

### Admin Account

**Test Admin 1:**
- Email: `alfred.toussaint@gmail.com`
- Password: `TestPassword123`
- Role: Admin

**Test Admin 2:**
- Email: `alfred.toussaint@novatp.com`
- Password: `Admin123!`
- Role: Admin

---

## Consumer App Testing

**Application URL:** https://shop-radar-app.preview.emergentagent.com/consumer

**Estimated Time:** 45-60 minutes

### Test Suite 1: Authentication & Onboarding

#### Test 1.1: Login
**Steps:**
1. Navigate to Consumer app URL
2. Click "Login" tab (should be selected by default)
3. Enter email: `alfred.toussaint@gmail.com`
4. Enter password: `TestPassword123`
5. Click "Sign In" button

**Expected Results:**
- ✅ Login successful
- ✅ Redirected to Consumer Dashboard
- ✅ DealShaq logo visible in header
- ✅ User name displayed in header

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 1.2: Registration (New User) - UPDATED
**Steps:**
1. Logout from current session
2. Navigate to Consumer app URL
3. Click "Register" tab
4. Fill in:
   - Name: `Test User [Your Name]`
   - Email: `testuser.[yourname]@example.com`
   - Password: `Test12345`
   - Select a charity from dropdown
   - **Delivery Location (REQUIRED):** Enter address or coordinates
   - **DACSAI Radius (REQUIRED):** Select radius (0.1 - 9.9 miles)
5. Click "Register" button

**Expected Results:**
- ✅ Registration successful
- ✅ Redirected to Dashboard
- ✅ Welcome message or toast notification
- ✅ **DACSAI is initialized with selected radius**
- ✅ **DACDRLP-List is auto-populated with nearby retailers**

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 1.3: Forgot Password
**Steps:**
1. Logout
2. Go to Login page
3. Click "Forgot password?" link
4. Enter email: `alfred.toussaint@gmail.com`
5. Click "Send Reset Link"

**Expected Results:**
- ✅ Success message: "Password reset link sent! Check your email."
- ✅ Modal closes
- ✅ (Check email for reset link - may take a few minutes)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 2: Smart Favorites Configuration

#### Test 2.1: Navigate to Settings
**Steps:**
1. Login as Consumer
2. Click "Settings" in the navigation menu

**Expected Results:**
- ✅ Settings page loads
- ✅ "Smart Favorites" section visible
- ✅ Account information displayed (email, name, role)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 2.2: Configure Auto-Add Threshold
**Steps:**
1. On Settings page, locate "Smart Favorites" section
2. Read the verbose question: "How many separate days would you want to be buying a non-favorite item, before you want DealShaq to add that item to your favorites list?"
3. Verify 3 radio button options are present:
   - "6 separate days"
   - "3 separate days"
   - "Never (0 days)" (should be default)
4. Select "6 separate days"
5. Click "Save Settings" button

**Expected Results:**
- ✅ Success toast: "Settings saved successfully!"
- ✅ "How It Works" info box visible below options
- ✅ Selection persists (refresh page and verify "6 separate days" is still selected)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 2.3: Change Threshold to Different Value
**Steps:**
1. Select "3 separate days"
2. Click "Save Settings"
3. Refresh the page

**Expected Results:**
- ✅ Success toast appears
- ✅ "3 separate days" is selected after refresh

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 3: Enhanced Favorites (DACFI-List)

#### Test 3.1: Navigate to Favorites
**Steps:**
1. Click "Favorites" in the navigation menu

**Expected Results:**
- ✅ Favorites page loads
- ✅ Title: "My Favorite Items (DACFI-List)"
- ✅ Input field for adding items
- ✅ Placeholder text: 'e.g., "Granola" or "Quaker, Granola"'
- ✅ Helper text about brand-specific items

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.2: Add Generic Item (Any Brand)
**Steps:**
1. Type "Granola" in the input field
2. Click "Add to Favorites" button

**Expected Results:**
- ✅ Success toast: "Granola added to your favorites! Automatically categorized as: Breakfast & Cereal"
- ✅ Item appears under "Breakfast & Cereal" category header
- ✅ Item shows "Manual" badge (green)
- ✅ NO brand indicator (because no comma was used)
- ✅ NO "Brand-specific" badge

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.3: Add Brand-Specific Item
**Steps:**
1. Type "Quaker, Granola" (note the comma after brand name)
2. Click "Add to Favorites"

**Expected Results:**
- ✅ Success toast with categorization message
- ✅ Item appears under "Breakfast & Cereal"
- ✅ Item shows "(Brand: Quaker)" indicator
- ✅ Item shows "🏷️ Brand-specific" badge
- ✅ Item shows "Manual" badge

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.4: Add Item with Organic Attribute
**Steps:**
1. Type "Organic 2% Milk"
2. Click "Add to Favorites"

**Expected Results:**
- ✅ Item categorized to "Dairy & Eggs"
- ✅ Item shows "🌿 Organic" indicator
- ✅ Item shows "Manual" badge
- ✅ NO brand indicator (no comma used)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.5: Add Brand-Specific with Organic
**Steps:**
1. Type "Valley Farm, 2% Milk"
2. Click "Add to Favorites"

**Expected Results:**
- ✅ Item categorized to "Dairy & Eggs"
- ✅ Item shows "(Brand: Valley Farm)" indicator
- ✅ Item shows "🏷️ Brand-specific" badge
- ✅ Item shows "Manual" badge

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.6: Test Duplicate Prevention
**Steps:**
1. Try to add "Granola" again (item already exists)
2. Click "Add to Favorites"

**Expected Results:**
- ✅ Error toast: "Item already in favorites"
- ✅ Item is NOT added again

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.7: Remove Item
**Steps:**
1. Find "Granola" in the favorites list
2. Click the trash/remove button

**Expected Results:**
- ✅ Success toast: "Granola removed from favorites"
- ✅ Item disappears from the list

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 3.8: Test Empty Input
**Steps:**
1. Leave input field empty
2. Click "Add to Favorites"

**Expected Results:**
- ✅ Error message OR button is disabled
- ✅ Nothing is added

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 4: Browse & Notifications

#### Test 4.1: Browse Deals
**Steps:**
1. Click "Browse" in navigation
2. Browse available deals
3. Try filtering by category if available

**Expected Results:**
- ✅ Deals are displayed
- ✅ Category filters work (if implemented)
- ✅ Deal information is clear

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 4.2: View Notifications
**Steps:**
1. Click "Alerts" (bell icon) in navigation
2. View notifications list

**Expected Results:**
- ✅ Notifications page loads
- ✅ Notifications displayed (if any exist)
- ✅ Can mark as read

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 5: Visual & UX Testing

#### Test 5.1: Logo Display
**Steps:**
1. Check logo in header on all pages
2. Click logo in header

**Expected Results:**
- ✅ DealShaq logo visible and properly sized
- ✅ Clicking logo returns to Dashboard
- ✅ Logo looks professional (not pixelated or stretched)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 5.2: Mobile Responsiveness
**Steps:**
1. Resize browser window to mobile size (or use mobile device)
2. Navigate through different pages
3. Test adding favorites on mobile

**Expected Results:**
- ✅ Layout adapts to mobile screen
- ✅ Navigation is usable
- ✅ Forms are accessible
- ✅ Text is readable

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 5.3: Cross-Browser Testing
**Steps:**
1. Test in Chrome
2. Test in Firefox
3. Test in Safari (if available)
4. Test in Edge (if available)

**Expected Results:**
- ✅ Works in all tested browsers
- ✅ No visual glitches
- ✅ All functionality works

**Browser Results:**
- [ ] Chrome: Pass / Fail
- [ ] Firefox: Pass / Fail
- [ ] Safari: Pass / Fail
- [ ] Edge: Pass / Fail

---

### Test Suite 6: Performance & Errors

#### Test 6.1: Page Load Speed
**Steps:**
1. Clear browser cache
2. Navigate to different pages
3. Observe load times

**Expected Results:**
- ✅ Pages load within 2-3 seconds
- ✅ No long waiting periods

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 6.2: Console Errors
**Steps:**
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Navigate through application

**Expected Results:**
- ✅ No red error messages
- ✅ No broken resource warnings

**Actual Results:**
- [ ] Pass
- [ ] Fail (list errors):

---

### Test Suite NEW-1: My Retailers (DACDRLP-List Management)

#### Test NEW-1.1: View My Retailers
**Steps:**
1. Login as Consumer
2. Click "Retailers" in the navigation menu

**Expected Results:**
- ✅ "My Retailers" page loads
- ✅ List of retailers in DACDRLP-List is displayed
- ✅ Each retailer shows: Name, Distance, Status (auto-added vs manual)
- ✅ Remove button available for each retailer

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test NEW-1.2: Remove a Retailer
**Steps:**
1. On "My Retailers" page, find a retailer inside your DACSAI
2. Click "Remove" button for that retailer
3. Confirm removal

**Expected Results:**
- ✅ Retailer is marked as "manually_removed"
- ✅ Retailer no longer appears in active list
- ✅ You will no longer receive notifications from this retailer
- ✅ Success toast notification

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test NEW-1.3: Add a Retailer (Outside DACSAI)
**Steps:**
1. On "My Retailers" page, find the "Add Retailer" section
2. Search for a retailer outside your DACSAI
3. Click "Add" button

**Expected Results:**
- ✅ Retailer is added to your DACDRLP-List with "manually_added: true"
- ✅ You will now receive notifications from this retailer
- ✅ Success toast notification

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite NEW-2: Radar View

#### Test NEW-2.1: View Radar
**Steps:**
1. Login as Consumer
2. Click "Radar" in the navigation menu

**Expected Results:**
- ✅ Radar View page loads
- ✅ Shows RSHDs (deals) from retailers in your DACDRLP-List
- ✅ Each deal shows: Item name, Retailer name, Discount %, Price, Expiry

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite NEW-3: DACSAI Settings

#### Test NEW-3.1: Update DACSAI Radius
**Steps:**
1. Go to Settings page
2. Find "Shopping Area (DACSAI)" section
3. Adjust the radius slider (e.g., from 5.0 to 7.5 miles)
4. Click "Save DACSAI Settings"

**Expected Results:**
- ✅ DACSAI-Rad is updated
- ✅ DACDRLP-List is recalculated (retailers added/removed based on new radius)
- ✅ Manual overrides (added/removed retailers) are preserved
- ✅ Success toast notification

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test NEW-3.2: Update Delivery Location
**Steps:**
1. Go to Settings page
2. Find "Delivery Location" section
3. Enter a new address or coordinates
4. Click "Update Location"

**Expected Results:**
- ✅ Delivery location is updated
- ✅ DACSAI center is recalculated
- ✅ DACDRLP-List is recalculated based on new location
- ✅ Success toast notification

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite NEW-4: Password Change

#### Test NEW-4.1: Change Password
**Steps:**
1. Go to Settings page
2. Find "Change Password" section
3. Enter current password
4. Enter new password
5. Confirm new password
6. Click "Change Password"

**Expected Results:**
- ✅ Password is changed successfully
- ✅ Success toast notification
- ✅ Can logout and login with new password

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

## Retailer App Testing

**Application URL:** https://shop-radar-app.preview.emergentagent.com/retailer

**Estimated Time:** 30-45 minutes

### Test Suite 7: Retailer Authentication

#### Test 7.1: Retailer Login
**Steps:**
1. Navigate to Retailer app URL
2. Enter email: `alfred.toussaint@gmail.com`
3. Enter password: `TestPassword123`
4. Click "Login"

**Expected Results:**
- ✅ Login successful
- ✅ Redirected to Retailer Dashboard
- ✅ DealShaq logo visible
- ✅ "Retailer Portal" subtitle shown

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 8: Inventory Management

#### Test 8.1: View Inventory
**Steps:**
1. Click "Inventory" in navigation
2. View list of posted items

**Expected Results:**
- ✅ Inventory page loads
- ✅ Items displayed in organized format
- ✅ Can see item details (name, category, price, discount)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 8.2: Post New RSHD Item
**Steps:**
1. Click "Post Item" in navigation
2. Fill in item details:
   - Name: "Test Deal Item"
   - Category: Select from dropdown
   - Regular Price: 10.00
   - Discount Level: 2 (DRLP 75% → Consumer 60% OFF)
   - Quantity: 50
3. Click "Post Item" button

**Expected Results:**
- ✅ Success message
- ✅ Item appears in inventory with correct discounts
- ✅ Shows: DRLP discount 75%, Consumer sees 60% OFF
- ✅ Form resets for next item

**Note:** DealShaq uses 3 discount levels:
- Level 1: DRLP 60% → Consumer 50% OFF
- Level 2: DRLP 75% → Consumer 60% OFF
- Level 3: DRLP 90% → Consumer 75% OFF

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 8.3: Edit Item
**Steps:**
1. From Inventory, find the test item
2. Click "Edit" button (if available)
3. Change discount level from 2 to 3
4. Save changes

**Expected Results:**
- ✅ Item updates successfully
- ✅ New discounts shown: DRLP 90%, Consumer 75% OFF
- ✅ Deal price recalculated correctly

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 8.4: Delete Item
**Steps:**
1. Find test item in inventory
2. Click "Delete" button
3. Confirm deletion (if prompted)

**Expected Results:**
- ✅ Item removed from inventory
- ✅ Confirmation message

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 9: Retailer Orders

#### Test 9.1: View Orders
**Steps:**
1. Click "Orders" in navigation
2. View order history

**Expected Results:**
- ✅ Orders page loads
- ✅ Orders displayed (if any exist)
- ✅ Order details visible

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 10: Retailer Visual Testing

#### Test 10.1: Logo and Branding
**Steps:**
1. Verify DealShaq logo in header
2. Check "Retailer Portal" subtitle
3. Verify consistent color scheme (blue theme)

**Expected Results:**
- ✅ Logo displays correctly
- ✅ Branding is consistent
- ✅ Visual hierarchy is clear

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

## Admin App Testing

**Application URL:** https://shop-radar-app.preview.emergentagent.com/admin

**Estimated Time:** 30-40 minutes

### Test Suite 11: Admin Authentication

#### Test 11.1: Admin Login
**Steps:**
1. Navigate to Admin app URL
2. Enter email: `alfred.toussaint@gmail.com`
3. Enter password: `TestPassword123`
4. Click "Login"

**Expected Results:**
- ✅ Login successful
- ✅ Redirected to Admin Dashboard
- ✅ DealShaq logo visible
- ✅ "Admin Portal" subtitle shown

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 12: Dashboard Overview

#### Test 12.1: View Statistics
**Steps:**
1. On Admin Dashboard, view statistics cards
2. Check metrics displayed (users, items, orders, etc.)

**Expected Results:**
- ✅ Statistics load correctly
- ✅ Numbers are accurate
- ✅ Visual cards are clear and readable

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 13: User Management

#### Test 13.1: View All Users
**Steps:**
1. Click "Users" in navigation
2. View list of all users

**Expected Results:**
- ✅ Users page loads
- ✅ All users displayed (Consumers, Retailers, Admins)
- ✅ User details visible (name, email, role, join date)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 13.2: Filter Users by Role
**Steps:**
1. On Users page, try filtering by role (if available)
2. Filter by "DAC" (Consumer)
3. Filter by "DRLP" (Retailer)
4. Filter by "Admin"

**Expected Results:**
- ✅ Filtering works correctly
- ✅ Only users with selected role shown

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 13.3: View User Details
**Steps:**
1. Click on a specific user
2. View detailed information

**Expected Results:**
- ✅ User detail page/modal opens
- ✅ Complete user information displayed
- ✅ Activity history visible (if implemented)

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 14: Item Management (Admin View)

#### Test 14.1: View All Items
**Steps:**
1. Click "Transactions" or "Items" in navigation
2. View all RSHD items across all retailers

**Expected Results:**
- ✅ All items displayed
- ✅ Can see retailer who posted each item
- ✅ Categories and details visible

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

#### Test 14.2: Moderate/Remove Item
**Steps:**
1. Find an item to moderate
2. Click edit/remove (if admin has these permissions)

**Expected Results:**
- ✅ Admin can moderate content
- ✅ Changes take effect

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test Suite 15: Admin Visual Testing

#### Test 15.1: Logo and Branding
**Steps:**
1. Verify DealShaq logo in header
2. Check "Admin Portal" subtitle
3. Verify consistent color scheme (purple/admin theme)

**Expected Results:**
- ✅ Logo displays correctly
- ✅ Admin branding distinct from Consumer/Retailer
- ✅ Professional appearance

**Actual Results:**
- [ ] Pass
- [ ] Fail (describe issue):

---

## Issue Reporting Template

### Bug Report Format

```
**Issue ID:** [Sequential number: ISSUE-001]
**Date:** [Date found]
**Tester:** [Your name]
**App:** [Consumer / Retailer / Admin]
**Severity:** [Critical / High / Medium / Low]

**Test Case:** [Test number and name]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:**


**Actual Result:**


**Screenshots/Videos:** [If applicable]

**Browser/Device:**
- Browser: [Chrome/Firefox/Safari/Edge]
- Version: 
- Operating System: 
- Screen Size: 

**Additional Notes:**

```

### Severity Definitions

**Critical:**
- Application crash
- Data loss
- Security vulnerability
- Cannot complete core functionality

**High:**
- Major feature not working
- Significant UX problem
- Affects multiple users

**Medium:**
- Minor feature not working
- Workaround available
- Visual inconsistency

**Low:**
- Cosmetic issue
- Minor text error
- Nice-to-have improvement

---

## Test Completion Summary

### Overall Results

**Consumer App:**
- Total Test Cases: 31
- Passed: ___
- Failed: ___
- Pass Rate: ___%

**Retailer App:**
- Total Test Cases: 11
- Passed: ___
- Failed: ___
- Pass Rate: ___%

**Admin App:**
- Total Test Cases: 11
- Passed: ___
- Failed: ___
- Pass Rate: ___%

**Overall:**
- Total Test Cases: 53
- Passed: ___
- Failed: ___
- Pass Rate: ___%

### Critical Issues Found

1. 
2. 
3. 

### Recommendations

1. 
2. 
3. 

### Sign-Off

**Tested By:** ___________________  
**Date:** ___________________  
**Signature:** ___________________  

**Approved for Production:** Yes / No  
**Comments:**

---

## End of Testing Guide
