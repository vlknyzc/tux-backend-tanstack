# GitHub Issues Created from Code Review

**Date:** October 21, 2025
**Total Issues Created:** 13

Based on the comprehensive code review documented in `CODE_REVIEW_REPORT.md`, the following GitHub issues have been created:

---

## Critical Priority Issues (🔴)

### #118 - [CRITICAL] Fix N+1 query in dimension_catalog_service.py
**Link:** https://github.com/vlknyzc/tux-backend/issues/118
**Estimated Effort:** 4-6 hours
**Impact:** 10-100x performance improvement for large catalogs

N+1 query pattern causing O(n²) complexity when building dimension catalogs. Pre-build dictionaries indexed by dimension ID to resolve.

---

### #119 - [CRITICAL] Add rate limiting to authentication endpoints
**Link:** https://github.com/vlknyzc/tux-backend/issues/119
**Estimated Effort:** 2-3 hours
**Impact:** Prevents brute force authentication attacks

No rate limiting on JWT token endpoints allows unlimited login attempts. Implement DRF throttling.

---

### #120 - [CRITICAL] Remove or secure debug_auth_status endpoint
**Link:** https://github.com/vlknyzc/tux-backend/issues/120
**Estimated Effort:** 15 minutes
**Impact:** Prevents information disclosure vulnerability

Debug endpoint exposes sensitive system information with AllowAny permission. Remove or secure with authentication.

---

### #121 - [CRITICAL] Fix recursive propagation performance bottleneck
**Link:** https://github.com/vlknyzc/tux-backend/issues/121
**Estimated Effort:** 8-12 hours
**Impact:** Enables deep inheritance hierarchies without timeouts

Recursive propagation causes exponential query growth. Implement breadth-first traversal with batching.

---

## High Priority Issues (🟠)

### #122 - [HIGH] Standardize workspace access control to prevent IDOR
**Link:** https://github.com/vlknyzc/tux-backend/issues/122
**Estimated Effort:** 1-2 days
**Impact:** Prevents unauthorized workspace access

Inconsistent workspace access control patterns across views. Standardize on check_workspace_access() method.

---

### #123 - [HIGH] Extract duplicate code to shared utilities
**Link:** https://github.com/vlknyzc/tux-backend/issues/123
**Estimated Effort:** 3-4 days
**Impact:** Improved maintainability and reduced bug risk

Significant code duplication across services. Create shared utility modules for:
- Formatting inheritance checks
- Dimension inheritance detection
- Cache key generation
- Dimension type checking

---

### #124 - [HIGH] Add transaction batching for large updates
**Link:** https://github.com/vlknyzc/tux-backend/issues/124
**Estimated Effort:** 2-3 days
**Impact:** Reduces database lock contention

Entire batch update in single transaction holds locks too long. Implement chunked transactions or Celery tasks.

---

### #125 - [HIGH] Add missing select_related/prefetch_related to fix N+1 queries
**Link:** https://github.com/vlknyzc/tux-backend/issues/125
**Estimated Effort:** 1-2 days
**Impact:** Eliminates 20-100+ queries per request

Missing select_related/prefetch_related in rule service and dimension catalog. Add appropriate joins.

---

## Medium Priority Issues (🟡)

### #126 - [MEDIUM] Clean up unused files and dependencies
**Link:** https://github.com/vlknyzc/tux-backend/issues/126
**Estimated Effort:** 1-2 hours
**Impact:** Cleaner codebase, ~1MB saved

Remove:
- 11 root-level debug/deployment scripts
- 287 .pyc files and __pycache__ directories
- Unused dependencies
- Empty/obsolete files

---

### #127 - [MEDIUM] Refactor complex functions violating single responsibility
**Link:** https://github.com/vlknyzc/tux-backend/issues/127
**Estimated Effort:** 1 week
**Impact:** Improved testability and maintainability

Refactor large functions:
- batch_update_strings (105 lines)
- get_rule_configuration_data (104 lines)
- _build_optimized_catalog (39 lines)
- _detect_string_conflicts (66 lines)

---

### #128 - [MEDIUM] Centralize configuration values (eliminate magic numbers)
**Link:** https://github.com/vlknyzc/tux-backend/issues/128
**Estimated Effort:** 4-6 hours
**Impact:** Easier configuration management

Move hardcoded values to centralized configuration:
- Cache timeouts
- Batch size thresholds
- Max inheritance depth
- Child count limits

---

### #129 - [MEDIUM] Fix String model unique constraint and signal issues
**Link:** https://github.com/vlknyzc/tux-backend/issues/129
**Estimated Effort:** 2-3 days
**Impact:** Prevents future bugs

Address:
- Changed unique constraint (audit code assumptions)
- Remove legacy signal handler
- Refactor fragile recursion prevention

---

## Low Priority Issues (🟢)

### #130 - [LOW] Add comprehensive type hints and improve code documentation
**Link:** https://github.com/vlknyzc/tux-backend/issues/130
**Estimated Effort:** 3-5 days
**Impact:** Better IDE support and type safety

Add type hints to all service methods, views, and serializers. Configure mypy for CI/CD.

---

## Implementation Roadmap

### Week 1 (Critical)
- [x] Create all GitHub issues
- [ ] Fix N+1 query in dimension_catalog_service (#118)
- [ ] Add rate limiting (#119)
- [ ] Remove/secure debug endpoint (#120)

### Week 2-3 (Critical + High)
- [ ] Fix recursive propagation (#121)
- [ ] Standardize workspace access control (#122)
- [ ] Add transaction batching (#124)
- [ ] Add select_related/prefetch_related (#125)

### Week 4-6 (High + Medium)
- [ ] Extract duplicate code (#123)
- [ ] Refactor complex functions (#127)
- [ ] Fix String model issues (#129)

### Week 7-8 (Medium + Low)
- [ ] Clean up unused files (#126)
- [ ] Centralize configuration (#128)
- [ ] Add type hints (#130)

---

## Summary Statistics

- **Total Issues:** 13
- **Critical (🔴):** 4 issues
- **High (🟠):** 4 issues
- **Medium (🟡):** 4 issues
- **Low (🟢):** 1 issue

**Total Estimated Effort:** 8-12 weeks

**Priority Focus:**
1. Performance (N+1 queries, recursion)
2. Security (rate limiting, IDOR, debug endpoints)
3. Code quality (duplication, complexity)
4. Cleanup (unused files, dependencies)

---

## Next Steps

1. **Review issues with team** - Discuss priorities and timeline
2. **Assign issues** - Allocate issues to team members
3. **Create sprint plan** - Break down into 2-week sprints
4. **Set up CI/CD checks** - Add automated code quality checks
5. **Regular code reviews** - Prevent new technical debt

---

**Related Documents:**
- See `CODE_REVIEW_REPORT.md` for full analysis and details
- All issues tagged for easy filtering in GitHub
- Use issue numbers (#118-130) for traceability in commits

**Notes:**
- All issues reference specific file paths and line numbers
- Each issue includes code examples and proposed solutions
- Estimated efforts are rough guidelines, adjust based on team capacity
