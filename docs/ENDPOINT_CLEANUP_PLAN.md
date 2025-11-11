# Backend Endpoint Cleanup Plan

**Created:** 2025-11-03
**Status:** Ready for Review (UPDATED with Frontend Recommendations)
**Estimated Time:** 3-5 days
**Risk Level:** Medium (requires careful testing)

## ⚠️ IMPORTANT: Read First

**This document provides comprehensive cleanup reference. For executable plan, see:**

📋 **STRATEGIC_CLEANUP_PLAN.md** - Step-by-step execution guide for Option B (RECOMMENDED)

**Before executing any cleanup, please review:**
- **RECOMMENDED_FRONTEND_ENDPOINTS.md** - Analysis of which "redundant" endpoints should actually be used by frontend
- **STRATEGIC_CLEANUP_PLAN.md** - Focused, actionable cleanup plan (Option B)

**Key Findings:**
- Some "redundant" endpoints provide HIGH VALUE if integrated into frontend
- **DO NOT DELETE** endpoints marked for frontend integration in RECOMMENDED_FRONTEND_ENDPOINTS.md
- Focus cleanup on truly redundant endpoints (debug, email tests, etc.)

**Three Options Available:**

### ✅ **Option B: Strategic Cleanup (RECOMMENDED - CHOSEN)**
- Remove only 12 truly redundant endpoints
- Preserve 25 high-value endpoints for frontend integration
- Low risk, high benefit
- **See: STRATEGIC_CLEANUP_PLAN.md for execution steps**

### Option A: Aggressive Cleanup (NOT RECOMMENDED)
- Remove ~30 endpoints immediately
- Risk losing valuable functionality
- This document describes this approach (kept for reference)

### Option C: Frontend Integration First
- Pause cleanup, implement frontend features first
- Cleanup after integration complete
- Safest but slowest approach

**CHOSEN STRATEGY: Option B (Strategic Cleanup)**

---

## Note

The rest of this document describes the original **Option A: Aggressive Cleanup** plan.

**For the recommended approach (Option B), please refer to STRATEGIC_CLEANUP_PLAN.md instead.**

This document is kept for reference and comparison purposes.

---

## Overview

This plan outlines the systematic removal of redundant backend endpoints that are not used by the frontend. The cleanup will reduce codebase complexity, improve maintainability, and eliminate potential security surface area.

**UPDATED:** This plan now focuses only on truly redundant endpoints. High-value endpoints are preserved for frontend integration.

---

## Cleanup Statistics

- **Total Redundant Endpoints:** ~30-35
- **Files to Modify:** ~15-20
- **Lines of Code to Remove:** ~2000-3000 (estimated)
- **Tests to Update/Remove:** TBD (need to audit test files)

---

## Phase 1: Preparation & Verification (Day 1)

### 1.1 Pre-Cleanup Audit

**Priority:** CRITICAL
**Time:** 2-3 hours

**Tasks:**
- [ ] Run full test suite and document current passing state
  ```bash
  python manage.py test > test_results_before_cleanup.txt
  ```
- [ ] Create backup branch
  ```bash
  git checkout -b backup/before-endpoint-cleanup
  git push origin backup/before-endpoint-cleanup
  ```
- [ ] Create cleanup working branch
  ```bash
  git checkout main
  git checkout -b cleanup/remove-redundant-endpoints
  ```
- [ ] Document all backend endpoints using Swagger
  ```bash
  # Access http://localhost:8000/api/schema/swagger-ui/
  # Export/screenshot current API documentation
  ```

### 1.2 Dependency Analysis

**Priority:** CRITICAL
**Time:** 1-2 hours

**Tasks:**
- [ ] Search for internal service-to-service calls that might use redundant endpoints
  ```bash
  grep -r "propagation-jobs" --include="*.py"
  grep -r "propagation-errors" --include="*.py"
  grep -r "/email/" --include="*.py"
  ```
- [ ] Check if any management commands use these endpoints
- [ ] Review signal handlers and background tasks for dependencies
- [ ] Verify no admin interface customizations depend on these endpoints

### 1.3 Stakeholder Notification

**Priority:** HIGH
**Time:** 30 minutes

**Tasks:**
- [ ] Notify team about planned cleanup
- [ ] Confirm propagation system is truly unused (or planned for deprecation)
- [ ] Verify platform-level approval endpoints should NOT be implemented
- [ ] Get approval to proceed from tech lead/product owner

