# DealShaq Admin Account Security

## Overview
Admin accounts have full system access and must be tightly controlled. This document outlines the security measures for Admin account management.

## Security Principles

### 1. No Public Registration
- ❌ **BLOCKED**: Admin accounts CANNOT be created through public `/api/auth/register`
- ✅ **ALLOWED**: Only through secure, authenticated methods
- **Reason**: Prevents unauthorized system access

### 2. Bootstrap Method
- First Admin account created via secure script: `create_first_admin.py`
- Script prompts for email, name, password
- Checks if Admin already exists (prevents duplicates)
- Should be run once on secure server

### 3. Admin-Only Creation
- After first Admin exists, additional Admins created via API
- Endpoint: `POST /api/admin/create-admin`
- **Requires**: Valid Admin authentication token
- **Logs**: All Admin creation events for audit trail

## Creating the First Admin

### Step 1: Run Bootstrap Script
```bash
cd /app/backend
python create_first_admin.py
```

### Step 2: Enter Details
```
Admin Email: admin@dealshaq.com
Admin Name: System Administrator
Admin Password: [secure password - min 8 chars]
Confirm Password: [same password]
```

### Step 3: Verify Creation
```
✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!

Email: admin@dealshaq.com
Name: System Administrator
Role: Admin
Account ID: [uuid]
```

### Step 4: First Login
- Navigate to: `/admin`
- Login with credentials
- **IMMEDIATELY change password** after first login

### Step 5: Secure Script
```bash
# Option 1: Delete script
rm /app/backend/create_first_admin.py

# Option 2: Restrict permissions
chmod 600 /app/backend/create_first_admin.py
chown root:root /app/backend/create_first_admin.py
```

## Creating Additional Admins

### Method: API Endpoint (Requires Admin Auth)

**Endpoint**: `POST /api/admin/create-admin`

**Headers**:
```
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "newadmin@dealshaq.com",
  "password": "SecurePassword123",
  "name": "New Admin Name",
  "role": "Admin",
  "charity_id": null
}
```

**Response**:
```json
{
  "message": "Admin account created successfully",
  "email": "newadmin@dealshaq.com"
}
```

**Security**:
- ✅ Requires valid Admin JWT token
- ✅ Only existing Admins can create new Admins
- ✅ Logs creation event with creator's email
- ✅ Returns 403 Forbidden if non-Admin tries

### Example Using curl:
```bash
# 1. Login as Admin
ADMIN_TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dealshaq.com","password":"password","role":"Admin"}' \
  | jq -r '.access_token')

# 2. Create new Admin
curl -X POST "$API_URL/api/admin/create-admin" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newadmin@dealshaq.com",
    "password": "SecurePassword123",
    "name": "New Admin",
    "role": "Admin"
  }'
```

## Public Registration Blocks

### Consumer/Retailer Registration (Allowed)
```json
// ✅ ALLOWED
POST /api/auth/register
{
  "email": "user@example.com",
  "role": "DAC",  // or "DRLP"
  ...
}
```

### Admin Registration (Blocked)
```json
// ❌ BLOCKED
POST /api/auth/register
{
  "email": "hacker@evil.com",
  "role": "Admin",
  ...
}

// Response: 403 Forbidden
{
  "detail": "Admin accounts cannot be created through public registration. Contact system administrator."
}
```

## Error Handling

### Invalid Role
```json
// Request
{
  "role": "SuperUser"
}

// Response: 400 Bad Request
{
  "detail": "Invalid role. Only 'DAC' (Consumer) and 'DRLP' (Retailer) registration allowed."
}
```

### Non-Admin Tries to Create Admin
```json
// Request with DAC or DRLP token
POST /api/admin/create-admin

// Response: 403 Forbidden
{
  "detail": "Only existing Admins can create new Admin accounts"
}
```

## Admin Account Lifecycle

### 1. Creation
- Via bootstrap script (first Admin)
- Via API endpoint (subsequent Admins)
- Email verification recommended (future)

### 2. Active Use
- Login at `/admin`
- Full system access
- All actions logged

### 3. Password Management
- Change password immediately after creation
- Strong password requirements (8+ chars)
- Rotate passwords regularly
- Use password manager

### 4. Deactivation
- Remove from database (soft delete recommended)
- Revoke all active sessions
- Audit all actions before removal

## Security Checklist

### ✅ Initial Setup
- [ ] Run `create_first_admin.py` on secure server
- [ ] Use strong password (12+ chars, mixed case, numbers, symbols)
- [ ] Login and verify Admin access
- [ ] Change password after first login
- [ ] Delete or secure bootstrap script

### ✅ Ongoing Security
- [ ] Limit number of Admin accounts (principle of least privilege)
- [ ] Document who has Admin access
- [ ] Rotate Admin passwords quarterly
- [ ] Monitor Admin activity logs
- [ ] Use 2FA (when implemented)

### ✅ Before Production
- [ ] Change all default passwords
- [ ] Review Admin account list
- [ ] Enable audit logging
- [ ] Set up alerts for Admin actions
- [ ] Backup Admin credentials securely

## Audit Logging

### Admin Creation Events
```python
logger.info(f"New Admin account created by {current_user['email']}: {new_admin_email}")
```

**Log Entry**:
```
2025-01-15 10:30:45 - INFO - New Admin account created by admin@dealshaq.com: newadmin@dealshaq.com
```

### Recommended Additional Logging
- Admin login attempts (success/failure)
- Admin actions (user creation, deletion, updates)
- System configuration changes
- Data exports
- Permission changes

## Best Practices

### Password Requirements
- **Minimum**: 8 characters
- **Recommended**: 12+ characters
- **Must include**: Mixed case, numbers, symbols
- **Avoid**: Dictionary words, personal info, common patterns

### Access Control
- **Principle of Least Privilege**: Only grant Admin when necessary
- **Separation of Duties**: Different Admins for different functions
- **Regular Audits**: Review Admin list quarterly
- **Time-limited Access**: Consider temporary Admin accounts

### Incident Response
If Admin account compromised:
1. **Immediately**: Revoke access, change passwords
2. **Investigate**: Review audit logs, identify breach scope
3. **Notify**: Alert all Admins and stakeholders
4. **Remediate**: Fix vulnerability, update security measures
5. **Document**: Create incident report for future reference

## Future Enhancements

### Planned Security Features (v2.0+)
- [ ] Two-Factor Authentication (2FA/MFA)
- [ ] IP whitelisting for Admin access
- [ ] Session timeout enforcement
- [ ] Email verification on Admin creation
- [ ] Admin approval workflow
- [ ] Granular permissions (read-only Admin, etc.)
- [ ] Audit log export
- [ ] Automated security monitoring

## Contact

For security concerns or to request Admin access:
- **Email**: security@dealshaq.com
- **Emergency**: Contact system administrator directly
- **Never**: Share Admin credentials via email, chat, or unsecured channels

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Security Level**: Critical  
**Review Frequency**: Quarterly
