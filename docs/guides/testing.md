# Phase 7: Testing Guide

## ✅ Implemented Features Testing

### 1. Security Hardening Tests

#### Test 1.1: Default Admin Must Change Password
```bash
# Login as default admin
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

**Expected Response**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "must_change_password": true  ← Should be TRUE
}
```

#### Test 1.2: Password Strength Validation
```bash
# Get access token first (save from above)
TOKEN="your_access_token_here"

# Try to change to a weak password (should FAIL)
curl -X POST "http://localhost:8000/auth/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "admin", "new_password": "weak"}'
```

**Expected**: HTTP 400 with error message about password requirements

#### Test 1.3: Common Password Detection
```bash
# Try a common password (should FAIL)
curl -X POST "http://localhost:8000/auth/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "admin", "new_password": "Password123!"}'
```

**Expected**: HTTP 400 - "Password is too common"

#### Test 1.4: Successful Password Change
```bash
# Use a strong, unique password (should SUCCEED)
curl -X POST "http://localhost:8000/auth/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "admin", "new_password": "MySecure@Pass2024!"}'
```

**Expected**: HTTP 200 with success message

#### Test 1.5: Verify Flag Cleared
```bash
# Login again with new password
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=MySecure@Pass2024!"
```

**Expected**: `must_change_password: false` in response

---

### 2. Real-Time Progress Tracking Tests

#### Test 2.1: Submit a Scan
```bash
# Get new token with updated password
TOKEN="new_access_token_here"

# Submit a scan
curl -X POST "http://localhost:8000/scans" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/psf/requests",
    "project_name": "requests-py"
  }'
```

**Expected**: Returns scan ID
```json
{
  "id": "abc123...",
  "project": "requests-py",
  "status": "queued",
  ...
}
```

#### Test 2.2: Poll Progress Endpoint
```bash
# Save the scan ID from above
SCAN_ID="abc123..."

# Check progress immediately
curl "http://localhost:8000/scans/$SCAN_ID/progress" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Progress Stages**:
1. **QUEUED** (0%)
2. **INITIALIZING** (5%)
3. **CLONING** (15%)
4. **DETECTING_COMPONENTS** (30%)
5. **RESOLVING_LICENSES** (70%) - with component counts
6. **EVALUATING_POLICY** (85%)
7. **GENERATING_REPORT** (95%)
8. **COMPLETE** (100%)

**Sample Response**:
```json
{
  "scan_id": "abc123...",
  "status": "running",
  "current_stage": "resolving_licenses",
  "progress_percent": 70,
  "message": "Resolved 25/50 components...",
  "components_found": 50,
  "components_resolved": 25,
  "elapsed_seconds": 12.5,
  "error": null
}
```

#### Test 2.3: Continuous Polling Script
```bash
# Poll every 2 seconds until complete
while true; do
  echo "=== $(date) ==="
  curl -s "http://localhost:8000/scans/$SCAN_ID/progress" \
    -H "Authorization: Bearer $TOKEN" | jq .
  sleep 2
done
```

---

### 3. Dashboard UI Tests (Manual)

#### Test 3.1: Password Change Flow
1. Login with admin/admin
2. Should see "You must change your password" banner
3. Try weak password - should show error
4. Success with strong password
5. No banner after relogin

#### Test 3.2: Progress Visualization
1. Submit a scan from dashboard
2. Watch progress bar update in real-time
3. See component counts: "Resolving 10/45 components"
4. See elapsed time increment
5. Progress completes at 100%

---

## Manual Testing Checklist

### Security:
- [ ] Login with default admin shows must_change_password=true
- [ ] Weak password rejected (< 8 chars)
- [ ] Password without uppercase rejected
- [ ] Password without digit rejected
- [ ] Password without special char rejected
- [ ] Common password rejected
- [ ] New strong password accepted
- [ ] Flag cleared after password change
- [ ] Subsequent login has must_change_password=false

### Progress Tracking:
- [ ] Scan submission returns queued status
- [ ] Progress endpoint returns initial state (queued, 0%)
- [ ] Progress updates to initializing (5%)
- [ ] Progress shows cloning stage (15%)
- [ ] Detect stage shows component count
- [ ] Resolving stage updates incrementally
- [ ] Component counters increase (e.g., 10/50, 20/50)
- [ ] Elapsed time increments
- [ ] Final stage is COMPLETE (100%)
- [ ] Progress API returns null after TTL expires

### Integration:
- [ ] Worker processes scan successfully
- [ ] Redis stores progress data
- [ ] API can retrieve progress
- [ ] Database updated with final results
- [ ] No errors in container logs

---

## Troubleshooting

### Check Logs:
```bash
# API logs
docker logs license-compliance-checker-api-1 -f

# Worker logs
docker logs license-compliance-checker-worker-1 -f

# Redis connection test
docker exec license-compliance-checker-redis-1 redis-cli PING
```

### Common Issues:

1. **Progress always null**: Check Redis connection, verify worker is running
2. **Password change fails**: Check validators import, verify database schema
3. **Worker not processing**: Check Arq connection, Redis URL

---

## Success Criteria

✅ **Security**:
- Default admin cannot use system without password change
- Only strong passwords accepted
- Common passwords blocked

✅ **Progress**:
- Real-time updates visible via API
- All scan stages tracked
- Component counts update correctly
- Progress reaches 100% on completion

✅ **User Experience**:
- Clear error messages
- Immediate feedback on password requirements
- Visual progress indication
- No black-box scanning

Ready to test! 🧪