---

## Phase 2: Low-Risk Cleanup (Day 2)

Start with endpoints that have minimal dependencies and low risk.

### 2.1 Remove Debug/Test Endpoints

**Priority:** HIGH
**Risk:** LOW
**Time:** 1 hour

**Endpoints to Remove:**
- `GET /api/v1/debug/auth-status/`
- `POST /api/v1/email/test/`
- `POST /api/v1/email/send/`

**Files to Modify:**
```
users/urls.py (lines 38, 46-47)
users/views.py (debug_auth_status function)
users/email_views.py (send_test_email, send_custom_email)
```

**Implementation Steps:**
1. [ ] Comment out URL patterns in `users/urls.py`
2. [ ] Run tests to ensure no breaks
3. [ ] If tests pass, delete the view functions
4. [ ] Remove imports for deleted functions
5. [ ] Commit changes: `git commit -m "Remove debug and email test endpoints"`

**Rollback Plan:**
- Restore from git: `git revert HEAD`

### 2.2 Remove JWT Verify Endpoint

**Priority:** HIGH
**Risk:** LOW
**Time:** 30 minutes

**Endpoint to Remove:**
- `POST /api/v1/jwt/verify/`

**Files to Modify:**
```
users/urls.py (line 34)
users/views.py (CustomTokenVerifyView if not used elsewhere)
```

**Implementation Steps:**
1. [ ] Search codebase for any usage of token verification
   ```bash
   grep -r "jwt/verify" --include="*.py"
   grep -r "CustomTokenVerifyView" --include="*.py"
   ```
2. [ ] If no usage found, comment out URL pattern
3. [ ] Run tests
4. [ ] Delete view if safe
5. [ ] Commit changes: `git commit -m "Remove unused JWT verify endpoint"`

### 2.3 Remove API Metadata Endpoints

**Priority:** MEDIUM
**Risk:** LOW
**Time:** 30 minutes

**Endpoints to Remove:**
- `GET /api/v1/version/`
- `GET /api/v1/demo/`

**Files to Modify:**
```
master_data/urls.py (lines 103, 105)
master_data/views/__init__.py (APIVersionView, VersionDemoView imports)
master_data/views/rule_views.py or similar (view classes)
```

**Implementation Steps:**
1. [ ] Comment out URL patterns
2. [ ] Run tests
3. [ ] Delete view classes if not used
4. [ ] Commit changes: `git commit -m "Remove API metadata endpoints"`

---

## Phase 3: Medium-Risk Cleanup (Day 3)

### 3.1 Remove Nested String Details Endpoints

**Priority:** HIGH
**Risk:** MEDIUM
**Time:** 2 hours

**Endpoints to Remove:**
- `GET /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/`
- `POST /api/v1/workspaces/{workspace_id}/strings/{string_id}/details/`
- All nested detail endpoints

**Files to Modify:**
```
master_data/urls_main_api.py (lines 42-58)
master_data/views/string_detail_views.py (StringDetailNestedViewSet class)
```

**Implementation Steps:**
1. [ ] Verify frontend only uses flat structure:
   ```
   /api/v1/workspaces/{workspace_id}/string-details/
   ```
2. [ ] Comment out nested router registration in `urls_main_api.py`
3. [ ] Run full test suite
4. [ ] If tests pass, delete `StringDetailNestedViewSet` class (lines ~234-290)
5. [ ] Remove nested_router import and definition
6. [ ] Commit changes: `git commit -m "Remove nested string details endpoints - frontend uses flat structure"`

**Testing Checklist:**
- [ ] Test string detail creation via flat endpoint
- [ ] Test string detail updates
- [ ] Test string detail deletion
- [ ] Verify string regeneration still works

### 3.2 Remove User Authorization Detail Endpoint

**Priority:** MEDIUM
**Risk:** LOW
**Time:** 30 minutes

**Endpoint to Remove:**
- `GET /api/v1/users/{userId}/authorizations/`

**Files to Modify:**
```
users/management_views.py (lines 150-204, authorizations action)
```

**Implementation Steps:**
1. [ ] Search for any usage of this endpoint
2. [ ] Comment out the `@action` decorator and method
3. [ ] Run tests
4. [ ] Delete method if safe
5. [ ] Commit changes: `git commit -m "Remove detailed user authorizations endpoint"`

### 3.3 Remove Rule Optimization Endpoints

**Priority:** MEDIUM
**Risk:** MEDIUM
**Time:** 1.5 hours

**Endpoints to Remove:**
- `GET /api/v1/workspaces/{workspace_id}/rules/{rule_id}/lightweight/`
- `POST /api/v1/workspaces/{workspace_id}/rules/cache/invalidate/`
- `GET /api/v1/workspaces/{workspace_id}/rules/{rule_id}/metrics/`

**Files to Modify:**
```
master_data/urls.py (lines 112-135)
master_data/views/rule_views.py or similar (LightweightRuleView, CacheManagementView)
```

**Implementation Steps:**
1. [ ] Search for internal usage of cache invalidation
   ```bash
   grep -r "cache/invalidate" --include="*.py"
   grep -r "CacheManagementView" --include="*.py"
   ```
2. [ ] If cache invalidation is used internally, keep the view but remove URL routing
3. [ ] Comment out URL patterns
4. [ ] Run tests
5. [ ] Delete unused view classes
6. [ ] Commit changes: `git commit -m "Remove rule optimization endpoints not used by frontend"`

---

## Phase 4: High-Risk Cleanup - Propagation System (Day 4)

**⚠️ CRITICAL: This is the largest cleanup and requires careful verification**

### 4.1 Verify Propagation System is Unused

**Priority:** CRITICAL
**Risk:** HIGH
**Time:** 2-3 hours

**Tasks:**
1. [ ] **Comprehensive Code Search**
   ```bash
   # Search for any references to propagation
   grep -r "PropagationJob" --include="*.py" | grep -v "migrations" | grep -v "__pycache__"
   grep -r "PropagationError" --include="*.py" | grep -v "migrations"
   grep -r "PropagationSettings" --include="*.py" | grep -v "migrations"
   grep -r "EnhancedStringDetail" --include="*.py" | grep -v "migrations"

   # Search for imports
   grep -r "from.*propagation" --include="*.py"
   grep -r "import.*propagation" --include="*.py"
   ```

2. [ ] **Check Signal Handlers**
   ```bash
   # Propagation signals might be auto-triggered
   grep -r "@receiver" master_data/signals/ | grep -i propagation
   ```

3. [ ] **Check Model Relationships**
   - Review if String/StringDetail models have FK relationships to propagation models
   - Check if any model save() methods trigger propagation

4. [ ] **Check Management Commands**
   ```bash
   ls -la master_data/management/commands/*propagation*
   ```

5. [ ] **Database Migration Review**
   - Check if propagation tables exist in production
   - Determine if tables have data

**Decision Point:**
- **If propagation IS used internally:** STOP - Do not proceed with Phase 4.2
- **If propagation is TRULY unused:** Proceed to Phase 4.2

### 4.2 Remove Propagation URL Endpoints

**Priority:** HIGH
**Risk:** MEDIUM
**Time:** 1 hour

**Endpoints to Remove:**
- All `/api/v1/workspaces/{workspace_id}/propagation-jobs/*` endpoints
- All `/api/v1/workspaces/{workspace_id}/propagation-errors/*` endpoints
- All `/api/v1/workspaces/{workspace_id}/enhanced-string-details/*` endpoints
- All `/api/v1/workspaces/{workspace_id}/propagation-settings/*` endpoints

**Files to Modify:**
```
master_data/urls.py (lines 71-91 - router registrations)
```

**Implementation Steps:**
1. [ ] Comment out router registrations (4 lines)
2. [ ] Run full test suite
3. [ ] If tests pass, keep views but remove from URLs
4. [ ] Commit changes: `git commit -m "Remove propagation system URL endpoints"`

**DO NOT DELETE:**
- Propagation models (might be used internally)
- Propagation services (might be called by signals)
- Propagation views (keep for potential future use)

### 4.3 Optional: Archive Propagation System

**Priority:** LOW
**Risk:** MEDIUM
**Time:** 2 hours

**Only proceed if:**
- Confirmed 100% unused
- No database tables have data
- No signal handlers reference propagation

**Tasks:**
1. [ ] Create `master_data/archived/` directory
2. [ ] Move propagation views to archived
3. [ ] Move propagation serializers to archived
4. [ ] Update imports to prevent accidental usage
5. [ ] Create database migration to drop propagation tables (reversible)
6. [ ] Commit: `git commit -m "Archive unused propagation system"`

---

## Phase 5: Documentation & Frontend Alignment (Day 5)

### 5.1 Update Frontend Documentation

**Priority:** HIGH
**Risk:** LOW
**Time:** 1.5 hours

**Tasks:**
1. [ ] Update `FRONTEND_ENDPOINTS_LIST.md`
   - Remove documented endpoints that were deleted
   - Add note about removed propagation system
   - Mark missing endpoints (platform approvals) as "not implemented"

2. [ ] Create `REMOVED_ENDPOINTS.md` documenting what was removed and why
   ```markdown
   # Removed Endpoints Log

   ## 2025-11-03 - Redundant Endpoint Cleanup

   ### Removed Endpoints
   - Debug endpoints (auth-status, email test)
   - JWT verify endpoint
   - Nested string details
   - Propagation system endpoints
   - etc.

   ### Rationale
   - Not used by frontend
   - Reduce API surface area
   - Improve maintainability
   ```

3. [ ] Update API documentation comments in code

### 5.2 Clarify Missing Endpoints

**Priority:** MEDIUM
**Risk:** LOW
**Time:** 1 hour

**Platform-Level Approval Endpoints** (documented but not implemented):

**Option A: Remove from Frontend Docs**
- [ ] Remove lines 167-169 from `FRONTEND_ENDPOINTS_LIST.md`
- [ ] Add note: "Platform-level approvals not implemented - use project-level approvals"

**Option B: Implement These Endpoints**
- [ ] Create GitHub issue to track implementation
- [ ] Add TODO comments in code
- [ ] Update frontend docs to mark as "planned"

**Decision:** Discuss with product team and choose A or B

### 5.3 Generate New API Documentation

**Priority:** MEDIUM
**Risk:** LOW
**Time:** 30 minutes

**Tasks:**
1. [ ] Export updated Swagger/OpenAPI schema
   ```bash
   python manage.py spectacular --file schema.yml
   ```
2. [ ] Generate updated ReDoc documentation
3. [ ] Create comparison report: before vs after
4. [ ] Commit documentation: `git commit -m "Update API documentation post-cleanup"`

---

## Phase 6: Testing & Validation (Day 5)

### 6.1 Automated Testing

**Priority:** CRITICAL
**Risk:** HIGH
**Time:** 2 hours

**Tasks:**
1. [ ] Run full backend test suite
   ```bash
   python manage.py test > test_results_after_cleanup.txt
   ```
2. [ ] Compare test results before/after
   ```bash
   diff test_results_before_cleanup.txt test_results_after_cleanup.txt
   ```
3. [ ] Fix any broken tests caused by cleanup
4. [ ] Ensure test coverage hasn't decreased significantly
   ```bash
   coverage run --source='.' manage.py test
   coverage report
   coverage html
   ```

### 6.2 Manual Testing

**Priority:** HIGH
**Risk:** MEDIUM
**Time:** 1-2 hours

**Test Cases:**
- [ ] User authentication flow (login, logout, refresh)
- [ ] Workspace listing and switching
- [ ] Dimension CRUD operations
- [ ] Dimension value CRUD operations
- [ ] Rule CRUD operations
- [ ] String CRUD operations (flat structure)
- [ ] String detail CRUD operations (flat structure)
- [ ] Project CRUD operations
- [ ] Project string operations
- [ ] Multi-operations endpoint

### 6.3 Frontend Integration Testing

**Priority:** CRITICAL
**Risk:** HIGH
**Time:** 2-3 hours

**Prerequisites:**
- Frontend application must be available
- Test data must be seeded

**Test Scenarios:**
1. [ ] Complete user registration/login flow
2. [ ] Workspace management from frontend
3. [ ] Dimension management workflows
4. [ ] Rule creation and editing
5. [ ] String generation and updates
6. [ ] Project creation and approval workflows
7. [ ] Bulk operations

**Validation:**
- [ ] No console errors related to API calls
- [ ] No 404 errors in network tab
- [ ] All frontend features work as expected

---

## Phase 7: Deployment & Monitoring (Post-Cleanup)

### 7.1 Staged Rollout

**Priority:** CRITICAL
**Risk:** HIGH
**Time:** Varies by environment

**Recommended Rollout:**
1. [ ] **Development Environment** (Day 1)
   - Deploy cleanup branch
   - Run automated tests
   - Manual smoke testing
   - Monitor for 24 hours

2. [ ] **Staging Environment** (Day 2-3)
   - Deploy to staging
   - Full regression testing
   - Frontend integration testing
   - Performance testing
   - Monitor for 48 hours

3. [ ] **Production Environment** (Day 4-5)
   - Deploy during low-traffic window
   - Monitor error rates closely
   - Have rollback plan ready
   - Monitor for 1 week

### 7.2 Monitoring Checklist

**Priority:** HIGH
**Risk:** HIGH
**Time:** Ongoing for 1 week

**Metrics to Watch:**
- [ ] API error rates (should not increase)
- [ ] Response times (should improve or stay same)
- [ ] 404 error rates (might see spike from removed endpoints)
- [ ] Database query counts (should decrease)
- [ ] Memory usage (should decrease slightly)

**Alert Triggers:**
- Sudden increase in 500 errors
- Increase in frontend error reports
- User reports of missing features

### 7.3 Rollback Plan

**Priority:** CRITICAL
**Risk:** N/A
**Time:** 15-30 minutes

**If issues arise:**

**Option 1: Revert Specific Phase**
```bash
# Identify problematic commit
git log --oneline

# Revert specific commit
git revert <commit-hash>
git push origin main
```

**Option 2: Full Rollback**
```bash
# Restore from backup branch
git checkout main
git reset --hard backup/before-endpoint-cleanup
git push origin main --force  # Use with caution!
```

**Option 3: Hotfix**
```bash
# If only specific endpoint needs restoration
git checkout cleanup/remove-redundant-endpoints -- path/to/file.py
git commit -m "Restore endpoint X due to unexpected dependency"
git push origin main
```

---

## Risk Mitigation Strategies

### High-Risk Items

1. **Propagation System Removal**
   - **Risk:** Internal services might use it
   - **Mitigation:** Thorough code search, signal handler review, database check
   - **Fallback:** Keep endpoints but mark as deprecated

2. **Nested String Details Removal**
   - **Risk:** Some frontend routes might use nested structure
   - **Mitigation:** Search frontend codebase for nested URLs
   - **Fallback:** Easy to restore if needed

3. **JWT Verify Endpoint**
   - **Risk:** Server-to-server auth might use it
   - **Mitigation:** Check all service integrations
   - **Fallback:** Quick restoration if needed

### Testing Gaps

**Potential Issues:**
- Tests might not cover all edge cases
- Some endpoints might be used by admin scripts
- Background jobs might call endpoints directly

**Mitigation:**
- Monitor logs for 404s in production
- Keep deleted code in git history for easy restoration
- Gradual rollout with monitoring

---

## Success Criteria

### Quantitative Metrics
- [ ] All existing tests pass
- [ ] No new errors in production logs
- [ ] API response times improve or stay same
- [ ] Code complexity metrics improve
- [ ] Documentation is up to date

### Qualitative Metrics
- [ ] Codebase is more maintainable
- [ ] API surface area is reduced
- [ ] Team can easily understand what endpoints are available
- [ ] Frontend developers have accurate endpoint documentation

---

## Post-Cleanup Tasks

### Immediate (Within 1 Week)
- [ ] Update team documentation/wiki
- [ ] Present cleanup results to team
- [ ] Archive cleanup plan for future reference
- [ ] Update onboarding documentation for new developers

### Future Considerations
- [ ] Consider implementing missing statistics endpoints if needed
- [ ] Evaluate if platform-level approvals should be built
- [ ] Review other potential cleanup opportunities
- [ ] Establish process for preventing endpoint sprawl

---

## Appendix A: File Inventory

### Files to Modify (Confirmed)

**URL Configuration:**
- `main/urls.py` - No changes (just includes)
- `users/urls.py` - Remove debug, email, JWT verify endpoints
- `master_data/urls.py` - Remove propagation routers, optimization endpoints
- `master_data/urls_main_api.py` - Remove nested string details
- `master_data/urls_projects.py` - No changes

**Views:**
- `users/views.py` - Remove debug_auth_status, possibly CustomTokenVerifyView
- `users/email_views.py` - Remove send_test_email, send_custom_email
- `users/management_views.py` - Remove authorizations action
- `master_data/views/string_detail_views.py` - Remove StringDetailNestedViewSet
- `master_data/views/rule_views.py` - Remove LightweightRuleView, CacheManagementView
- `master_data/views/propagation_views.py` - Comment out/archive (don't delete)

**Documentation:**
- `FRONTEND_ENDPOINTS_LIST.md` - Update to reflect reality
- Create `REMOVED_ENDPOINTS.md` - Track what was removed
- Update inline code documentation

---

## Appendix B: Command Reference

### Useful Commands During Cleanup

**Search for Endpoint Usage:**
```bash
# Search for URL patterns
grep -r "path.*endpoint_name" --include="*.py"

# Search for view class usage
grep -r "ViewClassName" --include="*.py" | grep -v migrations

# Search for import statements
grep -r "from.*views import.*ViewName" --include="*.py"
```

**Testing Commands:**
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test master_data
python manage.py test users

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific test file
python manage.py test master_data.tests.test_string_views
```

**Database Commands:**
```bash
# Check if propagation tables exist
python manage.py dbshell
\dt master_data_propagation*

# Check table row counts
SELECT COUNT(*) FROM master_data_propagationjob;
SELECT COUNT(*) FROM master_data_propagationerror;
```

**Git Commands:**
```bash
# Create backup
git checkout -b backup/before-cleanup
git push origin backup/before-cleanup

# Create working branch
git checkout -b cleanup/remove-redundant-endpoints

# View changes
git diff --stat
git diff path/to/file.py

# Commit changes
git add path/to/file.py
git commit -m "Remove redundant endpoints: description"

# Revert if needed
git revert HEAD
git reset --hard HEAD~1  # Use with caution!
```

---

## Appendix C: Stakeholder Communication Template

### Email Template: Cleanup Notification

**Subject:** Backend API Cleanup - Removing Unused Endpoints

**Body:**

Hi Team,

We're planning to clean up redundant backend API endpoints that are not used by the frontend application. This will:

- Reduce codebase complexity
- Improve maintainability
- Reduce potential security surface area
- Align backend with frontend requirements

**Timeline:**
- Start Date: [DATE]
- Expected Completion: [DATE]
- Environments: Dev → Staging → Production

**Endpoints to be Removed:**
- Debug/test endpoints (auth-status, email testing)
- Propagation system endpoints (~20+ endpoints)
- Nested string detail endpoints
- JWT verify endpoint
- Rule optimization endpoints

**Impact:**
- Frontend should see NO impact (these endpoints are not used)
- Backend API will be simpler and cleaner
- Performance may improve slightly

**Testing:**
- Full automated test suite
- Manual regression testing
- Frontend integration testing

**Rollback Plan:**
- All changes are versioned in Git
- Can rollback within minutes if issues arise
- Gradual rollout with monitoring

Please let me know if you have any concerns or questions.

Thanks,
[Your Name]

---

## Appendix D: Checklist Summary

Use this quick checklist to track overall progress:

### Phase 1: Preparation ☐
- [ ] Backup branch created
- [ ] Working branch created
- [ ] Test baseline captured
- [ ] Dependencies analyzed
- [ ] Stakeholders notified

### Phase 2: Low-Risk Cleanup ☐
- [ ] Debug endpoints removed
- [ ] Email test endpoints removed
- [ ] JWT verify endpoint removed
- [ ] API metadata endpoints removed
- [ ] Tests passing

### Phase 3: Medium-Risk Cleanup ☐
- [ ] Nested string details removed
- [ ] User authorizations endpoint removed
- [ ] Rule optimization endpoints removed
- [ ] Tests passing

### Phase 4: High-Risk Cleanup ☐
- [ ] Propagation system verified as unused
- [ ] Propagation URL endpoints removed
- [ ] Tests passing
- [ ] (Optional) Propagation system archived

### Phase 5: Documentation ☐
- [ ] Frontend docs updated
- [ ] Removed endpoints documented
- [ ] Missing endpoints clarified
- [ ] New API schema generated

### Phase 6: Testing ☐
- [ ] Automated tests passing
- [ ] Manual testing complete
- [ ] Frontend integration tested
- [ ] No regressions found

### Phase 7: Deployment ☐
- [ ] Dev environment deployed
- [ ] Staging environment deployed
- [ ] Production environment deployed
- [ ] Monitoring in place
- [ ] No issues detected

---

**END OF CLEANUP PLAN**
